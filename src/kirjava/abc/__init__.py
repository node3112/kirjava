#!/usr/bin/env python3

__all__ = (
    "Source", 
    "Constant",
    "Class", "Field", "Method",
    "Block", "Edge", "Graph", "RethrowBlock", "ReturnBlock",
    "Error", "TypeChecker", "Verifier", "VerifyError",
)

"""
Abstract base classes for different concepts used throughout Kirjava.
"""

import typing
from abc import abstractmethod, ABC
from typing import Any

if typing.TYPE_CHECKING:
    from ..types import BaseType


class Source(ABC):
    """
    The source of a particular value (deliberately quite generic), for storing debug information mainly.
    """

    ...


class Constant(ABC):
    """
    A Java constant (some piece of information that is constant).
    """

    def __init__(self, value: Any) -> None:
        self.value = value

    def __repr__(self) -> str:
        return "<%s(%r) at %x>" % (self.__class__.__name__, self.value, id(self))

    def __str__(self) -> str:
        return repr(self.value)

    def __eq__(self, other: Any) -> bool:
        return other.__class__ is self.__class__ and other.value == self.value  # or other == self.value

    def __hash__(self) -> int:
        return hash(self.value)

    @abstractmethod
    def get_type(self) -> "BaseType":
        """
        :return: The type of this constant, if applicable.
        """

        ...


from .class_ import *
from .field import *
from .graph import *
from .method import *
from .verifier import *
