from django.db.models import Count
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
    print(f"""
        Syncing electrodelogs of stl: {stl} - {datetime.datetime.now().strftime('%H:%M:%S')}
    """)
    task = BuffaloAsyncTask(
        description=f"Sync electrodelogs of stl: {stl}"
    )

    try:
        task.save()
        stl.sync_electrodelogs()
        print(f"""
            Completed Syncing electrodelogs of stl: {stl}
            - {datetime.datetime.now().strftime('%H:%M:%S')}
        """)
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
    stls = STLFile.objects.filter(subject=subject.id)
    print(f"""
        Syncing electrodelogs of device: {device} - {datetime.datetime.now().strftime('%H:%M:%S')}
    """)
    task.save()
    try:
        electrodelogs = ElectrodeLog.objects.filter(
            electrode__device=device
        ).annotate(
            num_stls=Count('electrodelogstl')
        ).filter(num_stls__lt=len(stls))

        for ell in electrodelogs:
            existing = ell.electrodelogstl.prefetch_related("stl").all().values("id")
            stls = STLFile.objects.filter(subject=subject).exclude(id__in=existing)
            for stl in stls:
                elstl = ElectrodeLogSTL(
                    stl=stl,
                    electrodelog=ell
                )
                elstl.is_in, elstl.distance = ell.is_in_stl(stl.stl_file.name)
                elstl.save()
        print(f"""
            Completed Syncing electrodelogs of device: {device}
            - {datetime.datetime.now().strftime('%H:%M:%S')}
        """)
        task.status = BuffaloAsyncTask.COMPLETED
    except Exception as err:
        task.status = BuffaloAsyncTask.ERROR
        task.message = type(err)

    task.save()
