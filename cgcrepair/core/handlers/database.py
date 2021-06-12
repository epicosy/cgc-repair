from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy import inspect

Base = declarative_base()


class Metadata(Base):
    __tablename__ = "metadata"

    name = Column('name', String, primary_key=True)
    excluded = Column('excluded', Boolean)
    total_lines = Column('total_lines', Integer)
    vuln_lines = Column('vuln_lines', Integer)
    patch_lines = Column('patch_lines', Integer)
    vuln_files = Column('vuln_files', Integer)
    main_cwe = Column('main_cwe', String)
    povs = Column('povs', Integer)


class Instance(Base):
    __tablename__ = "instance"

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String, unique=False)
    path = Column('path', String, unique=True)
    pointer = Column('pointer', Integer, unique=False, nullable=True)


class Database:
    def __init__(self, debug: bool = False):
        self.engine = create_engine('sqlite:///:memory', echo=debug)
        Base.metadata.create_all(bind=self.engine)

    def add(self, entity: Base):
        with Session(self.engine) as session, session.begin():
            session.add(entity)
            session.flush()
            session.refresh(entity)
            return entity.id

    def has_table(self, name: str):
        inspector = inspect(self.engine)
        return inspector.reflect_table(name, None)

    def query(self, entity: Base):
        with Session(self.engine) as session, session.begin():
            return session.query(entity)
