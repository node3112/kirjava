#!/usr/bin/env python3

__all__ = (
    "StackMapTable", "LineNumberTable", "LocalVariableTable", "LocalVariableTypeTable",
)

"""
Attributes found exclusively in the Code attribute.
"""

import logging
import struct
import typing
from abc import abstractmethod, ABC
from typing import IO, List, Tuple, Union

from . import AttributeInfo
from .. import descriptor, ClassFile
from ..constants import Class
from ... import types
from ...types.verification import VerificationType, Uninitialized
from ...types.reference import ArrayType, ClassOrInterfaceType
from ...version import Version

if typing.TYPE_CHECKING:
    from .method import Code

logger = logging.getLogger("kirjava.classfile.attributes.code")


class StackMapTable(AttributeInfo):
    """
    Contains information about stack frames, used for inference verification.
    """

    __slots__ = ("frames",)

    name_ = "StackMapTable"
    since = Version(50, 0)
    locations = ("Code",)

    @classmethod
    def _read_verification_type(cls, class_file: ClassFile, buffer: IO[bytes]) -> VerificationType:
        """
        Reads a verification type info from a buffer.
        """

        tag = buffer.read(1)[0]
        if tag == 0:
            return types.top_t
        elif tag == 1:
            return types.int_t
        elif tag == 2:
            return types.float_t
        elif tag == 3:
            return types.double_t
        elif tag == 4:
            return types.long_t
        elif tag == 5:
            return types.null_t
        elif tag == 6:
            return types.uninit_this_t
        elif tag == 7:
            class_index, = struct.unpack(">H", buffer.read(2))
            return class_file.constant_pool[class_index].get_actual_type()
        elif tag == 8:
            offset, = struct.unpack(">H", buffer.read(2))
            return Uninitialized(offset)

        raise ValueError("Invalid tag %i for verification type." % tag)

    @classmethod
    def _write_verification_type(cls, type_: VerificationType, class_file: ClassFile, buffer: IO[bytes]) -> None:
        """
        Writes a verification type to a buffer.
        """

        if type_ == types.top_t:
            buffer.write(bytes((0,)))
        elif type_ == types.int_t:
            buffer.write(bytes((1,)))
        elif type_ == types.float_t:
            buffer.write(bytes((2,)))
        elif type_ == types.double_t:
            buffer.write(bytes((3,)))
        elif type_ == types.long_t:
            buffer.write(bytes((4,)))
        elif type_ == types.null_t:
            buffer.write(bytes((5,)))
        elif type_ == types.uninit_this_t:
            buffer.write(bytes((6,)))
        elif type_ == types.this_t:
            buffer.write(bytes((7,)))
            buffer.write(struct.pack(">H", class_file.constant_pool.add(Class(type_.class_.name))))
        elif isinstance(type_, ClassOrInterfaceType):
            buffer.write(bytes((7,)))
            buffer.write(struct.pack(">H", class_file.constant_pool.add(Class(type_.name))))
        elif isinstance(type_, ArrayType):
            buffer.write(bytes((7,)))
            buffer.write(struct.pack(">H", class_file.constant_pool.add(Class(descriptor.to_descriptor(type_)))))
        elif isinstance(type_, Uninitialized):
            buffer.write(bytes((8,)))
            buffer.write(struct.pack(">H", type_.offset))
        else:
            raise TypeError("Invalid verification type %r." % type_)

    def __init__(self, parent: "Code") -> None:
        super().__init__(parent, StackMapTable.name_)

        self.frames: List[StackMapTable.StackMapFrame] = []

    def __repr__(self) -> str:
        return "<StackMapTable(%r) at %x>" % (self.frames, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        self.frames.clear()
        frames_count, = struct.unpack(">H", buffer.read(2))
        for index in range(frames_count):
            frame_type, = buffer.read(1)
            for stack_frame in self.STACK_MAP_FRAMES:
                if frame_type in stack_frame.frame_type:
                    self.frames.append(stack_frame.read(frame_type, class_file, buffer))
                    break
            else:
                ...  # TODO: Raise exception / log

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", len(self.frames)))
        for stack_frame in self.frames:
            stack_frame.write(class_file, buffer)

    # ------------------------------ Stack frame types ------------------------------ #

    class StackMapFrame(ABC):
        """
        A stack map frame info structure.
        """

        __slots__ = ("offset_delta",)

        frame_type = range(-1, -1)

        @classmethod
        @abstractmethod
        def read(cls, frame_type: int, class_file: ClassFile, buffer: IO[bytes]) -> "StackMapTable.StackMapFrame":
            """
            Reads a stack map frame from a buffer.

            :param frame_type: The frame type that has already been read.
            :param class_file: The classfile that the frame belongs to.
            :param buffer: The binary buffer to read from.
            :return: The stack map frame that was read.
            """

            ...

        def __init__(self, offset_delta: int) -> None:
            """
            :param offset_delta: The starting bytecode offset for this frame, as a delta from the previous frame.
            """

            self.offset_delta = offset_delta

        def __repr__(self) -> str:
            return "<%s(offset_delta=%i) at %x>" % (self.__class__.__name__, self.offset_delta, id(self))

        @abstractmethod
        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            """
            Writes this stack map frame to a buffer.

            :param class_file: The classfile that this stack map frame belongs to.
            :param buffer: The binary buffer to write to.
            """

            ...

    class SameFrame(StackMapFrame):
        """
        Indicates that this frame has the exact same locals as the previous frame and that the operand stack is empty.
        """

        frame_type = range(0, 64)

        @classmethod
        def read(cls, frame_type: int, class_file: ClassFile, buffer: IO[bytes]) -> "StackMapTable.SameFrame":
            return cls(frame_type)

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            buffer.write(bytes((self.offset_delta,)))

    class SameLocals1StackItemFrame(StackMapFrame):
        """
        Indicates that this frame has the exact same locals as the previous frame and that the operand stack has one entry.
        """

        __slots__ = ("stack_item",)

        frame_type = range(64, 128)

        @classmethod
        def read(
                cls, frame_type: int, class_file: ClassFile, buffer: IO[bytes],
        ) -> "StackMapTable.SameLocals1StackItemFrame":
            stack_item = StackMapTable._read_verification_type(class_file, buffer)
            return cls(frame_type - 64, stack_item)

        def __init__(self, offset_delta: int, stack_item: VerificationType) -> None:
            """
            :param stack_item: The extra stack item.
            """

            super().__init__(offset_delta)

            self.stack_item = stack_item

        def __repr__(self) -> str:
            return "<SameLocals1StackItemFrame(offset_delta=%i, stack_item=%s) at %x>" % (
                self.offset_delta, self.stack_item, id(self),
            )

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            buffer.write(bytes((self.offset_delta + 64,)))
            StackMapTable._write_verification_type(self.stack_item, class_file, buffer)

    class SameLocals1StackItemFrameExtended(StackMapFrame):  # Uh, yeah lmao
        """
        Indicates that this frame has the exact same locals as the previous frame and that the operand stack has one entry.
        The delta offset is given explicitly, however.
        """

        __slots__ = ("stack_item",)

        frame_type = range(247, 248)

        @classmethod
        def read(
                cls, frame_type: int, class_file: ClassFile, buffer: IO[bytes],
        ) -> "StackMapTable.SameLocals1StackItemFrameExtended":
            offset_delta, = struct.unpack(">H", buffer.read(2))
            stack_item = StackMapTable._read_verification_type(class_file, buffer)
            return cls(offset_delta, stack_item)

        def __init__(self, offset_delta: int, stack_item: VerificationType) -> None:
            """
            :param stack_item: The extra stack item.
            """

            super().__init__(offset_delta)
            
            self.stack_item = stack_item

        def __repr__(self) -> str:
            return "<SameLocals1StackItemFrameExtended(offset_delta=%i, stack_item=%s) at %x>" % (
                self.offset_delta, self.stack_item, id(self),
            )

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            buffer.write(bytes((247,)))
            buffer.write(struct.pack(">H", self.offset_delta))
            StackMapTable._write_verification_type(self.stack_item, class_file, buffer)

    class ChopFrame(StackMapFrame):
        """
        Indicates that the frame has the same locals as the previous frame except that the last <k> locals are absent and
        that the operand stack is empty.
        """

        __slots__ = ("chopped",)

        frame_type = range(248, 251)

        @classmethod
        def read(cls, frame_type: int, class_file: ClassFile, buffer: IO[bytes]) -> "StackMapTable.ChopFrame":
            offset_delta, = struct.unpack(">H", buffer.read(2))
            return cls(offset_delta, 251 - frame_type)

        def __init__(self, offset_delta: int, chopped: int) -> None:
            """
            :param chopped: The number of locals that were chopped.
            """

            super().__init__(offset_delta)

            self.chopped = chopped

        def __repr__(self) -> str:
            return "<ChopFrame(offset_delta=%i, chopped=%i) at %x>" % (self.offset_delta, self.chopped, id(self))

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            buffer.write(bytes((251 - self.chopped,)))
            buffer.write(struct.pack(">H", self.offset_delta))

    class SameFrameExtended(StackMapFrame):
        """
        Indicates that the frame has the exact same locals as the previous frame and that the operand stack is empty. The
        delta offset is explicitly given.
        """

        frame_type = range(251, 252)

        @classmethod
        def read(cls, frame_type: int, class_file: ClassFile, buffer: IO[bytes]) -> "StackMapTable.SameFrameExtended":
            offset_delta, = struct.unpack(">H", buffer.read(2))
            return cls(offset_delta)

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            buffer.write(bytes((251,)))
            buffer.write(struct.pack(">H", self.offset_delta))

    class AppendFrame(StackMapFrame):
        """
        Indicates that the frame has the exact same locals as the previous frame except that <k> additional locals are
        defined and that the operand stack is empty.
        """

        __slots__ = ("locals",)

        frame_type = range(252, 255)

        @classmethod
        def read(cls, frame_type: int, class_file: ClassFile, buffer: IO[bytes]) -> "StackMapTable.AppendFrame":
            offset_delta, = struct.unpack(">H", buffer.read(2))
            locals_ = tuple([
                StackMapTable._read_verification_type(class_file, buffer) for index in range(frame_type - 251)
            ])
            return cls(offset_delta, locals_)

        def __init__(self, offset_delta: int, locals_: Tuple[VerificationType, ...]) -> None:
            """
            :param locals_: The locals to append.
            """

            super().__init__(offset_delta)

            self.locals = locals_

        def __repr__(self) -> str:
            return "<AppendFrame(offset_delta=%i, locals=[%s]) at %x>" % (
                self.offset_delta, ", ".join(map(str, self.locals)), id(self),
            )

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            buffer.write(bytes((251 + len(self.locals),)))
            buffer.write(struct.pack(">H", self.offset_delta))
            for local in self.locals:
                StackMapTable._write_verification_type(local, class_file, buffer)

    class FullFrame(StackMapFrame):
        """
        A full stack frame.
        """

        __slots__ = ("locals", "stack")

        frame_type = range(255, 256)

        @classmethod
        def read(cls, frame_type: int, class_file: ClassFile, buffer: IO[bytes]) -> "StackMapTable.FullFrame":
            offset_delta, = struct.unpack(">H", buffer.read(2))
            locals_ = tuple([
                StackMapTable._read_verification_type(class_file, buffer)
                for index in range(struct.unpack(">H", buffer.read(2))[0])
            ])
            stack = tuple([
                StackMapTable._read_verification_type(class_file, buffer)
                for index in range(struct.unpack(">H", buffer.read(2))[0])
            ])

            return cls(offset_delta, locals_, stack)

        def __init__(
                self, offset_delta: int, locals_: Tuple[VerificationType, ...], stack: Tuple[VerificationType, ...],
        ) -> None:
            """
            :param locals_: The locals in this frame.
            :param stack: The stack in this frame.
            """

            super().__init__(offset_delta)

            self.locals = locals_
            self.stack = stack

        def __repr__(self) -> str:
            return "<FullFrame(offset_delta=%i, locals=[%s], stack=[%s]) at %x>" % (
                self.offset_delta, ", ".join(map(str, self.locals)), ", ".join(map(str, self.stack)), id(self),
            )

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            buffer.write(bytes((255,)))
            buffer.write(struct.pack(">H", self.offset_delta))

            buffer.write(struct.pack(">H", len(self.locals)))
            for local in self.locals:
                StackMapTable._write_verification_type(local, class_file, buffer)

            buffer.write(struct.pack(">H", len(self.stack)))
            for state in self.stack:
                StackMapTable._write_verification_type(state, class_file, buffer)

    STACK_MAP_FRAMES = (
        SameFrame,
        AppendFrame,
        SameLocals1StackItemFrame,
        ChopFrame,
        FullFrame,
        SameFrameExtended,
        SameLocals1StackItemFrameExtended,
    )


class LineNumberTable(AttributeInfo):
    """
    Records a mapping of line numbers to bytecode offsets.
    """

    __slots__ = ("entries",)

    name_ = "LineNumberTable"
    since = Version(45, 3)
    locations = ("Code",)

    def __init__(self, parent: "Code") -> None:
        super().__init__(parent, LineNumberTable.name_)

        self.entries: List[LineNumberTable.LineNumberEntry] = []

    def __repr__(self) -> str:
        return "<LineNumberTable(%r) at %x>" % (self.entries, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        self.entries.clear()
        entry_count, = struct.unpack(">H", buffer.read(2))
        for index in range(entry_count):
            self.entries.append(LineNumberTable.LineNumberEntry.read(class_file, buffer))

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", len(self.entries)))
        for entry in self.entries:
            entry.write(class_file, buffer)

    class LineNumberEntry:
        """
        An entry in the line number table.
        """

        __slots__ = ("class_file", "start_pc", "line_number",)

        @classmethod
        def read(cls, class_file: ClassFile, buffer: IO[bytes]) -> "LineNumberTable.LineNumberEntry":
            """
            Reads a line number entry from the buffer.

            :param class_file: The class file that the entry belongs to.
            :param buffer: The binary buffer to read from.
            :return: The read line number entry.
            """

            entry = cls()
            entry.start_pc, entry.line_number = struct.unpack(">HH", buffer.read(4))
            return entry

        def __init__(self, start_pc: Union[int, None] = None, line_number: Union[int, None] = None) -> None:
            """
            :param start_pc: The starting bytecode offset of the line.
            :param line_number: The source code line number.
            """

            self.start_pc = start_pc
            self.line_number = line_number

        def __repr__(self) -> str:
            return "<LineNumberEntry(start_pc=%i, line_number=%i) at %x>" % (self.start_pc, self.line_number, id(self))

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            """
            Writes this line number entry to the buffer.

            :param class_file: The class file that this entry belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(struct.pack(">HH", self.start_pc, self.line_number))


class LocalVariableTable(AttributeInfo):
    """
    Contains the names of the local variables used in the code.
    """

    __slots__ = ("entries",)

    name_ = "LocalVariableTable"
    since = Version(45, 3)
    locations = ("Code",)

    def __init__(self, parent: "Code") -> None:
        super().__init__(parent, LocalVariableTable.name_)

        self.entries: List[LocalVariableTable.LocalVariableEntry] = []

    def __repr__(self) -> str:
        return "<LocalVariableTable(%r) at %x>" % (self.entries, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        self.entries.clear()
        entries_count, = struct.unpack(">H", buffer.read(2))
        for index in range(entries_count):
            self.entries.append(LocalVariableTable.LocalVariableEntry.read(class_file, buffer))

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", len(self.entries)))
        for entry in self.entries:
            entry.write(class_file, buffer)

    class LocalVariableEntry:
        """
        An entry in the local variable table.
        """

        __slots__ = ("start_pc", "length", "name", "descriptor", "index")

        @classmethod
        def read(cls, class_file: ClassFile, buffer: IO[bytes]) -> "LocalVariableTable.LocalVariableEntry":
            """
            Reads a local variable entry from the buffer.

            :param class_file: The class file that the entry belongs to.
            :param buffer: The binary buffer to read from.
            :return: The read local variable entry.
            """

            entry = cls()

            entry.start_pc, entry.length = struct.unpack(">HH", buffer.read(4))

            name_index, descriptor_index = struct.unpack(">HH", buffer.read(4))
            entry.name = class_file.constant_pool.get_utf8(name_index)
            entry.descriptor = class_file.constant_pool.get_utf8(descriptor_index)
            entry.index, = struct.unpack(">H", buffer.read(2))

            # try:
            #     self.type_ = descriptor.parse_field_descriptor(
            #         self.descriptor,
            #         force_read=self.class_file.context.force_read_descriptors,
            #         dont_throw=False,
            #     )
            # except Exception as error:
            #     self.type_ = descriptor.parse_field_descriptor(self.descriptor, force_read=False, dont_throw=True)

            #     logger.warning("Invalid descriptor %r in class %r: %r" % (
            #         self.descriptor, self.class_file.name, error.args[0],
            #     ))
            #     logger.debug("Invalid descriptor on local %r." % self, exc_info=True)

            return entry

        def __init__(
                self,
                start_pc: Union[int, None] = None,
                length: Union[int, None] = None,
                name: Union[str, None] = None,
                descriptor: Union[str, None] = None,
                index: Union[int, None] = None,
        ) -> None:
            """
            :param start_pc: The starting bytecode offset that the local variable appears at.
            :param length: How many bytecodes the local variable persists for.
            :param name: The name of the local variable.
            :param descriptor: The type descriptor of the local variable.
            :param index: The local variable index.
            """

            self.start_pc = start_pc
            self.length = length
            self.name = name
            self.descriptor = descriptor
            self.index = index

        def __repr__(self) -> str:
            return "<LocalVariableEntry(start_pc=%i, length=%i, index=%i, name=%r, descriptor=%r) at %x>" % (
                self.start_pc, self.length, self.index, self.name, self.descriptor, id(self),
            )

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            """
            Writes this local variable entry to the buffer.

            :param class_file: The class file that the entry belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(struct.pack(">HH", self.start_pc, self.length))
            buffer.write(struct.pack(
                ">HH", class_file.constant_pool.add_utf8(self.name), class_file.constant_pool.add_utf8(self.descriptor),
            ))
            buffer.write(struct.pack(">H", self.index))


class LocalVariableTypeTable(AttributeInfo):
    """
    Information about local variables with signatures.
    """

    __slots__ = ("entries",)

    name_ = "LocalVariableTypeTable"
    since = Version(49, 0)
    locations = ("Code",)

    def __init__(self, parent: "Code") -> None:
        super().__init__(parent, LocalVariableTypeTable.name_)

        self.entries: List[LocalVariableTypeTable.LocalVariableTypeEntry] = []

    def __repr__(self) -> str:
        return "<LocalVariableTypeTable(%r) at %x>" % (self.entries, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        self.entries.clear()
        entries_count, = struct.unpack(">H", buffer.read(2))
        for index in range(entries_count):
            self.entries.append(LocalVariableTypeTable.LocalVariableTypeEntry.read(class_file, buffer))

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", len(self.entries)))
        for entry in self.entries:
            entry.write(class_file, buffer)

    class LocalVariableTypeEntry:
        """
        An entry in the local variable type table.
        """

        __slots__ = ("start_pc", "length", "name", "signature", "index")

        @classmethod
        def read(cls, class_file: ClassFile, buffer: IO[bytes]) -> "LocalVariableTypeTable.LocalVariableTypeEntry":
            """
            Reads a local variable type entry from the buffer.

            :param class_file: The class file that the entry belongs to.
            :param buffer: The binary buffer to read from.
            :return: The entry that was read.
            """

            entry = cls()

            entry.start_pc, entry.length = struct.unpack(">HH", buffer.read(4))

            name_index, signature_index = struct.unpack(">HH", buffer.read(4))
            entry.name = class_file.constant_pool.get_utf8(name_index)
            entry.signature = class_file.constant_pool.get_utf8(signature_index)
            entry.index, = struct.unpack(">H", buffer.read(2))

            # try:
            #     self.type_ = signature.parse_field_signature(
            #         self.signature,
            #         force_read=self.class_file.context.force_read_signatures,
            #         dont_throw=False,
            #     )
            # except Exception as error:
            #     self.type_ = signature.parse_field_signature(self.signature, force_read=False, dont_throw=True)

            #     logger.warning("Invalid signature %r in class %r: %r" % (
            #         self.signature, self.class_file.name, error.args[0],
            #     ))
            #     logger.debug("Invalid signature on local %r." % self, exc_info=True)

            return entry

        def __init__(
                self,
                start_pc: Union[int, None] = None,
                length: Union[int, None] = None,
                name: Union[str, None] = None,
                signature: Union[str, None] = None,
                index: Union[int, None] = None,
        ) -> None:
            """
            :param start_pc: The starting bytecode offset that the local variable appears.
            :param length: How many bytecodes the local variable appears for.
            :param name: The name of the local variable.
            :param signature: The signature of the local variable.
            :param index: The index of the local variable.
            """

            self.start_pc = start_pc
            self.length = length
            self.name = name
            self.signature = signature
            self.index = index

        def __repr__(self) -> str:
            return "<LocalVariableTypeEntry(start_pc=%i, length=%i, index=%i, name=%r, signature=%r) at %x>" % (
                self.start_pc, self.length, self.index, self.name, self.signature, id(self),
            )

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            """
            Writes this local variable type entry to the buffer.

            :param class_file: The class file that this entry belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(struct.pack(">HH", self.start_pc, self.length))
            buffer.write(struct.pack(
                ">HH", class_file.constant_pool.add_utf8(self.name), class_file.constant_pool.add_utf8(self.signature),
            ))
            buffer.write(struct.pack(">H", self.index))
