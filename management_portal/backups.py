"""Bounded, symlink-safe discovery of operational backup artifacts."""

from dataclasses import dataclass
from pathlib import Path
import stat


@dataclass(frozen=True)
class BackupArtifact:
    path: Path
    source: str
    modified_timestamp: float
    size_bytes: int

    @property
    def name(self):
        return self.path.name


@dataclass(frozen=True)
class BackupInventory:
    daily: tuple
    pre_release: tuple

    @property
    def preferred(self):
        """Prefer the daily backup stream; use a release snapshot as fallback."""
        if self.daily:
            return self.daily[0]
        return self.pre_release[0] if self.pre_release else None

    @property
    def history(self):
        return tuple(sorted(
            (*self.daily, *self.pre_release),
            key=lambda item: item.modified_timestamp,
            reverse=True,
        ))


def find_backup_inventory(backup_root):
    """Inspect only ``backup_root`` and its fixed ``daily`` child.

    Neither directory nor file symlinks are followed. Nested directories are
    deliberately ignored so a configured backup path cannot turn this status
    check into an unbounded filesystem traversal.
    """
    root = Path(backup_root)
    if not _is_real_directory(root):
        return BackupInventory(daily=(), pre_release=())

    daily_dir = root / "daily"
    daily = _regular_backups(daily_dir, "postgres-*.dump", "daily")
    pre_release = _regular_backups(root, "pre-release-*.dump", "pre_release")
    return BackupInventory(daily=daily, pre_release=pre_release)


def _is_real_directory(path):
    try:
        return stat.S_ISDIR(path.lstat().st_mode)
    except OSError:
        return False


def _regular_backups(directory, pattern, source):
    if not _is_real_directory(directory):
        return ()

    artifacts = []
    try:
        candidates = directory.glob(pattern)
        for candidate in candidates:
            try:
                metadata = candidate.lstat()
            except OSError:
                continue
            if not stat.S_ISREG(metadata.st_mode):
                continue
            artifacts.append(BackupArtifact(
                path=candidate,
                source=source,
                modified_timestamp=metadata.st_mtime,
                size_bytes=metadata.st_size,
            ))
    except OSError:
        return ()
    return tuple(sorted(artifacts, key=lambda item: item.modified_timestamp, reverse=True))
