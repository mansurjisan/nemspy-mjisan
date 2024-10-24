# sequence.py
from datetime import timedelta
import logging
from textwrap import indent
from typing import Dict, List, Union, Iterator  # Add all needed types

from ..model.base import (
    AttributeEntry,
    ConnectionEntry,
    EntryType,
    GridRemapMethod,
    INDENTATION,
    MediationEntry,
    MediatorEntry,
    ModelEntry,
    SequenceEntry,
    VerbosityOption,
)

from .earth import Earth  # Make sure this is here


class RunSequence(AttributeEntry, SequenceEntry):
    """
    multi-model container for model entries
    """
    entry_title = 'Run Sequence'

    def __init__(self, interval: timedelta, **kwargs):
        self.interval = interval

        if 'Verbosity' not in kwargs:
            kwargs['Verbosity'] = VerbosityOption.OFF

        # ... Rest of the RunSequence class implementation from your original configuration.py ...
        self.__models = {}
        attributes = {}
        for key, value in kwargs.items():
            model_types = [model_type.value for model_type in EntryType]
            if key.upper() in model_types and isinstance(value, ModelEntry):
                self.__models[EntryType(key.upper())] = value
            else:
                attributes[key] = value
        self.attributes = attributes

        self.__sequence = [
            model for model in self.models if model.entry_type != EntryType.MEDIATOR
        ]
        self.__link_models()

    def append(self, entry: SequenceEntry):
        """
        add a sequence entry
        """

        if isinstance(entry, ModelEntry):
            model_type = entry.entry_type
            if model_type in self.__models:
                del self.__models[model_type]
                self[entry.entry_type] = entry
        self.__sequence.append(entry)

    def extend(self, sequence: List[SequenceEntry]):
        """
        add several sequence entries
        """

        for entry in sequence:
            self.append(entry)

    @property
    def sequence(self) -> List[SequenceEntry]:
        """
        list of sequence entries in order, including model entries and connections / mediations
        """

        return self.__sequence

    @sequence.setter
    def sequence(self, sequence: List[SequenceEntry]):
        """
        set the sequence by passing a list of entries in order
        """

        sequence = list(sequence)
        if sequence != self.__sequence:
            mediator = self.mediator
            self.__models = {}
            if mediator is not None:
                self.mediator = mediator
            for entry in sequence:
                if isinstance(entry, ModelEntry):
                    model_type = entry.entry_type
                    if model_type in self.__models:
                        raise TypeError(
                            f'duplicate model type ' f'"{model_type.name}" in given sequence'
                        )
                    self.__models[model_type] = entry
            self.__link_models()
            self.__sequence = sequence

    def connect(
        self, source: EntryType, target: EntryType, method: GridRemapMethod = None, **kwargs,
    ):
        """
        assign a simple connection (not a mediation) between two model entries within the sequence
        """

        if method is None:
            method = GridRemapMethod.REDISTRIBUTE
        if EntryType.MEDIATOR in [source, target] and self.mediator is None:
            self.mediator = MediatorEntry(**kwargs)
        if source not in self.__models:
            raise KeyError(f'no {source.name} model in sequence')
        if target not in self.__models:
            raise KeyError(f'no {target.name} model in sequence')
        self.append(ConnectionEntry(self[source], self[target], method))

    @property
    def connections(self) -> List[Union[ConnectionEntry, MediationEntry]]:
        """
        list of all connections in the sequence
        """

        return [
            entry
            for entry in self.sequence
            if isinstance(entry, ConnectionEntry) or isinstance(entry, MediationEntry)
        ]

    @property
    def mediator(self) -> MediatorEntry:
        """
        shortcut property to the mediator entry
        """

        if EntryType.MEDIATOR in self:
            return self.__models[EntryType.MEDIATOR]
        else:
            return None

    @mediator.setter
    def mediator(self, mediator: MediatorEntry):
        """
        set the mediator entry (does not exist in the sequence by itself)
        """

        self[EntryType.MEDIATOR] = mediator

    def mediate(
        self,
        sources: List[EntryType] = None,
        functions: List[str] = None,
        targets: List[EntryType] = None,
        method: GridRemapMethod = None,
        processors: int = None,
        **attributes,
    ):
        """
        assign a mediation between two entries in the sequence
        """

        if 'name' not in attributes:
            attributes['name'] = 'mediator'
        if self.mediator is None:
            self.mediator = MediatorEntry(processors=processors, **attributes)
        else:
            self.mediator.attributes.update(attributes)
        if processors is not None:
            # increase mediation processor assignment if required
            if self.mediator.processors < processors:
                self.mediator.processors = processors

        if sources is not None:
            sources = [self[source] for source in sources]
        if targets is not None:
            targets = [self[target] for target in targets]

        self.append(MediationEntry(self.mediator, sources, functions, targets, method))

    @property
    def mediations(self) -> List[MediationEntry]:
        """
        list of all mediations in the sequence
        """

        return [entry for entry in self.sequence if isinstance(entry, MediationEntry)]

    @property
    def earth(self) -> Earth:
        """
        Earth system assigned to the sequence
        """

        return Earth(
            **{model.entry_type.name: model for model in self.models}, **self.attributes
        )

    @property
    def processors(self) -> int:
        """
        total number of processors assigned to sequence entries
        """

        return sum(model.processors for model in self.__models.values())

    def __link_models(self):
        """
        link entries and assign processors
        """

        models = self.models
        for model in models:
            if model.previous is not None:
                model.previous.next = None
            if model.next is not None:
                model.next = None
            model.start_processor = 0
        for model_index, model in enumerate(models):
            previous_model_index = model_index - 1
            if previous_model_index >= 0:
                model.previous = models[previous_model_index]

    def __setitem__(self, model_type: EntryType, model: ModelEntry):
        assert model_type == model.entry_type
        if model_type in self.__models:
            existing_model = self.__models[model_type]
            logging.debug(
                f'overwriting {model_type.name} model ' f'"{existing_model}" with "{model}"'
            )
            self.__sequence.remove(self.__sequence.index(existing_model))
        self.__models[model_type] = model
        self.__link_models()

    def __getitem__(self, model_type: EntryType) -> ModelEntry:
        return self.__models[model_type]

    @property
    def models(self) -> List[ModelEntry]:
        """
        list of models in the run sequence
        """

        models = [
            model
            for model_type, model in self.__models.items()
            if model_type in self and model_type is not EntryType.MEDIATOR
        ]
        if self.mediator is not None:
            models.insert(0, self.mediator)
        return models

    def __iter__(self) -> Iterator[ModelEntry]:
        for model in self.models:
            yield model

    def __contains__(self, model_type: EntryType) -> bool:
        return model_type in self.__models

    def __len__(self) -> int:
        return len(self.sequence)

    @property
    def sequence_entry(self) -> str:
        return str(self)

    def __str__(self) -> str:
        block = '\n'.join(
            [
                f'@{self.interval / timedelta(seconds=1):.0f}',
                indent(
                    '\n'.join(entry.sequence_entry for entry in self.__sequence), INDENTATION
                ),
                '@',
            ]
        )
        return '\n'.join([f'runSeq::', indent(block, INDENTATION), '::'])

    def __repr__(self) -> str:
        models = [f'{model.entry_type.name.lower()}={repr(model)}' for model in self.models]
        return f'{self.__class__.__name__}({repr(self.interval)}, {", ".join(models)})'
