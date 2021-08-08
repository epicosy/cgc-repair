import contextlib

from tabulate import tabulate
from cement import Controller, ex

from cgcrepair.core.corpus.cwe_parser import CWEParser
from cgcrepair.core.exc import CGCRepairError
from cgcrepair.core.handlers.database import Sanity
from sqlalchemy import MetaData


class Database(Controller):
    class Meta:
        label = 'database'
        stacked_on = 'base'
        stacked_type = 'nested'

    @ex(
        help='Removes a specified instance.',
        arguments=[
            (['--iid'], {'help': 'The id of the instance (challenge checked out).', 'type': int, 'required': True}),
            (['-d', '--destroy'], {'help': 'Deletes the files of instance.', 'action': 'store_true', 'required': False})
        ]
    )
    def remove(self):
        instance_handler = self.app.handler.get('database', 'instance', setup=True)
        res = instance_handler.delete(self.app.pargs.iid, self.app.pargs.destroy)

        if res > 0:
            self.app.log.info(f"Deleted instance {self.app.pargs.iid}")

    @ex(
        help='Deletes tables from database.'
    )
    def destroy(self):
        # TODO: make this work
        self.app.log.warning(f"This operation will delete all tables in the database: {self.app.db.engine.url}")
        res = input("Are you sure you want to continue this operation? (y/n) ")
        if res in ["Yes", "Y", "y", "yes"]:
            with contextlib.closing(self.app.db.engine.connect()) as con:
                trans = con.begin()
                self.app.log.warning(str(MetaData(bind=self.app.db.engine).sorted_tables))
                for table in reversed(MetaData().sorted_tables):
                    self.app.log.warning(f"Deleting {table}")
                    con.execute(table.delete())
                trans.commit()

    @ex(
        help='Lists specified table in the database.',
        arguments=[
            (['-I', '--instances'], {'help': 'Lists all instances in the database.', 'action': 'store_true',
                                     'required': False}),
            (['-M', '--metadata'], {'help': 'Lists metadata in the database.', 'action': 'store_true',
                                    'required': False}),
            (['-S', '--shared'], {'help': 'Lists challenges status on shared objects.', 'action': 'store_true',
                                  'required': False}),
            (['-n', '--name'], {'help': 'Lists only the name of the record in the table.', 'action': 'store_true',
                                'required': False})
        ]
    )
    def list(self):
        if self.app.pargs.instances:
            instance_handler = self.app.handler.get('database', 'instance', setup=True)
            instances = instance_handler.all()

            if self.app.pargs.name:
                self.app.render({'collection': [inst.name for inst in instances]}, 'list.jinja2')
            else:
                self.app.render({'header': "ID | MId | Name | Path | Pointer", 'collection': instances}, 'list.jinja2')

        if self.app.pargs.metadata:
            metadata_handler = self.app.handler.get('database', 'metadata', setup=True)
            metadata = metadata_handler.all()

            if self.app.pargs.name:
                self.app.render({'collection': [met.name for met in metadata]}, 'list.jinja2')
            else:
                self.app.render({'header': "Id | Name | CWE | Nº POVs | LOC | Vuln LOC | Patch LOC | Vuln Files",
                                 'collection': metadata}, 'list.jinja2')

        if self.app.pargs.shared:
            metadata_handler = self.app.handler.get('database', 'metadata', setup=True)
            corpus_handler = self.app.handler.get('corpus', 'corpus', setup=True)
            table = []

            for m in metadata_handler.all():
                challenge = corpus_handler.get(m.name)
                if challenge.has_shared_objects():
                    table.append([m.name, m.id])

            print(tabulate(table, headers=['Challenge Name', 'Challenge Id']))

    @ex(
        help="List the sanity checks",
        arguments=[(['--iid'], {'help': 'The id of the instance (challenge checked out).',
                                'type': int, 'required': False}),
                   (['-P', '--passed'], {'help': 'Filters out failed checks.', 'action': 'store_true',
                                         'required': False}),
                   (['-vp', '--pov_pass'], {'help': 'Selects checks with at least one pov passing.',
                                            'action': 'store_true', 'required': False}),
                   (['-pp', '--poll_pass'], {'help': 'Selects checks with at least one poll passing.',
                                             'action': 'store_true', 'required': False}),
                   (['-d', '--distinct'], {'help': 'Selects distinct checks based on challenge id.',
                                           'action': 'store_true', 'required': False}),
                   (['-M', '--missing'], {'help': 'Lists challenges without sanity check.',
                                          'action': 'store_true', 'required': False}),
                   ]
    )
    def sanity(self):
        instance_handler = self.app.handler.get('database', 'instance', setup=True)
        metadata_handler = self.app.handler.get('database', 'metadata', setup=True)
        table = []
        filters = {}

        if self.app.pargs.missing:
            checks = [sc.cid for sc in self.app.db.filter(Sanity, filters)]
            print([m.id for m in metadata_handler.all() if m.id not in checks])
            exit(0)

        if self.app.pargs.iid:
            filters[Sanity.iid] = lambda iid: iid == self.app.pargs.iid
        if self.app.pargs.passed:
            filters[Sanity.status] = lambda status: status == 'Passed'

        for sc in self.app.db.filter(Sanity, filters, Sanity.cid if self.app.pargs.distinct else None):
            if sc.iid:
                instance = instance_handler.get(sc.iid)
                outcomes = instance_handler.get_test_outcome(sc.iid)

                if self.app.pargs.pov_pass:
                    if True not in [not o.passed and o.sig == 11 for o in outcomes if o.is_pov]:
                        continue

                if self.app.pargs.poll_pass:
                    if True not in [o.passed and not o.failed for o in outcomes if not o.is_pov]:
                        continue

                table.append([sc.id, instance.name, sc.cid, instance.id, sc.status])
            else:
                metadata = metadata_handler.get(sc.cid)
                table.append([sc.id, metadata.name, sc.cid, ' - ', sc.status])

            # str_outcomes = '; '.join([f"{o.name}: {str(o.passed)[0]}|{o.exit_status}|{o.sig}" for o in outcomes])

        print(tabulate(table, headers=['Id', 'Challenge', 'Challenge Id', 'Instance Id', 'Status']))
        # 'Tests Outcomes (name: passed|exit status|signal)'
        # self.app.render({'header': header, 'collection': rows}, 'sanity.jinja2')

    @ex(
        help="List the benchmark's CWEs"
    )
    def cwes(self):
        metadata_handler = self.app.handler.get('database', 'metadata', setup=True)
        corpus_handler = self.app.handler.get('corpus', 'corpus', setup=True)
        metadata = metadata_handler.all()

        for m in metadata:
            challenge = corpus_handler.get(m.name)
            cwe_parser = CWEParser(description=challenge.info(), level=0)
            # TODO: get the real tests
            # tests = Tests(polls_path=challenge.paths.polls, povs_path=challenge.paths.povs)
            neg_tests = [f for f in challenge.paths.source.iterdir() if f.is_dir() and f.name.startswith("pov")]

            for pov, cwe in zip(neg_tests, cwe_parser.cwe_ids(number=False)):
                print(cwe, challenge.id(), challenge.name, challenge.id() + '_' + pov.name[-1])

    @ex(
        help='Lists outcomes for a specific instance.',
        arguments=[
            (['-t', '--test'], {'help': 'Lists all test outcomes in the database.', 'action': 'store_true',
                                'required': False}),
            (['-c', '--compile'], {'help': 'Lists all compile outcomes in the database.', 'action': 'store_true',
                                   'required': False}),
            (['--iid'], {'help': 'The id of the instance (challenge checked out).', 'type': int, 'required': True})
        ]
    )
    def outcomes(self):
        instance_handler = self.app.handler.get('database', 'instance', setup=True)
        instance = instance_handler.get(self.app.pargs.iid)

        if not instance:
            raise CGCRepairError(f"No instance {self.app.pargs.iid} found. "
                                 f"Use the ID supplied by the checkout command")

        if self.app.pargs.compile:
            outcomes = instance_handler.get_compile_outcome(self.app.pargs.iid)

            self.app.render({'header': "ID | Error | Tag | Exit Status ",
                             'collection': outcomes}, 'list.jinja2')

        if self.app.pargs.test:
            outcomes = instance_handler.get_test_outcome(self.app.pargs.iid)

            self.app.render({'header': "ID | Compile Outcome ID | Name | Error | Exit Status | Passed | Duration | "
                                       "Is POV | Signal | Failed | Total",
                             'collection': outcomes}, 'list.jinja2')
