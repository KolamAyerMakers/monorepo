from __future__ import annotations

import stat
import subprocess
import tarfile
import tempfile
from pathlib import Path

from tests.support.paths import SALTSTACK_DIRECTORY


RELEASE_SCRIPT = (
    SALTSTACK_DIRECTORY / "states/roles/kam-classroom/files/maker-guide-release"
)


def _run_release(
    artifact_directory: Path,
    release_directory: Path,
    action: str,
) -> None:
    assert (
        subprocess.run(
            [
                str(RELEASE_SCRIPT),
                str(artifact_directory),
                str(release_directory),
                action,
            ],
            check=False,
        ).returncode
        == 0
    )


def test_release_staging_activation_and_pruning_are_retry_safe() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        installation_directory = Path(temporary_directory)
        artifact_directory = installation_directory / "incoming"
        release_directory = installation_directory / "releases"
        source_directory = installation_directory / "source"
        artifact_directory.mkdir()
        release_directory.mkdir()
        (source_directory / "bin").mkdir(parents=True)
        source_bot_path = source_directory / "bin/maker-guide-bot"
        assert source_bot_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8") > 0
        source_bot_path.chmod(0o775)

        with tarfile.open(
            artifact_directory / "maker-guide.test.tar.gz",
            "w:gz",
        ) as archive:
            archive.add(source_directory, arcname=".")

        _run_release(artifact_directory, release_directory, "stage")
        _run_release(artifact_directory, release_directory, "staged")
        assert (
            stat.S_IMODE(
                (release_directory / "maker-guide.test/bin/maker-guide-bot")
                .stat()
                .st_mode
            )
            == 0o755
        )

        (release_directory / "old").mkdir()
        (release_directory / "obsolete").mkdir()
        (installation_directory / "current").symlink_to("releases/old")
        (installation_directory / "current.next").symlink_to("stale")
        (installation_directory / "previous.next").symlink_to("stale")
        assert (installation_directory / "pending-release.next").write_text(
            "stale\n", encoding="utf-8"
        ) > 0

        _run_release(artifact_directory, release_directory, "activate")
        _run_release(artifact_directory, release_directory, "active")
        _run_release(artifact_directory, release_directory, "pending")
        assert (installation_directory / "current").readlink() == Path(
            "releases/maker-guide.test"
        )
        assert (installation_directory / "previous").readlink() == Path("releases/old")
        assert not (installation_directory / "current.next").exists()
        assert not (installation_directory / "previous.next").exists()

        _run_release(artifact_directory, release_directory, "prune")
        _run_release(artifact_directory, release_directory, "prune")
        assert (release_directory / "maker-guide.test").is_dir()
        assert (release_directory / "old").is_dir()
        assert not (release_directory / "obsolete").exists()

        _run_release(artifact_directory, release_directory, "complete")
        assert not (installation_directory / "pending-release").exists()
