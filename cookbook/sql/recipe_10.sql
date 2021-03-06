-- get me all times we ran at least two different mazes, each of which contained "ChristmasLand" in the name.

select * 
from 
( 
	select subject, session_date, count(*) num_tasks 
	from 
	( 
		select subject, session_date, env_name 
		from 
		( 
			select ssubj.nickname subject, date(asess.start_time) session_date, environments.env_name 
			from  
			buffalo_sessiontask bst, buffalo_buffalosession bsess, actions_session asess, 
			buffalo_task btask, subjects_subject ssubj, 
			( 
				select 
					case 
						when trim(lower(task)) ~ '^ymaze$' then lower(trim(task)) 
						when trim(lower(task)) ~ '^ymaze'	then regexp_replace(lower(regexp_replace(trim(task), '\mymaze', '', 'gi')), '[\s+]', '', 'g') 
					end as env_name, 
					task_id 
				from ( 
					select btask.name task, btask.id task_id 
					from 
					buffalo_taskcategory btc, buffalo_task btask 
					where
					lower(btc.name) = 'ymaze' 
					and btc.id = btask.category_id 
				) env_clean 
			) environments 
			where 
			btask.id = environments.task_id 
			and btask.id = bst.task_id 
			and asess.id = bsess.session_ptr_id 
			and bsess.session_ptr_id = bst.session_id 
			and ssubj.id = asess.subject_id 
			and environments.env_name like '%' || trim(lower('garden')) || '%' -- Update this env name
			group by ssubj.nickname, date(asess.start_time), environments.env_name 
			order by ssubj.nickname, date(asess.start_time), environments.env_name 
		) env_logs 
	) env_count 
	group by env_count.subject, env_count.session_date 
) env_logs_filtered 
where env_logs_filtered.subject = 'test' -- Update this nickname
and env_logs_filtered.num_tasks >= 2
