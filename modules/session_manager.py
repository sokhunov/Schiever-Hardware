from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def create_connection_to_sql():
    """
    Create connection engine to sql database
    :return engine: sql connection engine
    """
    

    engine = create_engine(f"mssql+pyodbc://{DB['user']}:{DB['pw']}@{DB['server']}/{DB['database']}?{DB['driver']}",
                           echo=True)
    return engine


def load_session():
    """"""
    engine = create_connection_to_sql()

    db_session = Session(bind=engine)
    return db_session
