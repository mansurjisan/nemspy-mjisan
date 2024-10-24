# test_ufs_config.py

from datetime import datetime, timedelta
import os
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_ufs():
    logger.info("Starting UFS configuration test...")
    
    try:
        from nemspy import ModelingSystem
        from nemspy.model.base import UFSModelEntry, EntryType
        logger.info("Successfully imported required modules")
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return

    try:
        # Create ModelingSystem
        start_time = datetime(2020, 6, 1)
        end_time = start_time + timedelta(days=1)
        interval = timedelta(hours=1)
        
        nems = ModelingSystem(
            start_time=start_time,
            end_time=end_time,
            interval=interval,
        )
        logger.info("Created ModelingSystem successfully")

        # Create model entries

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
        logger.info("Created ocean entry")

        # Add models to system
        nems['OCN'] = ocn
        logger.info("Added all models to system")

        # Set up connections

        # Create test directory
        test_dir = 'test_ufs_output'
        os.makedirs(test_dir, exist_ok=True)
        logger.info(f"Created test directory: {test_dir}")

        # Write UFS configuration
        logger.info("Attempting to write UFS configuration...")
        nems.write_ufs_config(
            directory=test_dir,
            coupling_mode='coastal',
            history_n=1,
            restart_n=12,
            stop_n=120,
            overwrite=True
        )
        
        # Verify file creation
        config_path = os.path.join(test_dir, 'ufs.configure')
        if os.path.exists(config_path):
            logger.info(f"Successfully created UFS configuration at {config_path}")
            # Print the first few lines of the configuration
            with open(config_path, 'r') as f:
                logger.info("First 10 lines of UFS configuration:")
                for i, line in enumerate(f):
                    if i < 10:
                        logger.info(line.strip())
        else:
            logger.error(f"Failed to create configuration at {config_path}")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    test_ufs()
