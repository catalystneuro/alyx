-- Search for a string within the notes section of a session

select name, narrative, subject_id
from actions_session as2 
where as2.narrative like '%text%' -- Update this text with the text you want to find