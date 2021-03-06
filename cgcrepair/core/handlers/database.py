import contextlib

from pathlib import Path
from typing import Union, Dict, Any, Callable

from cement import Handler
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, joinedload
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
    is_pov = Column('is_pov', Boolean, nullable=False)
    result = Column('result', Boolean, nullable=False)
    status = Column('status', String, nullable=True)
    total = Column('total', Integer, nullable=True)
    passed = Column('passed', Integer, nullable=True)
    failed = Column('failed', Integer, nullable=True)
    error = Column('error', String, nullable=True)
    exit_status = Column('exit_status', Integer, nullable=False)
    sig = Column('sig', Integer, nullable=True)
    duration = Column('duration', Float, nullable=False)

    def get_clean_error(self):
        return self.error.strip().replace('\n', ' ') if self.error else ''

    def __str__(self):
        return f"{self.id} | {self.co_id} | {self.name} | {self.is_pov} | {self.result} | {self.status} | {self.total}" \
               f"| {self.passed} | {self.failed} | {self.get_clean_error()} | {self.exit_status} | {self.sig} | {self.duration}"

    def to_dict(self):
        return {'id': self.id, 'compile id': self.co_id, 'name': self.name, 'is pov': self.is_pov,
                'result': self.result, 'status': self.status, 'total': self.total, 'passed': self.passed,
                'failed': self.failed, 'error': self.get_clean_error(), 'exit status': self.exit_status,
                'signal': self.sig, 'duration': self.duration}


class CompileOutcome(Base):
    __tablename__ = "compile_outcome"

    id = Column('id', Integer, primary_key=True)
    instance_id = Column('instance_id', Integer, ForeignKey('instance.id'))
    instance = relationship("Instance", back_populates="compile_outcome")
    test_outcome = relationship("TestOutcome", back_populates="compile_outcome")
    error = Column('error', String, nullable=True)
    tag = Column('tag', String, nullable=False)
    exit_status = Column('exit_status', Integer)

    def __str__(self):
        clean_error = self.error.strip().replace('\n', ' ') if self.error else ''
        return f"{self.id} | {clean_error} | {self.tag} | {self.exit_status}"


class Sanity(Base):
    __tablename__ = "sanity"

    id = Column('id', Integer, primary_key=True)
    cid = Column('cid', String, ForeignKey('metadata.id'), nullable=False)
    iid = Column('iid', Integer, ForeignKey('instance.id'))
    instance = relationship("Instance", back_populates="sanity")
    status = Column('status', String, nullable=True)


class Vulnerability(Base):
    __tablename__ = "vulnerability"

    id = Column('id', String, primary_key=True)
    cid = Column('cid', String, ForeignKey('metadata.id'), nullable=False)
    cwe = Column('cwe', Integer, nullable=False)
    test = Column('test', String, nullable=False)
    related = Column('related', String)

    def __str__(self):
        return f"{self.id} | {self.cwe} | {self.test} | {self.related}"


class Metadata(Base):
    __tablename__ = "metadata"

    id = Column('id', String, primary_key=True)
    name = Column('name', String, nullable=False)
    excluded = Column('excluded', Boolean)
    total_lines = Column('total_lines', Integer)
    vuln_lines = Column('vuln_lines', Integer)
    patch_lines = Column('patch_lines', Integer)
    vuln_files = Column('vuln_files', Integer)
    main_cwe = Column('main_cwe', String)
    povs = Column('povs', Integer)
    #vid = Column('vid', String, ForeignKey('vulnerability.id'), nullable=True)
    #vulnerability = relationship("Vulnerability", foreign_keys=[vid])

    def __str__(self):
        return f"{self.id} | {self.name} | {self.main_cwe} | {self.povs} | {self.total_lines} | {self.vuln_lines} | " \
               f"{self.patch_lines} | {self.vuln_files}"


class Instance(Base):
    __tablename__ = "instance"

    id = Column('id', Integer, primary_key=True)
    m_id = Column('m_id', String)
    name = Column('name', String)
    path = Column('path', String)
    pointer = Column('pointer', Integer, nullable=True)
    test_outcome = relationship("TestOutcome", back_populates="instance")
    compile_outcome = relationship("CompileOutcome", back_populates="instance")
    sanity = relationship("Sanity", back_populates="instance")

    def working(self):
        working_dir = Path(self.path)
        build_root = working_dir / Path("build")

        return WorkingPaths(root=working_dir, source=working_dir / Path(self.name),
                            build_root=build_root, build=build_root / Path(self.name),
                            cmake=build_root / Path(self.name, "CMakeFiles", f"{self.name}.dir"),
                            binary=build_root / self.name / self.name)

    def __str__(self):
        return f"{self.id} | {self.m_id} | {self.name} | {self.path} | {self.pointer}"


