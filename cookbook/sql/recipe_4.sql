-- Tell me which wires were turned yesterday and have today.

select be.channel_number 
from buffalo_device bd, buffalo_electrode be, buffalo_electrodelog bel, 
buffalo_buffalosubject bsub, subjects_subject ssub 
where 
ssub.nickname = 'laureano' -- Update this nickname
and ssub.id = bsub.subject_ptr_id 
and bsub.subject_ptr_id = bd.subject_id 
and bd.id = be.device_id 
and be.id = bel.electrode_id 
and bel.turn is not null 
and date(bel.date_time) = '2019-06-25' -- Update this date
and be.channel_number in ( 
	select be_s.channel_number 
	from buffalo_device bd_s, buffalo_electrode be_s, 
	buffalo_buffalosubject bsub_s, actions_session asess, buffalo_channelrecording bch 
	where 
	bsub_s.subject_ptr_id = bsub.subject_ptr_id 
	and bsub_s.subject_ptr_id = bd_s.subject_id 
	and bd_s.id = be_s.device_id 
	and be_s.id = bch.electrode_id 
	and asess.id = bch.session_id 
	and (bch.number_of_cells = '3' or bch.number_of_cells = '4') 
	and date(asess.start_time) = '2019-06-17' -- Update this date
)