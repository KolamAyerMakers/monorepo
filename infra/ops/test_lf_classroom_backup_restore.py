#!/usr/bin/env python3
"""Check restored Ergo data is assigned to the local service account."""

import importlib.machinery
import importlib.util
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).with_name("lf-classroom-backup-restore")
SCRIPT_LOADER = importlib.machinery.SourceFileLoader(
    "lf_classroom_backup_restore", str(SCRIPT_PATH)
)
SCRIPT_SPECIFICATION = importlib.util.spec_from_loader(
    SCRIPT_LOADER.name, SCRIPT_LOADER
)
assert SCRIPT_SPECIFICATION is not None
backup_restore = importlib.util.module_from_spec(SCRIPT_SPECIFICATION)
sys.modules[SCRIPT_LOADER.name] = backup_restore
SCRIPT_LOADER.exec_module(backup_restore)


def test_repair_ergo_ownership() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        data_path = Path(temporary_directory) / "ergo"
        data_path.mkdir()
        database_path = data_path / "ircd.db"
        database_path.touch()
        with (
            patch.object(
                backup_restore.pwd,
                "getpwnam",
                return_value=SimpleNamespace(pw_uid=1234),
            ),
            patch.object(
                backup_restore.grp,
                "getgrnam",
                return_value=SimpleNamespace(gr_gid=5678),
            ),
            patch.object(backup_restore.os, "chown") as chown,
        ):
            backup_restore.repair_ergo_ownership(data_path)

    assert chown.call_args_list == [
        ((data_path, 1234, 5678),),
        ((database_path, 1234, 5678),),
    ]


if __name__ == "__main__":
    test_repair_ergo_ownership()
