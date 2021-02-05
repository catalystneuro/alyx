/* Find the name/wire number of all channels that were within 
1 mm above or below CA1 from Spock on April 27 2017. */

select be.channel_number, bels.distance 
from buffalo_device bd, buffalo_electrode be, buffalo_electrodelog bel, 
buffalo_electrodelogstl bels, buffalo_stlfile bstl, buffalo_buffalosubject bsub, 
data_dataset dset, subjects_subject ssub 
where 
ssub.nickname = 'laureano' -- update this nickname
and ssub.id = bsub.subject_ptr_id 
and dset.name = 'ca1' -- update this stl name
and dset.id  = bstl.dataset_ptr_id 
and bd.subject_id = bsub.subject_ptr_id 
and bd.id = be.device_id 
and be.id = bel.electrode_id 
and bel.id = bels.electrodelog_id 
and bstl.dataset_ptr_id = bels.stl_id 
and bels.is_in is true 
and abs(bels.distance) < 1 
and date(bel.date_time) = '2020-11-11' -- update this date to query an specific day
-- To query a year replace the last line with this condition:
    -- and date_part('year', date(bel.date_time)) = '2020' -- update this date to query a year