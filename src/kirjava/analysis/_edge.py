#!/usr/bin/env python3

__all__ = (
    "FallthroughEdge",
    "JumpEdge",
    "JsrJumpEdge", "JsrFallthroughEdge",
    "RetEdge",
    "SwitchEdge",
    "ExceptionEdge",
)

import typing
from typing import Any, Union

from .. import types
from ..abc import Edge
from ..classfile import instructions
from ..types.reference import ClassOrInterfaceType

if typing.TYPE_CHECKING:
    from ._block import InsnBlock
    from ..classfile.instructions import (
        Instruction, JsrInstruction, LookupSwitchInstruction,
        RetInstruction, TableSwitchInstruction,
    )


class _DummyEdge(Edge):
    """
    Dummy edge, for internal use only.
    """

    ...


class FallthroughEdge(Edge):
    """
    A fallthrough edge between two blocks. This occurs when there are no jumps between blocks, so the flow just falls
    through to the next block.
    """

    def __init__(self, from_: "InsnBlock", to: "InsnBlock") -> None:
        super().__init__(from_, to)

    def __repr__(self) -> str:
        return "<FallthroughEdge(from=%r, to=%r) at %x>" % (self.from_, self.to, id(self))

    def __str__(self) -> str:
        return "fallthrough %s -> %s" % (self.from_, self.to)


class JumpEdge(Edge):
    """
    An edge that occurs when an explicit jump instruction is used. This can be conditional or not, note that conditional
    jumps must be matched with a fallthrough edge, this is only enforced when the graph is assembled however.
    """

    __slots__ = ("jump",)

    def __init__(self, from_: "InsnBlock", to: "InsnBlock", jump: Union["Instruction", None] = None) -> None:
        """
        :param jump: The jump instruction that caused this edge.
        """

        super().__init__(from_, to)

        self.jump = jump
        if jump is None:
            self.jump = instructions.goto()  # By default

    def __repr__(self) -> str:
        return "<JumpEdge(from=%r, to=%r, jump=%s) at %x>" % (self.from_, self.to, self.jump, id(self))

    def __str__(self) -> str:
        return "%s %s -> %s" % (self.jump, self.from_, self.to)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return (
            other.__class__ is self.__class__ and
            other.from_ == self.from_ and
            other.to == self.to and
            other.jump == self.jump
        )

    def __hash__(self) -> int:
        return hash((self.from_, self.to, self.jump.opcode))


class JsrJumpEdge(JumpEdge):
    """
    A handle for a jsr instruction jump edge.
    """

    __slots__ = ("return_",)

    def __init__(self, from_: "InsnBlock", to: "InsnBlock", jump: "JsrInstruction") -> None:
        super().__init__(from_, to, jump)

    def __repr__(self) -> str:
        return "<JsrJumpEdge(from=%r, to=%r, jump=%s) at %x>" % (self.from_, self.to, self.jump, id(self))

    def __str__(self) -> str:
        return "%s %s -> %s" % (self.jump, self.from_, self.to)


class JsrFallthroughEdge(JumpEdge):
    """
    A handle for a jsr instruction fallthrough edge.
    """

    def __init__(self, from_: "InsnBlock", to: "InsnBlock", jump: "JsrInstruction") -> None:
        super().__init__(from_, to, jump)

    def __repr__(self) -> str:
        return "<JsrFallthroughEdge(from=%r, to=%r, jump=%s) at %x>" % (self.from_, self.to, self.jump, id(self))

    def __str__(self) -> str:
        return "fallthrough %s %s (-> %s)" % (self.jump, self.from_, self.to)


class RetEdge(JumpEdge):
    """
    A handle for a non-inlined ret instruction jump edge.
    """

    def __init__(self, from_: "InsnBlock", to: Union["InsnBlock", None], jump: "RetInstruction") -> None:
        super().__init__(from_, to, jump)

    def __repr__(self) -> str:
        return "<RetEdge(from=%r, to=%r, jump=%s) at %x>" % (self.from_, self.to, self.jump, id(self))

    def __str__(self) -> str:
        if self.to is not None:
            return "%s %s -> %s" % (self.jump, self.from_, self.to)
        return "%s %s -> unknown" % (self.jump, self.from_)


class SwitchEdge(JumpEdge):
    """
    An edge created by a switch instruction. Contains the instruction and the index.
    """

    __slots__ = ("value",)

    def __init__(
            self,
            from_: "InsnBlock",
            to: "InsnBlock",
            jump: Union["LookupSwitchInstruction", "TableSwitchInstruction"],
            value: Union[int, None],
    ) -> None:
        """
        :param jump: The switch instruction that created this edge.
        :param value: The value (or index) in the switch instruction that created this edge, None for the default.
        """

        super().__init__(from_, to, jump)

        self.value = value

    def __repr__(self) -> str:
        return "<SwitchEdge(from=%r, to=%r, jump=%s, value=%s) at %x>" % (
            self.from_, self.to, self.jump, self.value, id(self),
        )

    def __str__(self) -> str:
        if self.value is not None:
            return "switch %s value %i %s -> %s" % (self.jump, self.value, self.from_, self.to)
        return "switch %s default %s -> %s" % (self.jump, self.from_, self.to)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return (
            other.__class__ is SwitchEdge and
            other.from_ == self.from_ and
            other.to == self.to and
            other.value == self.value
        )

    def __hash__(self) -> int:
        return hash((self.from_, self.to, self.value))


class ExceptionEdge(Edge):
    """
    An edge between a block and its exception handler.
    """

    __slots__ = ("priority", "throwable", "inline_coverage")

    def __init__(
            self,
            from_: "InsnBlock",
            to: "InsnBlock",
            priority: int,
            throwable: Union[ClassOrInterfaceType, None] = None,
            inline_coverage: bool = False,
    ) -> None:
        """
        :param priority: The priority of this exception handler, lower values mean higher priority.
        :param throwable: The exception that this handler is catching, if None, it defaults to java/lang/Throwable.
        """

        super().__init__(from_, to)

        if throwable is None:
            throwable = types.throwable_t

        self.priority = priority
        self.throwable = throwable
        self.inline_coverage = inline_coverage

    def __repr__(self) -> str:
        return "<ExceptionEdge(from=%r, to=%r, priority=%i, throwable=%s, inline_coverage=%s) at %x>" % (
            self.from_, self.to, self.priority, self.throwable, self.inline_coverage, id(self),
        )

    def __str__(self) -> str:
        if self.inline_coverage:
            return "catch %s priority %i %s (+inlined) -> %s" % (self.throwable, self.priority, self.from_, self.to)
        return "catch %s priority %i %s -> %s" % (self.throwable, self.priority, self.from_, self.to)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return (
            other.__class__ is ExceptionEdge and
            other.from_ == self.from_ and
            other.to == self.to and
            other.priority == self.priority and
            other.throwable == self.throwable
        )

    def __hash__(self) -> int:
        return hash((self.from_, self.to, self.priority, self.throwable))
