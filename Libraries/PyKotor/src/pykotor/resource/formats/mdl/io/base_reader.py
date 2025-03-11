"""Base interface for MDL file readers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from pykotor.resource.formats.mdl.data.model import MDL

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


class MDLReader(ABC):
    """Abstract base class for MDL file readers.

    This defines the interface that both binary and ASCII MDL readers must implement.
    """

    def __init__(self, mdl_reader: BinaryReader, mdx_reader: BinaryReader):
        """Initialize the reader.

        Args:
            mdl_reader: The reader to use for reading the MDL file
            mdx_reader: The reader to use for reading the MDX file
        """
        self._mdl_reader = mdl_reader
        self._mdx_reader = mdx_reader
        self._mdl = MDL()
        self._names: List[str] = []
        self._node_by_number: dict[int, MDLNode] = {}

    @abstractmethod
    def read(self) -> MDL:
        """Read the MDL file and return the model.

        Returns:
            MDL: The loaded model
        """
        pass

    @abstractmethod
    def _load_names(self, offset: int, count: int) -> None:
        """Load the names list from the file.

        Args:
            offset: Offset to names data
            count: Number of names to load
        """
        pass

    @abstractmethod
    def _peek_nodes(self, offset: int, count: int) -> None:
        """Pre-scan nodes to build node lookup table.

        Args:
            offset: Offset to nodes data
            count: Number of nodes to scan
        """
        pass

    @abstractmethod
    def _load_nodes(self, offset: int, count: int) -> None:
        """Load all nodes from the file.

        Args:
            offset: Offset to nodes data
            count: Number of nodes to load
        """
        pass

    @abstractmethod
    def _load_animations(self, offset: int, count: int) -> None:
        """Load all animations from the file.

        Args:
            offset: Offset to animations data
            count: Number of animations to load
        """
        pass

    @property
    def model(self) -> MDL:
        """Get the loaded model.

        Returns:
            MDL: The loaded model
        """
        return self._mdl
