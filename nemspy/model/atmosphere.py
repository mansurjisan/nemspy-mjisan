from os import PathLike

from .base import EntryType, FileForcingEntry, ModelEntry


class AtmosphericModelEntry(ModelEntry):
    """
    abstract implementation of a generic atmospheric model
    """

    entry_type = EntryType.ATMOSPHERIC

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class AtmosphericForcingEntry(AtmosphericModelEntry, FileForcingEntry):
    """
    Atmospheric Mesh (ATMesh) reference
    """

    name = 'atmesh'

    def __init__(self, filename: PathLike = None, processors: int = None, **kwargs):
        if processors is None:
            processors = 1
        AtmosphericModelEntry.__init__(self, processors, **kwargs)
        FileForcingEntry.__init__(self, self.entry_type, filename)


class HWRFEntry(AtmosphericModelEntry):
    """
    Hurricane Weather Research and Forecasting (HWRF) model
    https://en.wikipedia.org/wiki/Hurricane_Weather_Research_and_Forecasting_Model
    """

    name = 'hwrf'

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)
