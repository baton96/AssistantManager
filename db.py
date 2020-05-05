from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine

engine = create_engine('sqlite:///assistants.db')
Base = declarative_base()

class Assistant(Base):
    __tablename__ = 'assistants'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    department = Column(String)
    job = Column(String)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)