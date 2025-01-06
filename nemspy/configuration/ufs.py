from datetime import datetime, timedelta
from os import PathLike
from .base import ConfigurationFile
from ..model.base import EntryType, ModelEntry, UFSModelEntry
from typing import List, Dict
from datetime import datetime, timedelta


class UFSConfigurationFile(ConfigurationFile):
    """UFS configuration file generator"""
    
    name = 'ufs.configure'
    
    def __init__(self, sequence, **kwargs):
        super().__init__(sequence, **kwargs)
        self.coupling_mode = kwargs.get('coupling_mode', 'uncoupled')
        self.history_n = kwargs.get('history_n', 1)
        self.restart_n = kwargs.get('restart_n', 12)
        self.stop_n = kwargs.get('stop_n', 120)

    def _get_component_list(self):
        """Get list of active components"""
        components = []
        for model in self.sequence.models:
            if model.entry_type != EntryType.MEDIATOR:
                components.append(model.entry_type.value)
        return components


    def _generate_run_sequence(self, components):
        """Generate run sequence based on available components"""
        has_mediator = any(model.entry_type == EntryType.MEDIATOR for model in self.sequence.models)
        has_wave = 'WAV' in components
        
        # Initialize runseq with appropriate timestep
        runseq = ["# Run Sequence #", "runSeq::", f"@{3600 if has_wave else 1800}"]
        
        if has_mediator:
            if has_wave:
                # Sequence for ATM-OCN-WAV-MED
                # First: MED prep phases
                if 'ATM' in components:
                    runseq.append("  MED med_phases_prep_atm")
                if 'OCN' in components:
                    runseq.extend([
                        "  MED med_phases_prep_ocn_accum",
                        "  MED med_phases_prep_ocn_avg"
                    ])
                if 'WAV' in components:
                    runseq.extend([
                        "  MED med_phases_prep_wav_accum",
                        "  MED med_phases_prep_wav_avg"
                    ])
                    
                # MED to model connections
                for comp in ['ATM', 'OCN', 'WAV']:
                    if comp in components:
                        runseq.append(f"  MED -> {comp} :remapMethod=redist")
                    
                # Model executions
                for comp in ['ATM', 'OCN', 'WAV']:
                    if comp in components:
                        runseq.append(f"  {comp}")
                        
                # Model to MED connections
                for comp in ['ATM', 'OCN', 'WAV']:
                    if comp in components:
                        runseq.append(f"  {comp} -> MED :remapMethod=redist")
                        
                # MED post phases
                for comp in ['ATM', 'OCN', 'WAV']:
                    if comp in components:
                        runseq.append(f"  MED med_phases_post_{comp.lower()}")
                        
                # History and restart writes
                runseq.extend([
                    "  MED med_phases_history_write",
                    "  MED med_phases_restart_write"
                ])
            else:
                # Sequence for ATM-OCN-MED
                # First: Model to MED connections and post phases
                for comp in ['ATM', 'OCN']:
                    if comp in components:
                        runseq.append(f"  {comp} -> MED :remapMethod=redist")
                        runseq.append(f"  MED med_phases_post_{comp.lower()}")
                
                # Second: MED prep phases
                if 'ATM' in components:
                    runseq.append("  MED med_phases_prep_atm")
                if 'OCN' in components:
                    runseq.extend([
                        "  MED med_phases_prep_ocn_accum",
                        "  MED med_phases_prep_ocn_avg"
                    ])
                    
                # Third: MED to model connections
                for comp in ['ATM', 'OCN']:
                    if comp in components:
                        runseq.append(f"  MED -> {comp} :remapMethod=redist")
                        
                # Finally: Model executions
                for comp in ['ATM', 'OCN']:
                    if comp in components:
                        runseq.append(f"  {comp}")
        
        runseq.extend(["@", "::"])
        return runseq
        
    def _generate_allcomp_attributes(self):
        """Generate ALLCOMP attributes section"""
        return [
            "ALLCOMP_attributes::",
            "  ScalarFieldCount = 3",
            "  ScalarFieldIdxGridNX = 1",
            "  ScalarFieldIdxGridNY = 2",
            "  ScalarFieldIdxNextSwCday = 3",
            "  ScalarFieldName = cpl_scalars",
            "  start_type = startup",
            "  restart_dir = RESTART/",
            "  case_name = ufs.cpld",
            f"  restart_n = {self.restart_n}",
            "  restart_option = nhours",
            "  restart_ymd = -999",
            "  orb_eccen = 1.e36",
            "  orb_iyear = 2000",
            "  orb_iyear_align = 2000",
            "  orb_mode = fixed_year",
            "  orb_mvelp = 1.e36",
            "  orb_obliq = 1.e36",
            f"  stop_n = {self.stop_n}",
            "  stop_option = nhours",
            "  stop_ymd = -999",
            "::"
        ]

    def __str__(self) -> str:
        # Get active components
        components = self._get_component_list()
        if 'MED' in [model.entry_type.value for model in self.sequence.models]:
            components.append('MED')
            
        config = [
            "#############################################",
            "####  UFS Run-Time Configuration File  #####",
            "#############################################",
            "# ESMF #",
            "logKindFlag:            ESMF_LOGKIND_MULTI",
            "globalResourceControl:  true",
            "# EARTH #",
            f"EARTH_component_list: {' '.join(sorted(components))}",
            "EARTH_attributes::",
            "  Verbosity = 0",
            "::"
        ]

        # Add each model's configuration
        for model in self.sequence.models:
            config.append(f"# {model.entry_type.value} #")
            config.append(str(model))
            config.append("")

        # Add run sequence
        config.extend(self._generate_run_sequence(components))
        
        # Add ALLCOMP attributes
        config.extend(self._generate_allcomp_attributes())

        return '\n'.join(config)


