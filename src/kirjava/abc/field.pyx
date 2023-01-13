# cython: language=c
# cython: language_level=3

__all__ = (
    "Field",
)

"""
Java field abstraction.
"""

from typing import Tuple

from .class_ cimport Class
from ..types import BaseType


cdef class Field:
    """
    An abstract representation of a Java field.
    """

    # ------------------------------ Access flags ------------------------------ #

    property is_public:
        """
        Is this field public?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_private:
        """
        Is this field private?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_protected:
        """
        Is this field protected?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_static:
        """
        Is this field static?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_final:
        """
        Is this field final (cannot be re-assigned)?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_volatile:
        """
        Is this field volatile (can't be cached)?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_transient:
        """
        Is this field transient?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_synthetic:
        """
        Is this field synthetic (generated by the compiler)?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    property is_enum:
        """
        Is this field an element of an enum class?
        """

        def __get__(self) -> bool:
            ...

        def __set__(self, value: bool) -> None:
            ...

    # ------------------------------ Other properties ------------------------------ #

    property name:
        """
        The name of this field.
        """

        def __get__(self) -> str:
            ...

        def __set__(self, value: str) -> None:
            ...

    property type:
        """
        The type of this field.
        """

        def __get__(self) -> BaseType:
            ...

        def __set__(self, value: BaseType) -> None:
            ...

    cdef readonly Class class_

    def __init__(self, class_: Class) -> None:
        """
        :param class_: The class that this field belongs to.
        """

        self.class_ = class_

    def get_reference(self) -> Tuple[Class, str, BaseType]:
        """
        :return: A reference to this field that can be used in instructions.
        """

        return self.class_, self.name, self.type

    def get_ref(self) -> Tuple[Class, str, BaseType]:
        """
        :return: A reference to this field that can be used in instructions.
        """

        return self.class_, self.name, self.type