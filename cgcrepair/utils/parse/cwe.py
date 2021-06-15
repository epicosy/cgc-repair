import itertools
from typing import Union, List

import pandas as pd
import re

CWE_REGEX = r'CWE-\d{1,4}'
PARENT_CWE = r"^::NATURE:ChildOf:CWE ID:(\d{1,4}):"
PRECEDE_CWE = r"::NATURE:CanPrecede:CWE ID:(\d{1,4}):"
PEER_CWE = r"::NATURE:PeerOf:CWE ID:(\d{1,4}):"
ALIAS_CWE = r"::NATURE:CanAlsoBe:CWE ID:(\d{1,4}):"
# TODO: fix this path, can not remain like this
cwe_dict = pd.read_csv('/etc/cgc-repair/cwe_dict.csv', index_col=False)
cwe_dict.rename(columns={'CWE-ID': 'cwe_id', 'Name': 'name', 'Related Weaknesses': 'relatives'}, inplace=True)
no_null_relatives = cwe_dict[cwe_dict.relatives.notnull()]
cwe_alias = {}
cwe_precedents = {}


def cwe_from_info(description: str) -> list:
    return re.findall(CWE_REGEX, description)


def most_common(lst: list):
    return max(itertools.groupby(sorted(lst)), key=lambda tup: (len(list(tup[1])), -lst.index(tup[0])))[0]


def populate_relatives():
    def get_aliases(relatives: str):
        return re.findall(ALIAS_CWE, relatives)

    def get_peers(relatives: str):
        return re.findall(PEER_CWE, relatives)

    def get_precedents(relatives: str):
        return re.findall(PRECEDE_CWE, relatives)

    for i, row in no_null_relatives.iterrows():
        aliases = get_aliases(row.relatives)
        peers = get_peers(row.relatives)
        precedents = get_precedents(row.relatives)

        if aliases:
            for alias in aliases:
                cwe_alias[int(alias)] = row.cwe_id

        if peers:
            for peer in peers:
                cwe_alias[int(peer)] = row.cwe_id

        if precedents:
            for precedent in precedents:
                cwe_precedents[int(precedent)] = row.cwe_id


def match_parent_cwe(related_weakness: str) -> Union[int, None]:
    match = re.match(PARENT_CWE, related_weakness)

    if match:
        return int(match.group(1))
    else:
        return None


def get_parent(cwe_id: int) -> Union[int, None]:
    if not cwe_id:
        return None

    cwe_row = no_null_relatives[no_null_relatives.cwe_id == cwe_id]

    if cwe_row.empty:
        return None

    return match_parent_cwe(cwe_row.relatives.values[0])


def top_parent(cwe_id: int, previous: int = None, count: int = 2, depth: int = 0) -> int:
    if not cwe_id:
        return previous

    if depth == count:
        if cwe_id:
            return cwe_id
        return previous

    parent = get_parent(cwe_id)
    alias = cwe_alias.get(cwe_id)

    if parent:
        return top_parent(parent, cwe_id, count, depth + 1)
    elif alias:
        return top_parent(alias, cwe_id, count, depth + 1)
    else:
        return cwe_id


def get_name(cwe_id: int) -> str:
    if not cwe_id:
        return ""

    cwe_row = cwe_dict[cwe_dict.cwe_id == cwe_id]

    if cwe_row.empty:
        return ""

    return cwe_row.name.values[0]


def main_cwe(cwe_ids: List[int], count: int):
    if not cwe_ids:
        return None

    parents = [top_parent(cwe_id, count=count) for cwe_id in cwe_ids]

    if len(parents) > 1:
        return most_common(parents)

    return parents[0]


populate_relatives()
