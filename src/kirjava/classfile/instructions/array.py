#!/usr/bin/env python3

"""
Instructions related to arrays.
"""

from abc import ABC
from typing import List, Union

from . import Instruction
from ... import types
from ...abc import Error, TypeChecker
from ...analysis.trace import BlockInstruction, State
from ...types import BaseType
from ...types.reference import ArrayType


class ArrayLoadInstruction(Instruction, ABC):
    """
    Loads a value from an array.
    """

    throws = (
        types.arrayindexoutofboundsexception_t,
        types.nullpointerexception_t,
    )

    type_: Union[BaseType, None] = ...

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        index_entry, array_entry = state.pop(source, 2)

        # Check initial types (array and int)
        if not checker.check_array(array_entry.type):
            errors.append(Error(source, "expected array type, got %s" % array_entry.type))
        if not checker.check_merge(types.int_t, index_entry.type):
            errors.append(Error(source, "expected type int, got %s" % index_entry.type))

        # Create type from array, taking into account if it's multi-dimensional
        if isinstance(array_entry.type, ArrayType):
            if array_entry.type.dimension > 1:
                type_ = ArrayType(array_entry.type.element_type, array_entry.type.dimension - 1)
            else:
                type_ = array_entry.type.element_type.to_verification_type()
        else:
            type_ = array_entry.type  # Best we can do I guess

        if self.type_ is not None:
            type__ = self.type_.to_verification_type()
            if not checker.check_merge(type__, type_):
                errors.append(Error(source, "expected type %s, got %s" % (type__, type_)))
            state.push(source, checker.merge(type__, type_), parents=(index_entry, array_entry))

        else:
            if not checker.check_reference(type_):
                errors.append(Error(source, "expected reference type, got %s" % type_))
            state.push(source, type_, parents=(index_entry, array_entry))  # Best we can do :(


class ArrayStoreInstruction(Instruction, ABC):
    """
    Stores a value in an array.
    """

    throws = (
        types.arrayindexoutofboundsexception_t,
        types.arraystoreexception_t,
        types.nullpointerexception_t,
    )

    type_: Union[BaseType, None] = ...

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        # Check the array type matches what the instruction expects
        if self.type_ is not None:
            type_ = self.type_.to_verification_type()
            entry, *_ = state.pop(source, type_.internal_size, tuple_=True)
            if not checker.check_merge(type_, entry.type):
                errors.append(Error(source, "expected type %s, got %s" % (type_, entry.type)))
        else:
            entry = state.pop(source)
            if not checker.check_reference(entry.type):
                errors.append(Error(source, "expected reference type, got %s" % entry.type))

        index_entry, array_entry = state.pop(source, 2)

        # Check the array and index types are valid
        if not checker.check_array(array_entry.type):
            errors.append(Error(source, "expected array type, got %s" % array_entry.type))
        if not checker.check_merge(types.int_t, index_entry.type):
            errors.append(Error(source, "expected type int, got %s" % index_entry.type))

        if isinstance(array_entry.type, ArrayType):
            if array_entry.type.dimension > 1:
                type_ = ArrayType(array_entry.type.element_type, array_entry.type.dimension - 1)
            else:
                type_ = array_entry.type.element_type.to_verification_type()
        else:
            type_ = array_entry.type

        # Check the value can merge with the array that we popped
        if not checker.check_merge(type_, entry.type):
            errors.append(Error(source, "expected type %s, got %s" % (type_, entry.type)))


class ArrayLengthInstruction(Instruction, ABC):
    """
    Gets the length of an array.
    """

    throws = (types.nullpointerexception_t,)

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        if not checker.check_array(entry.type):
            errors.append(Error(source, "expected array type, got %s" % entry.type))
        state.push(source, types.int_t, parents=(entry,))
