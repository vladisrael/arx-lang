from dataclasses import dataclass, field
from llvmlite import ir
from typing import Set

@dataclass
class TypeEnum:
    int64 : ir.IntType = ir.IntType(64)
    int32 : ir.IntType = ir.IntType(32)
    int16 : ir.IntType = ir.IntType(16)
    int8 : ir.IntType = ir.IntType(8)
    boolean : ir.IntType = ir.IntType(1)
    string : ir.PointerType = ir.IntType(8).as_pointer()
    void : ir.VoidType = ir.VoidType()


@dataclass
class ArtemisData:
    map_paths:Set[str] = field(default_factory=set)
    library_paths:Set[str] = field(default_factory=set)