"""Utilities for file operations."""


import tarfile
import zipfile
from pathlib import Path


def safe_extract_zip(zf: zipfile.ZipFile, dest: Path) -> None:
    """Extract a zip file safely.

    Args:
      zf: The zip file to extract.
      dest: The destination directory to extract the zip file to.
    """
    for member in zf.namelist():
        member_path = dest / member
        if not member_path.resolve().is_relative_to(dest.resolve()):
            raise Exception(f"Unsafe path detected in zip: {member}")
        zf.extract(member, dest)


def safe_extract_tar(tf: tarfile.TarFile, dest: Path) -> None:
    """Extract a tar file safely.

    Args:
      tf: The tar file to extract.
      dest: The destination directory to extract the tar file to.
    """
    for member in tf.getmembers():
        member_path = dest / member.name
        if not member_path.resolve().is_relative_to(dest.resolve()):
            raise Exception(f"Unsafe path detected in tar: {member.name}")
        tf.extract(member, dest)
