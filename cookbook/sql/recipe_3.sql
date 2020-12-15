/* Get a list of all channels with units in Spock in the hippocampus for 
each day when we ran an ABA format Y-maze experiment in April 2017. */

select date(asess.start_time), be.channel_number 
from buffalo_device bd, buffalo_electrode be, buffalo_electrodelog bel, 
buffalo_electrodelogstl bels, buffalo_stlfile bstl, buffalo_buffalosubject bsub, 
data_dataset dset, buffalo_buffalosession bsess, buffalo_task btask, 
actions_session asess, buffalo_channelrecording bch, subjects_subject ssub 
where 
ssub.nickname = 'Lionel' -- Update this nickname
and ssub.id = bsub.subject_ptr_id  
and dset.name = 'hpc' -- Update this stl name
and dset.id  = bstl.dataset_ptr_id 
and bd.subject_id = bsub.subject_ptr_id 
and bd.id = be.device_id 
and be.id = bel.electrode_id 
and bel.id = bels.electrodelog_id 
and date(bel.date_time) = date(asess.start_time) 
and bstl.dataset_ptr_id = bels.stl_id 
and bels.is_in is true 
and asess.id  = bsess.session_ptr_id 
and asess.id = bch.session_id 
and (bch.number_of_cells = '3' or bch.number_of_cells = '4') 
and date_part('month', date(asess.start_time)) = '10' -- Update this month
and date_part('year', date(asess.start_time)) = '2020' -- Update this year
and asess.id in 
( 
	select session_id 
	from 
	buffalo_taskcategory btask_cat_yq, buffalo_task btask_yq, 
	( 
		select session_id, task_cat, last_task_id 
		from 
		( 
			select comp_query_a.session_id, comp_query_a.task_id, comp_query_a.task_cat task_cat, comp_query_a.last_task_id, 
			cast(comp_query_a.task_sequence as integer) - cast(comp_query_b.task_sequence as integer) diff 
			from 
			( 
				select asess_s.id session_id , btask_s.id task_id, btask_s.name task_name, btc_s.name task_cat, 
               bsessta_s.task_sequence task_sequence, 
				row_number() over(partition by asess_s.id, btask_s.id order by bsessta_s.task_sequence) gtask_seq, 
				bsessta_last_s.task_id last_task_id 
				from buffalo_buffalosession bsess_s , actions_session asess_s, 
				buffalo_sessiontask bsessta_s left outer join buffalo_sessiontask bsessta_last_s on 
               bsessta_s.session_id = bsessta_last_s.session_id 
					and bsessta_last_s.task_sequence = (bsessta_s.task_sequence - 1), 
				buffalo_task btask_s, buffalo_taskcategory btc_s 
				where 
				asess_s.id = bsess_s.session_ptr_id 
				and bsessta_s.session_id = bsess_s.session_ptr_id 
				and btask_s.id = bsessta_s.task_id 
				and btc_s.id = btask_s.category_id 
				order by asess_s.id, btask_s.id, bsessta_s.task_sequence 
			) comp_query_a, 
			( 
				select session_id, task_id, task_name, task_sequence, task_cat, comp_query_int.gtask_seq + 1 gtask_next, 
               last_task_id 
				from 
				( 
					select asess_s.id session_id , btask_s.id task_id, btask_s.name task_name, btc_s.name task_cat, 
                   bsessta_s.task_sequence task_sequence, 
					row_number() over(partition by asess_s.id, btask_s.id order by bsessta_s.task_sequence) gtask_seq, 
					bsessta_last_s.task_id last_task_id 
					from buffalo_buffalosession bsess_s , actions_session asess_s, 
					buffalo_sessiontask bsessta_s left outer join buffalo_sessiontask bsessta_last_s on 
                   bsessta_s.session_id = bsessta_last_s.session_id 
						and bsessta_last_s.task_sequence = (bsessta_s.task_sequence - 1), 
					buffalo_task btask_s, buffalo_taskcategory btc_s 
					where 
					asess_s.id = bsess_s.session_ptr_id 
					and bsessta_s.session_id = bsess_s.session_ptr_id 
					and btask_s.id = bsessta_s.task_id 
					and btc_s.id = btask_s.category_id 
					order by asess_s.id, btask_s.id, bsessta_s.task_sequence 
				) comp_query_int 
			) comp_query_b 
			where comp_query_a.gtask_seq = comp_query_b.gtask_next 
			and comp_query_a.session_id = comp_query_b.session_id 
			and comp_query_a.task_id = comp_query_b.task_id 
		) diff_query 
		where diff_query.diff = 2 
		and lower(diff_query.task_cat) like '%ymaze%' -- Update this task category
	) ymaze_query 
	where 
	btask_yq.id = ymaze_query.last_task_id 
	and btask_cat_yq.id =	btask_yq.category_id 
	and lower(btask_cat_yq.name) not like '%ymaze%' -- Update this task category
) 
group by date(asess.start_time), asess.id, be.channel_number