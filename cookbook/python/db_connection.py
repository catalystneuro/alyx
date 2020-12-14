import psycopg2

def get_connection():
    try:
        db_host = ""
        db_name = ""
        db_user = ""
        db_password = ""

        dsn = f"host={db_host} dbname={db_name} user={db_user} password={db_password}"

        return psycopg2.connect(dsn)
    except psycopg2.OperationalError as err:
        print("The connection wasn't established")
        return None
    except Exception as err:
        print(err)