-- Find all days with both calibration and Y-maze on which at least 5 hippocampal channels had ripples.

select date(asess.start_time) 
from subjects_subject ssub, buffalo_buffalosubject bsub, 
buffalo_buffalosession bsess, actions_session asess, 
buffalo_sessiontask bsta 
where 
ssub.nickname = 'Lionel' -- Update this nickname
and ssub.id = bsub.subject_ptr_id 
and asess.id = bsess.session_ptr_id 
and asess.id = bsta.session_id 
and exists ( 
	select * 
	from buffalo_sessiontask bst, buffalo_task btas, buffalo_taskcategory btc 
	where bst.session_id = asess.id 
	and btas.id = bst.task_id 
   and btc.id = btas.category_id 
	and lower(btc.name) like '%ymaze%' -- Update this task category name
) 
and exists ( 
	select * 
	from buffalo_sessiontask bst, buffalo_task btas 
	where bst.session_id = asess.id 
	and btas.id = bst.task_id 
	and lower(btas.name) like '%calibration%' -- Update this task type name
) 
and asess.id in ( 
	select session_id 
	from ( 
		select asess_s.id session_id, count(*) counter 
		from buffalo_device bd_s, buffalo_electrode be_s, buffalo_electrodelog bel_s, 
		buffalo_electrodelogstl bels_s, buffalo_stlfile bstl_s, 
		data_dataset dset_s, buffalo_channelrecording bch_s, 
		actions_session asess_s 
		where 
		bd_s.subject_id = ssub.id 
		and dset_s.id = bstl_s.dataset_ptr_id 
		and bstl_s.subject_id = bd_s.subject_id 
		and dset_s.name = 'hpc' -- Update this stl name
		and dset_s.id  = bstl_s.dataset_ptr_id 
		and bd_s.id = be_s.device_id 
		and be_s.id = bel_s.electrode_id 
		and bel_s.id = bels_s.electrodelog_id 
		and bstl_s.dataset_ptr_id = bels_s.stl_id 
		and bels_s.is_in is true 
		and date(asess_s.start_time) = date(bel_s.date_time) 
		and asess_s.id = bch_s.session_id 
		and be_s.id = bch_s.electrode_id 
		and bch_s.ripples = 'yes' 
		group by asess_s.id 
	) session_sq 
	where session_sq.counter >= 1 
) 
group by date(asess.start_time) 
order by date(asess.start_time)
