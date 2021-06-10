from typing import List, Union
from cgcrepair.utils.parse.cwe import cwe_from_info, main_cwe, get_name, top_parent


class CWEParser:
    def __init__(self, description: str, level: int = 3):
        self.description = description
        self.main = None
        self.level = level

    def cwe_ids(self, number: bool = True) -> List[Union[int, str]]:
        if number:
            return [int(cwe.split('-')[1]) for cwe in cwe_from_info(self.description)]
        else:
            return [cwe for cwe in cwe_from_info(self.description)]

    def cwe_type(self):
        ids = self.cwe_ids()
        main = main_cwe(ids, count=3)

        return f"CWE-{main}: {get_name(main)}"

    def get_cwes(self, parent: bool = False, name: bool = False) -> List[Union[str, int]]:
        ids = self.cwe_ids()

        if parent:
            ids = [top_parent(_id, None, count=3) for _id in ids]

        if name:
            ids = [f"CWE-{_id} {get_name(_id)}" for _id in ids]

        return ids
