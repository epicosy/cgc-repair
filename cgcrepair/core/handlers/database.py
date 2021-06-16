from pathlib import Path

from cement import Handler
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, relationship
from sqlalchemy import inspect

from cgcrepair.core.corpus.challenge import Challenge
from cgcrepair.core.corpus.cwe_parser import CWEParser
from cgcrepair.core.corpus.manifest import Manifest
from cgcrepair.core.interfaces import DatabaseInterface
from cgcrepair.utils.data import WorkingPaths

Base = declarative_base()


class TestOutcome(Base):
    __tablename__ = "test_outcome"

    id = Column('id', Integer, primary_key=True)
    instance_id = Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False)
    co_id = Column('co_id', Integer, ForeignKey('compile_outcome.id'), nullable=False)
    instance = relationship("Instance", back_populates="test_outcome")
    compile_outcome = relationship("CompileOutcome", back_populates="test_outcome")
    name = Column('name', String, nullable=False)
    error = Column('error', String, nullable=True)
    exit_status = Column('exit_status', Integer, nullable=False)
    passed = Column('passed', Boolean, nullable=False)
    duration = Column('duration', Float, nullable=False)
    is_pov = Column('is_pov', Boolean, nullable=False)
    sig = Column('sig', Integer, nullable=False)
    failed = Column('failed', Integer, nullable=True)
    total = Column('total', Integer, nullable=False)


class CompileOutcome(Base):
    __tablename__ = "compile_outcome"

    id = Column('id', Integer, primary_key=True)
    instance_id = Column('instance_id', Integer, ForeignKey('instance.id'))
    instance = relationship("Instance", back_populates="compile_outcome")
    test_outcome = relationship("TestOutcome", back_populates="compile_outcome")
    error = Column('error', String, nullable=True)
    tag = Column('tag', String, nullable=False)
    exit_status = Column('exit_status', Integer)


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

    def __str__(self):
        return f"{self.name} | {self.main_cwe} | {self.povs} | {self.total_lines} | {self.vuln_lines} | " \
               f"{self.patch_lines} | {self.vuln_files}"


class Instance(Base):
    __tablename__ = "instance"

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String)
    path = Column('path', String)
    pointer = Column('pointer', Integer, nullable=True)
    test_outcome = relationship("TestOutcome", back_populates="instance")
    compile_outcome = relationship("CompileOutcome", back_populates="instance")

    def working(self):
        working_dir = Path(self.path)
        build_root = working_dir / Path("build")

        return WorkingPaths(root=working_dir, source=working_dir / Path(self.name),
                            build_root=build_root, build=build_root / Path(self.name),
                            cmake=build_root / Path(self.name, "CMakeFiles", f"{self.name}.dir"))

    def __str__(self):
        return f"{self.id} | {self.name} | {self.path} | {self.pointer}"


class InstanceHandler(DatabaseInterface, Handler):
    class Meta:
        label = 'instance'

    def get(self, instance_id: int):
        return self.app.db.query(Instance, instance_id)

    def get_compile_outcome(self, instance_id: int):
        return self.app.db.query_attr(Instance, instance_id, 'compile_outcome')

    def all(self):
        return self.app.db.query(Instance)


class MetadataHandler(DatabaseInterface, Handler):
    class Meta:
        label = 'metadata'

    def __call__(self, challenge: Challenge):
        cwe_parser = CWEParser(description=challenge.info(), level=self.app.config.get_config('cwe_level'))
        manifest = Manifest(source_path=challenge.paths.source)

        metadata = Metadata()
        metadata.name = challenge.name
        metadata.excluded = False
        metadata.total_lines = manifest.total_lines
        metadata.vuln_lines = manifest.vuln_lines
        metadata.patch_lines = manifest.patch_lines
        metadata.vuln_files = len(manifest.vuln_files)
        metadata.main_cwe = cwe_parser.cwe_type()
        # metadata.vulns = manifest.get_vulns()
        # metadata.patches = manifest.get_patches()

        return metadata

    def all(self):
        return self.app.db.query(Metadata)


class Database:
    def __init__(self, debug: bool = False):
        self.engine = create_engine('sqlite:///:memory', echo=debug)
        Base.metadata.create_all(bind=self.engine)

    def add(self, entity: Base):
        with Session(self.engine) as session, session.begin():
            session.add(entity)
            session.flush()
            session.refresh(entity)
            session.expunge_all()

            if hasattr(entity, 'id'):
                return entity.id

    def has_table(self, name: str):
        inspector = inspect(self.engine)
        return inspector.reflect_table(name, None)

    def query(self, entity: Base, entity_id: int = None):
        with Session(self.engine) as session, session.begin():
            if entity_id and hasattr(entity, 'id'):
                results = session.query(entity).filter(entity.id == entity_id).first()
            else:
                results = session.query(entity).all()

            session.expunge_all()
            return results

    def query_attr(self, entity: Base, entity_id: int, attr: str):
        with Session(self.engine) as session, session.begin():
            if hasattr(entity, 'id') and hasattr(entity, attr):
                results = session.query(entity).filter(entity.id == entity_id).first()
                attr_result = getattr(results, attr)
                session.expunge_all()
                return attr_result

    def count(self, entity: Base):
        with Session(self.engine) as session, session.begin():
            return session.query(entity).count()

    def update(self, entity: Base, entity_id: int, attr: str, value):
        with Session(self.engine) as session, session.begin():
            if hasattr(entity, 'id') and hasattr(entity, attr):
                session.query(entity).filter(entity.id == entity_id).update({attr: value})
            else:
                raise ValueError(f"Could not update {type(entity)} {attr} with value {value}")
