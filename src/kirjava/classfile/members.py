#!/usr/bin/env python3

import logging
import struct
import typing
from typing import Dict, IO, Tuple, Union

from . import descriptor
from .. import _argument
from ..abc import Field, Method
from ..types import BaseType

if typing.TYPE_CHECKING:
    from . import ClassFile
    from .attributes import AttributeInfo

logger = logging.getLogger("kirjava.classfile.members")


class MethodInfo(Method):
    """
    Represents a method in a class.
    """

    __slots__ = ("_class", "_name", "_argument_types", "_return_type", "access_flags", "attributes")

    @classmethod
    def read(cls, class_file: "ClassFile", buffer: IO[bytes]) -> "MethodInfo":
        """
        Reads a method info from the buffer.

        :param class_file: The class file that the method belongs to.
        :param buffer: The binary buffer to read from.
        :return: The method info that was read.
        """

        method_info = cls.__new__(cls)

        method_info._class = class_file
        method_info.access_flags, name_index, descriptor_index = struct.unpack(">HHH", buffer.read(6))
        method_info._name = class_file.constant_pool.get_utf8(name_index)
        descriptor_ = class_file.constant_pool.get_utf8(descriptor_index)

        try:
            type_ = descriptor.parse_method_descriptor(
                descriptor_,
                force_read=False,
                dont_throw=False,
            )
            method_info._argument_types, method_info._return_type = type_

        except Exception as error:
            type_ = descriptor.parse_method_descriptor(descriptor_, force_read=False, dont_throw=True)

            if not isinstance(type_, tuple) or len(type_) != 2:
                method_info._argument_types = type_
                method_info._return_type = type_
            else:
                method_info._argument_types, method_info._return_type = type_

            logger.warning("Invalid descriptor %r in class %r: %r" % (descriptor_, class_file.name, error))
            logger.debug("Invalid descriptor on method %r." % method_info, exc_info=True)

        method_info.attributes = {}
        attributes_count, = struct.unpack(">H", buffer.read(2))
        for index in range(attributes_count):
            attribute_info = attributes.read_attribute(method_info, class_file, buffer)
            method_info.attributes[attribute_info.name] = (
                method_info.attributes.setdefault(attribute_info.name, ()) + (attribute_info,)
            )

        return method_info

    ACC_PUBLIC = 0x0001
    ACC_PRIVATE = 0x0002
    ACC_PROTECTED = 0x0004
    ACC_STATIC = 0x0008
    ACC_FINAL = 0x0010
    ACC_SYNCHRONIZED = 0x0020
    ACC_BRIDGE = 0x0040
    ACC_VARARGS = 0x0080
    ACC_NATIVE = 0x0100
    ACC_ABSTRACT = 0x0400
    ACC_STRICT = 0x0800
    ACC_SYNTHETIC = 0x1000

    @property
    def is_public(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_PUBLIC)

    @is_public.setter
    def is_public(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_PUBLIC
        else:
            self.access_flags &= ~MethodInfo.ACC_PUBLIC

    @property
    def is_private(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_PRIVATE)

    @is_private.setter
    def is_private(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_PRIVATE
        else:
            self.access_flags &= ~MethodInfo.ACC_PRIVATE

    @property
    def is_protected(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_PROTECTED)

    @is_protected.setter
    def is_protected(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_PROTECTED
        else:
            self.access_flags &= ~MethodInfo.ACC_PROTECTED

    @property
    def is_static(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_STATIC)

    @is_static.setter
    def is_static(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_STATIC
        else:
            self.access_flags &= ~MethodInfo.ACC_STATIC

    @property
    def is_final(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_FINAL)

    @is_final.setter
    def is_final(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_FINAL
        else:
            self.access_flags &= ~MethodInfo.ACC_FINAL

    @property
    def is_synchronized(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_SYNCHRONIZED)

    @is_synchronized.setter
    def is_synchronized(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_SYNCHRONIZED
        else:
            self.access_flags &= ~MethodInfo.ACC_SYNCHRONIZED

    @property
    def is_bridge(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_BRIDGE)

    @is_bridge.setter
    def is_bridge(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_BRIDGE
        else:
            self.access_flags &= ~MethodInfo.ACC_BRIDGE

    @property
    def is_varargs(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_VARARGS)

    @is_varargs.setter
    def is_varargs(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_VARARGS
        else:
            self.access_flags &= ~MethodInfo.ACC_VARARGS

    @property
    def is_abstract(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_ABSTRACT)

    @is_abstract.setter
    def is_abstract(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_ABSTRACT
        else:
            self.access_flags &= ~MethodInfo.ACC_ABSTRACT

    @property
    def is_native(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_NATIVE)

    @is_native.setter
    def is_native(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_NATIVE
        else:
            self.access_flags &= ~MethodInfo.ACC_NATIVE

    @property
    def is_synthetic(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_SYNTHETIC)

    @is_synthetic.setter
    def is_synthetic(self, value: bool) -> None:
        if value: 
            self.access_flags |= MethodInfo.ACC_SYNTHETIC
        else:
            self.access_flags &= ~MethodInfo.ACC_SYNTHETIC

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def argument_types(self) -> Tuple[BaseType, ...]:
        return self._argument_types

    @argument_types.setter
    def argument_types(self, value: Tuple[BaseType, ...]) -> None:
        self._argument_types = value

    @property
    def return_type(self) -> BaseType:
        return self._return_type

    @return_type.setter
    def return_type(self, value: BaseType) -> None:
        self._return_type = value

    @property
    def class_(self) -> "ClassFile":
        return self._class

    @property
    def code(self) -> Union["Code", None]:
        """
        :return: The code attribute for this method, None if it doesn't have one.
        """

        code, *_ = self.attributes.get(Code.name_, (None,))
        return code

    @code.setter
    def code(self, value: Union["Code", None]) -> None:
        """
        Sets this method's code attribute.
        """

        if value is None:
            del self.attributes[Code.name_]
        else:
            self.attributes[value.name] = (value,)

    def __init__(
            self,
            class_: "ClassFile",
            name: str,
            *descriptor_: _argument.MethodDescriptor,
            is_public: bool = False,
            is_private: bool = False,
            is_protected: bool = False,
            is_static: bool = False,
            is_final: bool = False,
            is_synchronized: bool = False,
            is_bridge: bool = False,
            is_varargs: bool = False,
            is_abstract: bool = False,
            is_native: bool = False,
            is_synthetic: bool = False,
    ) -> None:
        """
        :param class_: The classfile that this method belongs to.
        :param name: The name of the method.
        :param argument_types: The argument types of this method.
        :param return_type: The return type of this method.
        """

        self._name = name
        self._argument_types, self._return_type = _argument.get_method_descriptor(*descriptor_)
        self._class = class_

        if class_ is not None and not self in class_._methods:
            class_._methods.append(self)

        self.access_flags = 0

        self.is_public = is_public
        self.is_private = is_private
        self.is_protected = is_protected
        self.is_static = is_static
        self.is_final = is_final
        self.is_synchronized = is_synchronized
        self.is_bridge = is_bridge
        self.is_varargs = is_varargs
        self.is_abstract = is_abstract
        self.is_native = is_native
        self.is_synthetic = is_synthetic

        self.attributes: Dict[str, Tuple[AttributeInfo, ...]] = {}

    def __repr__(self) -> str:
        return "<MethodInfo(name=%r, argument_types=(%s), return_type=%s) at %x>" % (
            self._name,
            # More Pythonic looking to add a comma to the end
            ", ".join(map(str, self._argument_types)) + ("," if len(self._argument_types) == 1 else ""),
            self._return_type, id(self),
        )

    def __str__(self) -> str:
        if self._class is None:
            return "%s %s(%s)" % (self.return_type, self._name, ", ".join(map(str, self._argument_types)))
        return "%s#%s %s(%s)" % (
            self._class.name, self.return_type, self._name, ", ".join(map(str, self._argument_types)),
        )

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        """
        Writes this method to the buffer.

        :param class_file: The class file that this method belongs to.
        :param buffer: The binary buffer to write to.
        """

        if self._class is None:  # Might be explicitly writing this to a different classfile? Idk.
            self._class = class_file

        buffer.write(struct.pack(
            ">HHH",
            self.access_flags,
            class_file.constant_pool.add_utf8(self._name),
            class_file.constant_pool.add_utf8(descriptor.to_descriptor(self._argument_types, self._return_type)),
        ))

        buffer.write(struct.pack(">H", len(self.attributes)))
        for attributes_ in self.attributes.values():
            for attribute in attributes_:
                attributes.write_attribute(attribute, class_file, buffer)


class FieldInfo(Field):
    """
    Represents a field in class.
    """

    __slots__ = ("_class", "_name", "_type", "access_flags", "attributes")
    
    @classmethod
    def read(cls, class_file: "ClassFile", buffer: IO[bytes]) -> "FieldInfo":
        """
        Reads a field info from the buffer, given the class file it belongs too as well.

        :param class_file: The class file that the field belongs to.
        :param buffer: The binary buffer to read from.
        :return: The field info that was read.
        """

        field_info = cls.__new__(cls)

        field_info._class = class_file
        field_info.access_flags, name_index, descriptor_index = struct.unpack(">HHH", buffer.read(6))
        field_info._name = class_file.constant_pool.get_utf8(name_index)
        descriptor_ = class_file.constant_pool.get_utf8(descriptor_index)

        try:
            field_info._type = descriptor.parse_field_descriptor(
                descriptor_,
                force_read=False,
                dont_throw=False,
            )
        except Exception as error:  # force_read=True won't throw
            field_info._type = descriptor.parse_field_descriptor(descriptor_, force_read=False, dont_throw=True)

            logger.warning("Invalid descriptor %r in class %r: %r" % (descriptor_, class_file.name, error.args[0]))
            logger.debug("Invalid descriptor on field %r." % field_info, exc_info=True)

        field_info.attributes = {}
        attributes_count, = struct.unpack(">H", buffer.read(2))
        for index in range(attributes_count):
            attribute_info = attributes.read_attribute(field_info, class_file, buffer)
            field_info.attributes[attribute_info.name] = (
                field_info.attributes.setdefault(attribute_info.name, ()) + (attribute_info,)
            )

        return field_info

    ACC_PUBLIC = 0x0001
    ACC_PRIVATE = 0x0002
    ACC_PROTECTED = 0x0004
    ACC_STATIC = 0x0008
    ACC_FINAL = 0x0010
    ACC_VOLATILE = 0x0040
    ACC_TRANSIENT = 0x0080
    ACC_SYNTHETIC = 0x1000
    ACC_ENUM = 0x4000

    @property
    def is_public(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_PUBLIC)

    @is_public.setter
    def is_public(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_PUBLIC
        else:
            self.access_flags &= ~FieldInfo.ACC_PUBLIC

    @property
    def is_private(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_PRIVATE)

    @is_private.setter
    def is_private(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_PRIVATE
        else:
            self.access_flags &= ~FieldInfo.ACC_PRIVATE

    @property
    def is_protected(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_PROTECTED)

    @is_protected.setter
    def is_protected(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_PROTECTED
        else:
            self.access_flags &= ~FieldInfo.ACC_PROTECTED

    @property
    def is_static(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_STATIC)

    @is_static.setter
    def is_static(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_STATIC
        else:
            self.access_flags &= ~FieldInfo.ACC_STATIC

    @property
    def is_final(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_FINAL)

    @is_final.setter
    def is_final(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_FINAL
        else:
            self.access_flags &= ~FieldInfo.ACC_FINAL

    @property
    def is_volatile(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_VOLATILE)

    @is_volatile.setter
    def is_volatile(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_VOLATILE
        else:
            self.access_flags &= ~FieldInfo.ACC_VOLATILE

    @property
    def is_transient(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_TRANSIENT)

    @is_transient.setter
    def is_transient(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_TRANSIENT
        else:
            self.access_flags &= ~FieldInfo.ACC_TRANSIENT

    @property
    def is_synthetic(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_SYNTHETIC)

    @is_synthetic.setter
    def is_synthetic(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_SYNTHETIC
        else:
            self.access_flags &= ~FieldInfo.ACC_SYNTHETIC

    @property
    def is_enum(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_ENUM)

    @is_enum.setter
    def is_enum(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_ENUM
        else:
            self.access_flags &= ~FieldInfo.ACC_ENUM

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def type(self) -> BaseType:
        return self._type

    @type.setter
    def type(self, value: BaseType) -> None:
        self._type = value

    @property
    def class_(self) -> "ClassFile":
        return self._class

    def __init__(
            self,
            class_: "ClassFile",
            name: str,
            type_: _argument.FieldDescriptor,
            is_public: bool = False,
            is_private: bool = False,
            is_protected: bool = False,
            is_static: bool = False,
            is_final: bool = False,
            is_volatile: bool = False,
            is_transient: bool = False,
            is_synthetic: bool = False,
            is_enum: bool = False,
    ) -> None:
        """
        :param class_: The class that this field belongs to.
        :param name: The name of this field.
        :param type_: The type of this field.
        """

        self._name = name
        self._type = _argument.get_field_descriptor(type_)
        self._class = class_

        if class_ is not None and not self in class_._fields:
            class_._fields.append(self)

        self.access_flags = 0

        self.is_public = is_public
        self.is_private = is_private
        self.is_protected = is_protected
        self.is_static = is_static
        self.is_final = is_final
        self.is_volatile = is_volatile
        self.is_transient = is_transient
        self.is_synthetic = is_synthetic
        self.is_enum = is_enum

        self.attributes: Dict[str, Tuple[AttributeInfo, ...]] = {}

    def __repr__(self) -> str:
        return "<FieldInfo(name=%r, type=%s) at %x>" % (self._name, self._type, id(self))

    def __str__(self) -> str:
        if self._class is None:
            return "%s %s" % (self._type, self._name)
        return "%s#%s %s" % (self._class.name, self._type, self._name)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        """
        Writes this field info to the buffer.

        :param class_file: The class file to write this field to.
        :param buffer: The binary buffer to write to.
        """

        if self._class is None:
            self._class = class_file

        buffer.write(struct.pack(
            ">HHH",
            self.access_flags,
            class_file.constant_pool.add_utf8(self._name),
            class_file.constant_pool.add_utf8(descriptor.to_descriptor(self._type)),
        ))

        buffer.write(struct.pack(">H", len(self.attributes)))
        for attributes_ in self.attributes.values():
            for attribute in attributes_:
                attributes.write_attribute(attribute, class_file, buffer)


from . import attributes
from .attributes.method import Code
# from ..analysis.graph import InsnGraph
