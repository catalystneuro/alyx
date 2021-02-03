-- Find all channels in Spock that were alive on April 15th 2017 but dead on May 15th 2017

select be.channel_number 
from buffalo_device bd, buffalo_electrode be, 
buffalo_buffalosubject bsub, buffalo_buffalosession bsess, 
actions_session asess, buffalo_channelrecording bch, subjects_subject ssub 
where 
ssub.nickname = 'snake' -- Update this nickname
and ssub.id = bsub.subject_ptr_id 
and asess.id = bsess.session_ptr_id 
and bsess.session_ptr_id = bch.session_id 
and bsub.subject_ptr_id = bd.subject_id 
and bd.id = be.device_id 
and bch.alive = 'yes' 
and bch.electrode_id = be.id 
and date(asess.start_time) = '2020-02-26' -- Update this date
and be.channel_number in ( 
	select be_s.channel_number 
	from buffalo_device bd_s, buffalo_electrode be_s, 
	buffalo_buffalosubject bsub_s, buffalo_buffalosession bsess_s, 
	actions_session asess_s, buffalo_channelrecording bch_s, subjects_subject ssub_s 
	where 
	ssub_s.id = ssub.id 
	and ssub_s.id = bsub_s.subject_ptr_id 
	and asess_s.id = bsess_s.session_ptr_id 
	and bsess_s.session_ptr_id = bch_s.session_id 
	and bsub_s.subject_ptr_id = bd_s.subject_id 
	and bd_s.id = be_s.device_id 
	and bch_s.alive = 'no' 
	and bch_s.electrode_id = be_s.id 
	and date(asess_s.start_time) = '2019-10-04' -- Update this date
	-- for date range:
    -- and date(asess_s.start_time) between 'date1' and 'date2' both times
)
