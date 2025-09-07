from .data_classes import TypeEnum
from llvmlite import ir

def string_to_ir(string_type: str) -> ir.Type:
    match string_type:
        case 'int':
            return TypeEnum.int32
        case 'int*':
            return TypeEnum.int32.as_pointer()
        case 'float':
            return TypeEnum.float32
        case 'bool':
            return TypeEnum.boolean
        case 'str':
            return TypeEnum.string
        case 'string':
            return TypeEnum.string
        case _:
            pass
    return TypeEnum.void

def ir_to_string(ir_type: ir.Type) -> str:
    if isinstance(ir_type, ir.IntType):
        if ir_type.width == 1:
            return 'bool'
        elif ir_type.width == 32:
            return 'int'
    elif isinstance(ir_type, ir.FloatType):
        return 'float'
    elif isinstance(ir_type, ir.PointerType):
        return 'str'
    return 'void'
