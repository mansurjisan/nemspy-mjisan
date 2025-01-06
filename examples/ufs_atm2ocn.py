# ufs_atm2ocn.py
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