class UFSModelConfigurationFile(ConfigurationFile):
    """
    ``model_configure`` file for UFS, containing more detailed configuration parameters
    """
    name = 'model_configure'

    def __init__(
        self,
        start_time: datetime,
        duration: timedelta,
        sequence: 'RunSequence',
        dt_atmos: int = 720,
        **kwargs
    ):
        self.start_time = start_time
        self.duration = duration
        self.dt_atmos = dt_atmos
        
        # Default values for UFS parameters
        self.quilting = kwargs.get('quilting', True)
        self.quilting_restart = kwargs.get('quilting_restart', False)
        self.write_groups = kwargs.get('write_groups', 1)
        self.write_tasks_per_group = kwargs.get('write_tasks_per_group', 6)
        self.itasks = kwargs.get('itasks', 1)
        self.output_history = kwargs.get('output_history', True)
        self.history_file_on_native_grid = kwargs.get('history_file_on_native_grid', False)
        self.write_dopost = kwargs.get('write_dopost', False)
        self.write_nsflip = kwargs.get('write_nsflip', False)
        self.num_files = kwargs.get('num_files', 2)
        self.filename_base = kwargs.get('filename_base', 'atmmesh.')
        self.output_grid = kwargs.get('output_grid', 'cubed_sphere_grid')
        self.output_file = kwargs.get('output_file', 'netcdf')
        self.zstandard_level = kwargs.get('zstandard_level', 5)
        self.ideflate = kwargs.get('ideflate', 0)
        self.quantize_mode = kwargs.get('quantize_mode', 'quantize_bitround')
        self.quantize_nsd = kwargs.get('quantize_nsd', 0)
        self.ichunk2d = kwargs.get('ichunk2d', 0)
        self.jchunk2d = kwargs.get('jchunk2d', 0)
        self.ichunk3d = kwargs.get('ichunk3d', 0)
        self.jchunk3d = kwargs.get('jchunk3d', 0)
        self.kchunk3d = kwargs.get('kchunk3d', 0)
        self.imo = kwargs.get('imo', 384)
        self.jmo = kwargs.get('jmo', 190)
        self.output_fh = kwargs.get('output_fh', '12 -1')
        self.iau_offset = kwargs.get('iau_offset', 0)
        self.fhrot = kwargs.get('fhrot', 0)
        self.restart_interval = kwargs.get('restart_interval', 0)

        super().__init__(sequence)

    def __str__(self) -> str:
        duration_hours = round(self.duration / timedelta(hours=1))
        
        config = [
            f'start_year:              {self.start_time.year}',
            f'start_month:             {self.start_time.month}',
            f'start_day:               {self.start_time.day}',
            f'start_hour:              {self.start_time.hour:02d}',
            f'start_minute:            {self.start_time.minute}',
            f'start_second:            {self.start_time.second}',
            f'nhours_fcst:             {duration_hours}',
            f'fhrot:                   {self.fhrot}',
            f'dt_atmos:                {self.dt_atmos}',
            f'restart_interval:        {self.restart_interval}',
            f'quilting:                .{str(self.quilting).lower()}.',
            f'quilting_restart:        .{str(self.quilting_restart).lower()}.',
            f'write_groups:            {self.write_groups}',
            f'write_tasks_per_group:   {self.write_tasks_per_group}',
            f'itasks:                  {self.itasks}',
            f'output_history:          .{str(self.output_history).lower()}.',
            f'history_file_on_native_grid: .{str(self.history_file_on_native_grid).lower()}.',
            f'write_dopost:            .{str(self.write_dopost).lower()}.',
            f'write_nsflip:            .{str(self.write_nsflip).lower()}.',
            f'num_files:               {self.num_files}',
            f'filename_base:           {self.filename_base}',
            f"output_grid:             '{self.output_grid}'",
            f"output_file:             '{self.output_file}'",
            f'zstandard_level:         {self.zstandard_level}',
            f'ideflate:                {self.ideflate}',
            f"quantize_mode:           '{self.quantize_mode}'",
            f'quantize_nsd:            {self.quantize_nsd}',
            f'ichunk2d:                {self.ichunk2d}',
            f'jchunk2d:                {self.jchunk2d}',
            f'ichunk3d:                {self.ichunk3d}',
            f'jchunk3d:                {self.jchunk3d}',
            f'kchunk3d:                {self.kchunk3d}',
            f'imo:                     {self.imo}',
            f'jmo:                     {self.jmo}',
            f'output_fh:               {self.output_fh}',
            f'iau_offset:              {self.iau_offset}'
        ]
        
        return '\n'.join(config)

