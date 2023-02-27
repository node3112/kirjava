# cython: langauge=c
# cython: language_level=3

__all__ = (
    "Method",
)

"""
Java method abstraction.
"""

from typing import Iterable, Tuple

from .class_ cimport Class
from ..types import BaseType


cdef class Method:
    """
    An abstract representation of a Java method.
    """

    # ------------------------------ Access flags ------------------------------ #

    property is_public:
        """
        Is this method public?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_private:
        """
        Is this method private?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_protected:
        """
        Is this method protected?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_static:
        """
        Is this method static?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_final:
        """
        Is this method final (cannot be overriden)?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_synchronized:
        """
        Is access to this method synchronized?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_bridge:
        """
        Is this method generated by the compiler?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_varargs:
        """
        Does this method have a variable number of arguments?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_native:
        """
        Does this method reference a function defined in a native binary?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_abstract:
        """
        Does this method have a provided implementation?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_strict:
        """
        Does this method use FP-strict floating point mode?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_synthetic:
        """
        Is this method synthetic (generated by the compiler)?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    # ------------------------------ Other properties ------------------------------ #

    property name:
        """
        The name of this method.
        """

        def __get__(self) -> str:
            ...

        def __set__(self, value: str) -> None:
            ...

    property argument_types:
        """
        The argument types of this method.
        """

        def __get__(self) -> Tuple[BaseType, ...]:
            ...

        def __set__(self, value: Iterable[BaseType, ...]) -> None:
            ...

    property return_type:
        """
        The return type of this method.
        """

        def __get__(self) -> BaseType:
            ...

        def __set__(self, value: BaseType) -> None:
            ...

    def __init__(self, class_: Class) -> None:
        """
        :param class_: The class that this method belongs to.
        """

        self.class_ = class_

    def get_reference(self) -> Tuple[Class, str, Tuple[BaseType, ...], BaseType]:
        """
        :return: A reference to this method that can be used in instructions.
        """

        return self.class_, self.name, self.argument_types, self.return_type

    def get_ref(self) -> Tuple[Class, str, Tuple[BaseType, ...], BaseType]:
        """
        :return: A reference to this method that can be used in instructions.
        """

        return self.class_, self.name, self.argument_types, self.return_type
