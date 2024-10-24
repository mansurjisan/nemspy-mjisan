# configuration/earth.py

from enum import Enum
import logging
from textwrap import indent
from typing import Iterator, Tuple

from ..model.base import (
    AttributeEntry,
    EntryType,
    INDENTATION,
    ModelEntry,
)

class Earth(AttributeEntry):
    """
    multi-model coupling container representing the entire Earth system
    """
    entry_title = 'EARTH'

    def __init__(self, **models):
        if 'Verbosity' not in models:
            from ..model.base import VerbosityOption
            models['Verbosity'] = VerbosityOption.OFF

        self.__models = {model_type: None for model_type in EntryType}

        attributes = {}
        for key, value in models.items():
            if key.upper() in {entry.name for entry in EntryType}:
                if isinstance(value, ModelEntry):
                    self[EntryType[key.upper()]] = value
            else:
                attributes[key] = value
        self.attributes = attributes

    @property
    def models(self):
        """
        list of models comprising the Earth system
        """

        return self.__models

    def __getitem__(self, model_type: EntryType) -> ModelEntry:
        return self.__models[model_type]

    def __setitem__(self, model_type: EntryType, model: ModelEntry):
        assert model_type == model.entry_type
        if self.__models[model_type] is not None:
            LOGGER.warning(
                f'overwriting existing "{model_type.name}" model: ' f'{repr(self[model_type])}'
            )
        self.__models[model_type] = model

    def __contains__(self, model_type: EntryType):
        return model_type in self.__models

    def __iter__(self) -> Iterator[Tuple[EntryType, ModelEntry]]:
        for model_type, model in self.models.items():
            yield model_type, model

    def __str__(self) -> str:
        attributes = [
            f'{attribute} = {value if not isinstance(value, Enum) else value.value}'
            for attribute, value in self.attributes.items()
        ]

        return '\n'.join(
            [
                f'{self.entry_title}_component_list: '
                f'{" ".join(model_type.value for model_type, model in self.models.items() if model is not None)}',
                f'{self.entry_title}_attributes::',
                indent('\n'.join(attributes), INDENTATION),
                '::',
            ]
        )

    def __repr__(self) -> str:
        models = [
            f'{model_type.name}={repr(model)}' for model_type, model in self.models.items()
        ]
        models += [f'{key}={value}' for key, value in self.attributes.items()]
        return (
            f'{self.__class__.__name__}({self.attributes["Verbosity"]}, {", ".join(models)})'
        )
