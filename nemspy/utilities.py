import logging
import os
from datetime import datetime
from os import PathLike
from pathlib import Path
import shutil
import warnings


def create_symlink(
    source_filename: PathLike, symlink_filename: PathLike, relative: bool = False
):
    """
    :param source_filename: path to point to
    :param symlink_filename: path at which to create symlink
    :param relative: make symlink relative to source location
    """

    if not isinstance(source_filename, Path):
        source_filename = Path(source_filename)
    if not isinstance(symlink_filename, Path):
        symlink_filename = Path(symlink_filename)

    if symlink_filename.is_symlink():
        logging.debug(f'removing symlink "{symlink_filename}"')
        os.remove(symlink_filename)
    symlink_filename = symlink_filename.parent.absolute().resolve() / symlink_filename.name

    starting_directory = None
    if relative:
        starting_directory = Path().cwd().resolve()
        os.chdir(symlink_filename.parent)
        if source_filename.is_absolute():
            try:
                source_filename = source_filename.relative_to(symlink_filename.parent)
            except ValueError as error:
                warnings.warn(error)
                os.chdir(starting_directory)
    else:
        source_filename = source_filename.absolute()

    try:
        symlink_filename.symlink_to(source_filename)
    except Exception as error:
        warnings.warn(f'could not create symbolic link: {error}')
        shutil.copyfile(source_filename, symlink_filename)

    if starting_directory is not None:
        os.chdir(starting_directory)

def parse_datetime(value: str) -> datetime:
    """
    parse datetime from string

    :param value: datetime string
    :return: parsed datetime object
    """
    try:
        # Try different datetime formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%Y%m%d %H:%M:%S',
            '%Y%m%d %H:%M',
            '%Y%m%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
                
        raise ValueError(f"time data '{value}' does not match any known format")
    except Exception as e:
        raise ValueError(f"Failed to parse datetime from '{value}': {str(e)}")

