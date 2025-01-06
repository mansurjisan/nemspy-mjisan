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
git clone --branch -b ufs-coastal-temp https://github.com/mansurjisan/ufs-nemspy.git

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
```

### UFS Configuration for ATM OCN with Atmospheric Forcing Provided through CMEPS Mediator 
```python
from datetime import datetime, timedelta
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_ufs_config():
    logger.info("Starting UFS configuration test...")

    try:
        from nemspy import ModelingSystem
        from nemspy.model.base import UFSModelEntry, EntryType
        from nemspy.configuration import UFSModelConfigurationFile
        logger.info("Successfully imported required modules")

        # Create ModelingSystem
        start_time = datetime(2012, 10, 27)
        end_time = start_time + timedelta(hours=56)
        interval = timedelta(seconds=1800)

        nems = ModelingSystem(
            start_time=start_time,
            end_time=end_time,
            interval=interval,
        )
        logger.info("Created ModelingSystem successfully")

        # Create mediator
        med = UFSModelEntry(
            name='cmeps',
            model_type=EntryType.MEDIATOR,
            petlist_bounds=(0, 319),
            omp_num_threads=1,
            ATM_model='datm',
            OCN_model='schism',
            history_n=1,
            history_option='nhours',
            history_ymd=-999,
            coupling_mode='coastal',
            pio_typename='PNETCDF',
            pio_stride=8
        )
        logger.info("Created mediator entry")

        # Create atmosphere model
        atm = UFSModelEntry(
            name='datm',
            model_type=EntryType.ATMOSPHERIC,
            petlist_bounds=(0, 159),
            omp_num_threads=1,
            Verbosity=0,
            DumpFields='false',
            ProfileMemory='false',
            OverwriteSlice='true'
        )
        logger.info("Created atmosphere entry")

        # Create ocean model
        ocn = UFSModelEntry(
            name='schism',
            model_type=EntryType.OCEAN,
            petlist_bounds=(160, 319),
            omp_num_threads=1,
            Verbosity=0,
            DumpFields='false',
            ProfileMemory='false',
            OverwriteSlice='true',
            meshloc='element',
            CouplingConfig='none'
        )
        logger.info("Created ocean entry")

        # Add models to system
        nems['MED'] = med
        nems['ATM'] = atm
        nems['OCN'] = ocn
        logger.info("Added models to system")

        # Set up connections
        nems.connect('ATM', 'MED')
        nems.connect('OCN', 'MED')
        logger.info("Set up model connections")

        # Create output directory
        test_dir = 'test_ufs_output'
        os.makedirs(test_dir, exist_ok=True)
        logger.info(f"Created directory: {test_dir}")

        # Write UFS configuration files
        logger.info("Writing UFS configuration files...")

        # Write ufs.configure
        nems.write_ufs_config(
            directory=test_dir,
            coupling_mode='coastal',
            history_n=1,
            restart_n=12,
            stop_n=56,
            overwrite=True
        )

        # Write model_configure
        model_config = UFSModelConfigurationFile(
            start_time=start_time,
            duration=end_time - start_time,
            sequence=nems.sequence,  # Changed this line
            dt_atmos=720,
            quilting=True,
            quilting_restart=False,
            write_groups=1,
            write_tasks_per_group=6,
            itasks=1,
            output_history=True,
            imo=384,
            jmo=190,
            output_fh='12 -1'
        )

        model_config.write(os.path.join(test_dir, 'model_configure'), overwrite=True)
        logger.info("Wrote model_configure file")

        # Verify configurations
        for filename in ['ufs.configure', 'model_configure']:
            config_path = os.path.join(test_dir, filename)
            if os.path.exists(config_path):
                logger.info(f"Successfully created {filename} at {config_path}")
                with open(config_path, 'r') as f:
                    logger.info(f"{filename} preview:")
                    print(f.read())
            else:
                logger.error(f"Failed to create {filename} at {config_path}")

    except Exception as e:
        logger.error(f"Error during configuration: {e}", exc_info=True)

if __name__ == "__main__":
    create_ufs_config()

```
## Output Examples
### UFS Output
#### `ufs.configure`
```fortran

#############################################
####  UFS Run-Time Configuration File  #####
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
MED_petlist_bounds:             0 319
MED_omp_num_threads:            1
MED_attributes::
    ATM_model = datm
    OCN_model = schism
    history_n = 1
    history_option = nhours
    history_ymd = -999
    coupling_mode = coastal
    pio_typename = PNETCDF
    pio_stride = 8
::

# ATM #
ATM_model:                      datm
ATM_petlist_bounds:             0 159
ATM_omp_num_threads:            1
ATM_attributes::
    Verbosity = 0
    DumpFields = false
    ProfileMemory = false
    OverwriteSlice = true
::

# OCN #
OCN_model:                      schism
OCN_petlist_bounds:             160 319
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
@1800
  ATM -> MED :remapMethod=redist
  MED med_phases_post_atm
  OCN -> MED :remapMethod=redist
  MED med_phases_post_ocn
  MED med_phases_prep_atm
  MED med_phases_prep_ocn_accum
  MED med_phases_prep_ocn_avg
  MED -> ATM :remapMethod=redist
  MED -> OCN :remapMethod=redist
  ATM
  OCN
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
  stop_n = 56
  stop_option = nhours
  stop_ymd = -999
::
```
#### `model_configure`
```fortran
start_year:              2012
start_month:             10
start_day:               27
start_hour:              00
start_minute:            0
start_second:            0
nhours_fcst:             56
fhrot:                   0
dt_atmos:                720
restart_interval:        0
quilting:                .true.
quilting_restart:        .false.
write_groups:            1
write_tasks_per_group:   6
itasks:                  1
output_history:          .true.
history_file_on_native_grid: .false.
write_dopost:            .false.
write_nsflip:            .false.
num_files:               2
filename_base:           atmmesh.
output_grid:             'cubed_sphere_grid'
output_file:             'netcdf'
zstandard_level:         5
ideflate:                0
quantize_mode:           'quantize_bitround'
quantize_nsd:            0
ichunk2d:                0
jchunk2d:                0
ichunk3d:                0
jchunk3d:                0
kchunk3d:                0
imo:                     384
jmo:                     190
output_fh:               12 -1
iau_offset:              0
```



