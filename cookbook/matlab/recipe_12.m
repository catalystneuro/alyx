% search a string within the notes section of a session 

% Set this variable with the text you wanna search
text_to_find = '%text to find%'

session_note = sprintf(['select name, narrative, subject_id '  ...
'from  actions_session as2 ' ...
'where as2.narrative LIKE ''%s'' '
], text_to_find)


sessions_with_that_text = fetch(conn, session_note);