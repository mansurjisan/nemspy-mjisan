from os import PathLike

from .base import EntryType, FileForcingEntry, ModelEntry


class IceModelEntry(ModelEntry):
    """
    abstract implementation of a generic ice model
    """

    entry_type = EntryType.ICE

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class IceForcingEntry(IceModelEntry, FileForcingEntry):
    """
    Ice model mesh reference
    """

    name = 'icemesh'

    def __init__(self, filename: PathLike = None, processors: int = None, **kwargs):
        if processors is None:
            processors = 1
        # Uses ww3data as name but the implementation is model agnostic
        IceModelEntry.__init__(self, processors, **kwargs)
        FileForcingEntry.__init__(self, self.model_type, filename)
