# configuration.py

import warnings
from typing import Dict, List, Union
from datetime import datetime, timedelta
from os import PathLike
from pathlib import Path

warnings.warn(
    "Direct use of configuration.py is deprecated. Use nemspy.configuration.* instead",
    DeprecationWarning,
    stacklevel=2
)

# Import from new locations
from nemspy.configuration.base import (
    ConfigurationFile,
    ensure_directory,
    FileForcingsFile,
    ModelConfigurationFile,
    NEMSConfigurationFile,
)
from nemspy.configuration.earth import Earth
from nemspy.configuration.sequence import RunSequence
from nemspy.configuration.ufs import UFSConfigurationFile

# Re-export for backward compatibility
__all__ = [
    'ConfigurationFile',
    'Earth',
    'ensure_directory',
    'FileForcingsFile',
    'ModelConfigurationFile',
    'NEMSConfigurationFile',
    'RunSequence',
    'UFSConfigurationFile'
]

# For backward compatibility, maintain the original class structure
class Earth(Earth):
    pass

class RunSequence(RunSequence):
    pass

class ConfigurationFile(ConfigurationFile):
    pass

class NEMSConfigurationFile(NEMSConfigurationFile):
    pass

class FileForcingsFile(FileForcingsFile):
    pass

class ModelConfigurationFile(ModelConfigurationFile):
    pass
