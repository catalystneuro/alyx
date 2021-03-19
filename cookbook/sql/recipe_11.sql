-- Get data from electrodes x,y,z

select distinct  be2.turn, be2.impedance , be2.notes, be2.date_time, bc.notes, bc.number_of_cells, bc.ripples, b4.channel_number
from buffalo_channelrecording bc, buffalo_electrodelog be2, (
	select id, be.channel_number 
	from buffalo_electrode be 
	where be.channel_number in ('1', '5') -- Update this with the channel numbers of te electrodes
	and be.subject_id = (
		select id from subjects_subject ss where ss.nickname='monita' -- Update this with the name of the subject
	)
) b4
where be2.electrode_id in (b4.id) 
and date(be2.date_time) between '2021-02-16' and '2021-02-17' -- comment this line if wanna query an exact date
-- and date(be2.date_time) = '2021-02-16' -- Uncomment this line if wanna query an exact date
and bc.electrode_id in (b4.id)