import os
from configparser import ConfigParser

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session


def get_db_url_from_alembic_ini():
    config = ConfigParser()
    dirname = os.path.dirname(__file__)
    alembic_ini_path = os.path.join(dirname, "../../..", "alembic.ini")
    config.read(alembic_ini_path)
    return config.get("alembic", "sqlalchemy.url")


db_url = get_db_url_from_alembic_ini()

engine = create_engine(db_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
