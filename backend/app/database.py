from sqlmodel import SQLModel, create_engine
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "controller.db")
sqlite_url = f"sqlite:///{DB_PATH}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)
