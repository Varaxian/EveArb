from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def make_session_factory(database_url: str):
    engine = create_engine(database_url, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
