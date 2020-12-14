import psycopg2
import db_connection

conn = db_connection.get_connection()

if conn:
    try:

        cur = conn.cursor()

        subject_nickname = "monita"

        query_sql = """
        select weight_date, weight, food_type, unit, amount
        from (
            select date(ass.start_time) weight_date, aw.weight weight, ass.subject_id subject, bft.name food_type, bft.unit unit, bf.amount amount
            from buffalo_weighinglog bw, actions_weighing aw,
            buffalo_buffalosession bb, actions_session ass,
            buffalo_foodlog bf, buffalo_foodtype bft
            where
            aw.id = bw.weighing_ptr_id
            and ass.id = bb.session_ptr_id
            and bw.session_id = bb.session_ptr_id
            and bb.session_ptr_id = bf.session_id
            and bft.id = bf.food_id
            union
            select date(aw.date_time) weight_date, aw.weight weight, aw.subject_id subject, bft.name food_type, bft.unit unit, bf.amount amount
            from buffalo_weighinglog bw, actions_weighing aw left outer join buffalo_foodlog bf on bf.subject_id = aw.subject_id and date(bf.date_time) = date(aw.date_time),
            buffalo_foodtype bft
            where aw.id = bw.weighing_ptr_id
            and bft.id = bf.food_id
            and aw.id not in
                (
                    select aw.id
                    from buffalo_weighinglog bw, actions_weighing aw,
                    buffalo_buffalosession bb, actions_session ass
                    where
                    aw.id = bw.weighing_ptr_id
                    and ass.id = bb.session_ptr_id
                    and bw.session_id = bb.session_ptr_id
                )
        ) weight, subjects_subject ssubj
        where subject = ssubj.id
        and ssubj.nickname = '{}'
        order by weight_date asc
        """.format(subject_nickname)

        cur.execute(query_sql)
        for row in cur:
            print(row)

    except Exception as err:
        print(err)
    finally:
        conn.close()
else:
    print("There is no connection to the db")