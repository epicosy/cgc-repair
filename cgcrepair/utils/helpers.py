import os
import sys
from pathlib import Path

import psutil

from typing import List


def kill_by_pid(pids: List[str] = None):
    killed_pids = []
    """
        Kills processes from a supplied list of pids 
    """
    for pid in pids:
        print(int(pid))
        if psutil.pid_exists(int(pid)):
            os.system(f"kill -9 {pid}")
            killed_pids.append(pid)

    return killed_pids


def kill_by_name(process_name: str,  target_pids: List[str] = None):
    """
    Gets a list of all the PIDs of a all the running process whose name contains the given string process_name and
    kills the process. If target_pids list is supplied, it checks the pids for the process with the list
    """
    # based on https://thispointer.com/python-check-if-a-process-is-running-by-name-and-find-its-process-id-pid/
    # Iterate over the all the running process
    killed_pids = []

    for proc in psutil.process_iter():
        try:
            proc_info = proc.as_dict(attrs=['pid', 'name', 'create_time'])
            # Check if process name contains the given name string.
            if process_name in proc_info['name']:
                if psutil.pid_exists(proc_info['pid']):
                    if target_pids and proc_info['pid'] not in target_pids:
                        continue
                    os.system(f"kill -9 {proc_info['pid']}")
                    killed_pids.append(proc_info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as pe:
            sys.stderr.write(str(pe))

    return killed_pids


def collect_files(path: Path, target_suffix: str) -> List[Path]:
    coverage_files = []

    def recurse_walk(current: Path, parent: Path, suffix: str):
        for f in current.iterdir():
            if f.is_dir():
                recurse_walk(f, parent / Path(f.name), suffix)
            elif f.name.endswith(suffix):
                short_path = parent / Path(f.name)
                coverage_files.append(short_path)

    for folder in path.iterdir():
        if folder.is_dir():
            recurse_walk(folder, Path(folder.name), target_suffix)

    return coverage_files
