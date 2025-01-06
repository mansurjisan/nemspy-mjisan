# configuration/base.py

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
import logging
import os
from os import PathLike
from pathlib import Path
import sys
from textwrap import indent
from typing import Iterator, List, Tuple, Union

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata

from ..model.base import (
    AttributeEntry,
    ConnectionEntry,
    EntryType,
    FileForcingEntry,
    GridRemapMethod,
    INDENTATION,
    MediationEntry,
    MediatorEntry,
    ModelEntry,
    SequenceEntry,
    VerbosityOption,
)
from ..utilities import create_symlink

def ensure_directory(directory: PathLike) -> Path:
    """
    ensure that a directory exists

    :param directory: directory path to ensure
    :returns: path to ensured directory
    """
    if not isinstance(directory, Path):
        directory = Path(directory)
    directory = directory.expanduser()
    if directory.is_file():
        directory = directory.parent
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    return directory

class ConfigurationFile(ABC):
    """
    abstraction of a configuration file
    """

    name: str = NotImplementedError

    def __init__(self, sequence: 'RunSequence', **kwargs):
        """
        :param sequence: run sequence object containing models and order
        :param kwargs: additional configuration parameters
        """
        self.sequence = sequence
        self.additional_params = kwargs

    def __getitem__(self, entry_type: type) -> List[AttributeEntry]:
        return [entry for entry in self if isinstance(entry, entry_type)]

    @property
    def version_header(self) -> str:
        installed_distributions = importlib_metadata.distributions()
        for distribution in installed_distributions:
            if (distribution.metadata['Name'] is not None
                and distribution.metadata['Name'].lower() == 'nemspy'):
                version = distribution.version
                break
        else:
            version = 'unknown'
        return f'# `{self.name}` generated with NEMSpy {version}'

    def write(
        self, filename: PathLike, overwrite: bool = False, include_version: bool = False
    ) -> Path:
        """
        write this configuration to file

        :param filename: path to file
        :param overwrite: overwrite an existing file
        :param include_version: include NEMSpy version information
        :returns: path to written file
        """
        if not isinstance(filename, Path):
            filename = Path(filename)
        ensure_directory(filename.parent)

        output = f'{self}\n'
        if include_version:
            output = f'{self.version_header}\n{output}'

        if filename.is_dir():
            filename = filename / self.name
            logging.debug(f'creating new file "{os.path.relpath(filename.resolve(), Path.cwd())}"')

        if filename.exists():
            logging.debug(f'{"overwriting" if overwrite else "skipping"} existing file "{os.path.relpath(filename.resolve(), Path.cwd())}"')
        if not filename.exists() or overwrite:
            with open(filename, 'w', newline='\n') as output_file:
                output_file.write(output)

        return filename

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.sequence)})'

class FileForcingsFile(ConfigurationFile):
    """
    ``config.rc`` file, containing paths to forcing files
    """
    name = 'config.rc'

    @property
    def entries(self) -> List[FileForcingEntry]:
        return [entry for entry in self.sequence if isinstance(entry, FileForcingEntry)]

    def __iter__(self) -> Iterator[AttributeEntry]:
        for entry in self.entries:
            yield entry

    def __str__(self) -> str:
        return '\n'.join([FileForcingEntry.__str__(model_mesh) for model_mesh in self])

class ModelConfigurationFile(ConfigurationFile):
    """
    ``model_configure`` file, containing information on modeled start and end times, as well as ensemble information
    """
    name = 'model_configure'

    def __init__(
        self,
        start_time: datetime,
        duration: timedelta,
        sequence: 'RunSequence',
        create_atm_namelist_rc: bool = True,
    ):
        self.start_time = start_time
        self.duration = duration
        self.create_atm_namelist_rc = create_atm_namelist_rc
        super().__init__(sequence)

    def write(
        self, filename: PathLike, overwrite: bool = False, include_version: bool = False,
    ) -> Path:
        filename = super().write(filename, overwrite, include_version)
        if self.create_atm_namelist_rc:
            create_symlink(filename, filename.parent / 'atm_namelist.rc', relative=True)
        return filename

    def __str__(self) -> str:
        duration_hours = round(self.duration / timedelta(hours=1))
        return '\n'.join([
            'total_member:            1',
            'print_esmf:              .true.',
            f'namelist:                {"atm_namelist.rc" if self.create_atm_namelist_rc else "model_configure"}',
            f'PE_MEMBER01:             {self.sequence.processors}',
            f'start_year:              {self.start_time.year}',
            f'start_month:             {self.start_time.month}',
            f'start_day:               {self.start_time.day}',
            f'start_hour:              {self.start_time.hour}',
            f'start_minute:            {self.start_time.minute}',
            f'start_second:            {self.start_time.second}',
            f'nhours_fcst:             {duration_hours:.0f}',
            'RUN_CONTINUE:            .false.',
            'ENS_SPS:                 .false.',
        ])

    
class NEMSConfigurationFile(ConfigurationFile):
    """
    ``nems.configure`` file, containing NEMS members, coupling connections, and run sequence information
    """
    name = 'nems.configure'

    @property
    def entries(self) -> List[AttributeEntry]:
        return [self.sequence.earth, *self.sequence.models, self.sequence]

    def __iter__(self) -> Iterator[AttributeEntry]:
        for entry in self.entries:
            yield entry

    def __str__(self) -> str:
        return '\n'.join(
            f'# {entry.entry_title} #\n{entry}\n' 
            for entry in self
        ).strip()

# Import Earth and RunSequence from your existing configuration.py
from .earth import Earth
from .sequence import RunSequence

__all__ = [
    'ConfigurationFile',
    'ensure_directory',
    'FileForcingsFile',
    'ModelConfigurationFile',
    'NEMSConfigurationFile',
    'RunSequence',
    'Earth',
]
