from sqlalchemy import create_engine
from src.backend.database import Base

engine = create_engine("sqlite:///test_database.db", echo=True)

def test_creation():
    try:
        Base.metadata.create_all(bind=engine)
        print("Successfully created database")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    test_creation()