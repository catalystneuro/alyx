import dramatiq
import datetime
from .models import (
    STLFile,
    BuffaloAsyncTask,
    ElectrodeLog,
    ElectrodeLogSTL,
    Device
)


@dramatiq.actor
def sync_electrodelogs_stl(stl_id):
    stl = STLFile.objects.get(pk=stl_id)
    print(f"Syncing electrodelogs of stl: {stl}")
    task = BuffaloAsyncTask(
        description=f"Sync electrodelogs of stl: {stl}"
    )
    try:
        task.save()
        stl.sync_electrodelogs()
        task.status = BuffaloAsyncTask.COMPLETED
    except Exception as err:
        task.status = BuffaloAsyncTask.ERROR
        task.message = type(err)

    task.save()


@dramatiq.actor
def sync_electrodelogs_device(device_id):
    device = Device.objects.get(pk=device_id)
    task = BuffaloAsyncTask(
        description=f"Syncing electrodelogs of device: {device}"
    )
    subject = device.subject
    print(f"Syncing electrodelogs of device: {device} - {datetime.datetime.now().strftime('%H:%M:%S')}")
    try:
        task.save()
        electrodelogs = ElectrodeLog.objects.prefetch_related('electrode__device__subject').filter(
            electrode__device=device_id
        )
        for ell in electrodelogs:
            existing = ell.electrodelogstl.prefetch_related("stl").all().values("id")
            stls = STLFile.objects.filter(subject=subject).exclude(id__in=existing)
            for stl in stls:
                elstl = ElectrodeLogSTL(
                    stl=stl,
                    electrodelog=ell
                )
                elstl.is_in = ell.is_in_stl(stl.stl_file.name)
                elstl.save()
        print(f"Completed Syncing electrodelogs of device: {device} - {datetime.datetime.now().strftime('%H:%M:%S')}")
        task.status = BuffaloAsyncTask.COMPLETED
    except Exception as err:
        task.status = BuffaloAsyncTask.ERROR
        task.message = type(err)

    task.save()
