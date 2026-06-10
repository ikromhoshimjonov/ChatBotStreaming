from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker



SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:1@localhost:5433/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