class InstanceHandler(DatabaseInterface, Handler):
    class Meta:
        label = 'instance'

    def delete(self, instance_id: int, destroy: bool = False):
        if destroy:
            instance: Instance = self.get(instance_id)
            instance_path = Path(instance.path)

            if instance_path.exists() and instance_path.is_dir():
                instance_path.rmdir()

        return self.app.db.delete(Instance, instance_id)

    def get(self, instance_id: int):
        return self.app.db.query(Instance, instance_id)

    def get_compile_outcome(self, instance_id: int):
        return self.app.db.query_attr(Instance, instance_id, 'compile_outcome')

    def get_test_outcome(self, instance_id: int):
        return self.app.db.query_attr(Instance, instance_id, 'test_outcome')

    def all(self):
        return self.app.db.query(Instance)


class VulnerabilityHandler(DatabaseInterface, Handler):
    class Meta:
        label = 'vulnerability'

    def delete(self, vid: str):
        return self.app.db.delete(Vulnerability, vid)

    def get(self, vid: str):
        return self.app.db.query(Vulnerability, vid)

    def find(self, cid: str):
        return self.app.db.filter(Vulnerability, {Vulnerability.cid: lambda v_cid: v_cid == cid}).all()

    def all(self):
        return self.app.db.query(Vulnerability)


class MetadataHandler(DatabaseInterface, Handler):
    class Meta:
        label = 'metadata'

    def __call__(self, challenge: Challenge):
        cwe_parser = CWEParser(description=challenge.info(), level=self.app.config.get_config('cwe_level'))
        manifest = Manifest(source_path=challenge.paths.source)

        metadata = Metadata()
        metadata.name = challenge.name
        metadata.id = challenge.id()
        metadata.excluded = False
        metadata.multi_cb = manifest.multi_cb
        metadata.total_lines = manifest.total_lines
        metadata.vuln_lines = manifest.vuln_lines
        metadata.patch_lines = manifest.patch_lines
        metadata.vuln_files = len(manifest.vuln_files)
        metadata.main_cwe = cwe_parser.cwe_type()
        # metadata.vulns = manifest.get_vulns()
        # metadata.patches = manifest.get_patches()

        return metadata

    def get(self, cid: str):
        return self.app.db.query(Metadata, cid)

    def all(self):
        return self.app.db.query(Metadata)


class Database:
    def __init__(self, dialect: str, username: str, password: str, host: str, port: int, database: str,
                 debug: bool = False):
        self.engine = create_engine(f"{dialect}://{username}:{password}@{host}:{port}/{database}", echo=debug)
        Base.metadata.create_all(bind=self.engine)

    def refresh(self, entity: Base):
        with Session(self.engine) as session, session.begin():
            session.refresh(entity)

        return entity

    def add(self, entity: Base):
        with Session(self.engine) as session, session.begin():
            session.add(entity)
            session.flush()
            session.refresh(entity)
            session.expunge_all()

            if hasattr(entity, 'id'):
                return entity.id

    def destroy(self):
        # metadata = MetaData(self.engine, reflect=True)
        with contextlib.closing(self.engine.connect()) as con:
            trans = con.begin()
            Base.metadata.drop_all(bind=self.engine)
            trans.commit()

    def delete(self, entity: Base, entity_id: Union[int, str]):
        with Session(self.engine) as session, session.begin():
            return session.query(entity).filter(entity.id == entity_id).delete(synchronize_session='evaluate')

    def has_table(self, name: str):
        inspector = inspect(self.engine)
        return inspector.reflect_table(name, None)

    def query(self, entity: Base, entity_id: Union[int, str] = None, load: str = None):
        with Session(self.engine) as session, session.begin():
            if load:
                query = session.query(entity).options(joinedload(load))
            else:
                query = session.query(entity)

            if entity_id and hasattr(entity, 'id'):
                query = query.filter(entity.id == entity_id).first()
            else:
                query = query.all()

            session.expunge_all()

            return query

    def query_attr(self, entity: Base, entity_id: int, attr: str):
        with Session(self.engine) as session, session.begin():
            if hasattr(entity, 'id') and hasattr(entity, attr):
                results = session.query(entity).filter(entity.id == entity_id).first()
                attr_result = getattr(results, attr)
                session.expunge_all()
                return attr_result

    def filter(self, entity: Base, filters: Dict[Any, Callable], distinct: Any = None):
        with Session(self.engine) as session, session.begin():
            query = session.query(entity)

            for attr, exp in filters.items():
                query = query.filter(exp(attr))
            if distinct:
                query = query.distinct(distinct)
            session.expunge_all()
            return query

    def count(self, entity: Base):
        with Session(self.engine) as session, session.begin():
            return session.query(entity).count()

    def update(self, entity: Base, entity_id: int, attr: str, value):
        with Session(self.engine) as session, session.begin():
            if hasattr(entity, 'id') and hasattr(entity, attr):
                session.query(entity).filter(entity.id == entity_id).update({attr: value})
            else:
                raise ValueError(f"Could not update {type(entity)} {attr} with value {value}")
