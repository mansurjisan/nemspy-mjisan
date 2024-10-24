# UFS-NEMSpy

[![tests](https://github.com/noaa-ocs-modeling/NEMSpy/workflows/tests/badge.svg)](https://github.com/noaa-ocs-modeling/NEMSpy/actions?query=workflow%3Atests)
[![codecov](https://codecov.io/gh/noaa-ocs-modeling/nemspy/branch/master/graph/badge.svg?token=uyeRvhmBtD)](https://codecov.io/gh/noaa-ocs-modeling/nemspy)
[![build](https://github.com/noaa-ocs-modeling/NEMSpy/workflows/build/badge.svg)](https://github.com/noaa-ocs-modeling/NEMSpy/actions?query=workflow%3Abuild)
[![version](https://img.shields.io/pypi/v/nemspy)](https://pypi.org/project/nemspy)
[![license](https://img.shields.io/github/license/noaa-ocs-modeling/nemspy)](https://creativecommons.org/share-your-work/public-domain/cc0)
[![style](https://sourceforge.net/p/oitnb/code/ci/default/tree/_doc/_static/oitnb.svg?format=raw)](https://sourceforge.net/p/oitnb/code)
[![documentation](https://readthedocs.org/projects/nemspy/badge/?version=latest)](https://nemspy.readthedocs.io/en/latest/?badge=latest)

UFS-NEMSpy generates configuration files for both NEMS and UFS coupled modeling applications. For NEMS, it generates (`nems.configure`, `config.rc`, `model_configure`, `atm_namelist.rc`). For UFS, it generates (`ufs.configure` and related configuration files).

```shell
git clone --branch ufs-coastal https://github.com/mansurjisan/ufs-nemspy.git

cd ufs-nemspy/

pip install -e .
```

This branch extends NEMSpy to support both NEMS and UFS configurations. NEMS and UFS implement the [National Unified Operational Prediction Capability (NUOPC)](https://www.earthsystemcog.org/projects/nuopc/).

Documentation can be found at https://nemspy.readthedocs.io

## New Features
- Support for UFS Coastal configurations
- CMEPS mediator support
- Flexible coupling configurations (OCN-only, ATM-OCN, ATM-OCN-WAV)
- UFS-compliant configuration file generation

## Usage Examples

### Traditional NEMS Configuration
```python
from datetime import datetime, timedelta
from pathlib import Path

from nemspy import ModelingSystem
from nemspy.model import ADCIRCEntry, AtmosphericForcingEntry, WaveWatch3ForcingEntry

# Original NEMS configuration example remains the same...
```

### UFS Coastal Configuration
```python
from datetime import datetime, timedelta
from nemspy import ModelingSystem
from nemspy.model.base import UFSModelEntry, EntryType

# Create modeling system
start_time = datetime(2020, 6, 1)
end_time = start_time + timedelta(days=1)
interval = timedelta(hours=1)

nems = ModelingSystem(
    start_time=start_time,
    end_time=end_time,
    interval=interval,
)

# Create UFS model entries
med = UFSModelEntry(
    name='cmeps',
    model_type=EntryType.MEDIATOR,
    petlist_bounds=(0, 7),
    omp_num_threads=1,
    ATM_model='datm',
    OCN_model='schism',
    WAV_model='ww3',
    history_n=1,
    history_option='nhours',
    history_ymd=-999,
    coupling_mode='coastal'
)

atm = UFSModelEntry(
    name='datm',
    model_type=EntryType.ATMOSPHERIC,
    petlist_bounds=(0, 7),
    omp_num_threads=1,
    Verbosity=0,
    DumpFields='false',
    ProfileMemory='false',
    OverwriteSlice='true'
)

ocn = UFSModelEntry(
    name='schism',
    model_type=EntryType.OCEAN,
    petlist_bounds=(8, 15),
    omp_num_threads=1,
    Verbosity=0,
    DumpFields='false',
    ProfileMemory='false',
    OverwriteSlice='true',
    meshloc='element',
    CouplingConfig='none'
)

# Add models and set connections
nems['MED'] = med
nems['ATM'] = atm
nems['OCN'] = ocn

nems.connect('ATM', 'MED')
nems.connect('OCN', 'MED')

# Write UFS configuration
nems.write_ufs_config(
    directory='ufs_configuration',
    coupling_mode='coastal',
    history_n=1,
    restart_n=12,
    stop_n=120,
    overwrite=True
)
```
## Output Examples
### UFS Output
#### `ufs.configure`
```fortran

#############################################
####  NEMS Run-Time Configuration File  #####
#############################################
# ESMF #
logKindFlag:            ESMF_LOGKIND_MULTI
globalResourceControl:  true
# EARTH #
EARTH_component_list: ATM MED OCN
EARTH_attributes::
  Verbosity = 0
::
# MED #
MED_model:                      cmeps
MED_petlist_bounds:             0 7
MED_omp_num_threads:            1
MED_attributes::
    ATM_model = datm
    OCN_model = schism
    history_n = 1
    history_option = nhours
    history_ymd = -999
    coupling_mode = coastal
::

# ATM #
ATM_model:                      datm
ATM_petlist_bounds:             0 7
ATM_omp_num_threads:            1
ATM_attributes::
    Verbosity = 0
    DumpFields = false
    ProfileMemory = false
    OverwriteSlice = true
::

# OCN #
OCN_model:                      schism
OCN_petlist_bounds:             8 15
OCN_omp_num_threads:            1
OCN_attributes::
    Verbosity = 0
    DumpFields = false
    ProfileMemory = false
    OverwriteSlice = true
    meshloc = element
    CouplingConfig = none
::

# Run Sequence #
runSeq::
@3600
  MED med_phases_prep_atm
  MED med_phases_prep_ocn_accum
  MED med_phases_prep_ocn_avg
  MED -> ATM :remapMethod=redist
  MED -> OCN :remapMethod=redist
  MED -> MED :remapMethod=redist
  ATM
  OCN
  MED
  ATM -> MED :remapMethod=redist
  OCN -> MED :remapMethod=redist
  MED -> MED :remapMethod=redist
  MED med_phases_post_atm
  MED med_phases_post_ocn
  MED med_phases_post_med
  MED med_phases_history_write
  MED med_phases_restart_write
@
::
ALLCOMP_attributes::
  ScalarFieldCount = 3
  ScalarFieldIdxGridNX = 1
  ScalarFieldIdxGridNY = 2
  ScalarFieldIdxNextSwCday = 3
  ScalarFieldName = cpl_scalars
  start_type = startup
  restart_dir = RESTART/
  case_name = ufs.cpld
  restart_n = 12
  restart_option = nhours
  restart_ymd = -999
  orb_eccen = 1.e36
  orb_iyear = 2000
  orb_iyear_align = 2000
  orb_mode = fixed_year
  orb_mvelp = 1.e36
  orb_obliq = 1.e36
  stop_n = 120
  stop_option = nhours
  stop_ymd = -999
::
```

