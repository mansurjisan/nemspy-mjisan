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
        runseq = ["# Run Sequence #", "runSeq::", "@3600"]
        
        has_mediator = any(model.entry_type == EntryType.MEDIATOR for model in self.sequence.models)
        
        if has_mediator:
            # Mediator prep phases
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
            
            # Mediator to model connections
            for comp in components:
                runseq.append(f"  MED -> {comp} :remapMethod=redist")
            
        # Model executions
        for comp in components:
            runseq.append(f"  {comp}")
            
        if has_mediator:
            # Model to mediator connections
            for comp in components:
                runseq.append(f"  {comp} -> MED :remapMethod=redist")
                
            # Mediator post phases
            for comp in components:
                runseq.append(f"  MED med_phases_post_{comp.lower()}")
                
            runseq.extend([
                "  MED med_phases_history_write",
                "  MED med_phases_restart_write"
            ])
            
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
            "####  NEMS Run-Time Configuration File  #####",
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
