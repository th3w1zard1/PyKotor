from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tools.language_translator import Translator
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


class PatcherModifications(ABC):

    def __init__(self, filename: str, destination: str | None = None, translator: Translator | None = None) -> None:
        self.filename: str = filename
        self.destination: str = destination or "Override"
        self.action: str = "Patch" + " "
        self.translator = translator

    @abstractmethod
    def apply(self, source: SOURCE_TYPES, memory: PatcherMemory, logger: PatchLogger, game: Game) -> bytes:
        ...
