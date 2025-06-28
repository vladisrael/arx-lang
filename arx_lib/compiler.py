from llvmlite import ir, binding
import configparser, glob, shutil, os, sys, re
from .data_classes import ArtemisData
from typing import List, Tuple, Set, Dict, Optional

int32 = ir.IntType(32)
void = ir.VoidType()

class ArtemisCompiler:
    def __init__(self, compiler_data:ArtemisData):
        self.module : ir.Module = ir.Module(name="arx")
        self.module.triple = binding.get_default_triple()
        self.builder = None
        self.func = None

        self.variables = {}
        self.extern_c : List[str] = []
        self.extern_functions : Dict[str, str] = {}
        self.type_string : ir.Type = ir.IntType(8).as_pointer()

        for path in compiler_data.map_paths:
            maps : str = glob.glob(os.path.join(path, '*.map'))
            for map_file in maps:
                cfg : configparser.ConfigParser = configparser.ConfigParser()
                cfg.read(map_file)
                self.extern_c.append(
                    cfg['meta']['name']
                )

                for arx_name, c_name in cfg['functions'].items():
                    self.extern_functions[f"{cfg['meta']['name']}.{arx_name}"] = c_name

    def compile_function(self, name, statements):
        func_ty = ir.FunctionType(int32, [])
        self.func = ir.Function(self.module, func_ty, name=name)
        block = self.func.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)

        for stmt in statements:
            self.compile_statement(stmt)

        if self.builder.block.terminator is None:
            self.builder.ret(ir.Constant(int32, 0))

    def compile_statement(self, stmt):
        kind = stmt[0]
        if kind == 'expr':
            self.compile_expr(stmt[1])
        elif kind == 'return':
            retval = self.compile_expr(stmt[1])
            self.builder.ret(retval)
        elif kind == 'declare':
            var_type_str, var_name, value_expr = stmt[1], stmt[2], stmt[3]
            value = self.compile_expr(value_expr)

            # For now, only support int
            if var_type_str == 'int':
                ptr = self.builder.alloca(int32, name=var_name)
                self.builder.store(value, ptr)
                self.variables[var_name] = ptr
            elif var_type_str == 'bool':
                bool_ty = ir.IntType(1)
                ptr = self.builder.alloca(bool_ty, name=var_name)
                self.builder.store(value, ptr)
                self.variables[var_name] = ptr
            elif var_type_str == 'string':
                ptr = self.builder.alloca(self.type_string, name=var_name)
                self.builder.store(value, ptr)
                self.variables[var_name] = ptr
            else:
                raise NotImplementedError(f'Unsupported type: {var_type_str}')

    def compile_expr(self, expr):
        kind = expr[0]

        if kind == 'call_method':
            obj, method, args = expr[1], expr[2], expr[3]
            full_name : str = obj + '.' + method
            if full_name not in self.extern_functions:
                raise NameError(f'Function {full_name} not found in extern functions')

            llvm_data : str = self.extern_functions[full_name]

            # Compile arguments
            arg_vals = [self.compile_expr(arg) for arg in args]
            arg_types = [arg.type for arg in arg_vals]
            llvm_name, return_type_id = llvm_data.split('>')
            if llvm_data.startswith('*'):
                result : Optional[re.Match] = re.search(rf'([a-zA-Z_][a-zA-Z0-9_]*)\:{','.join([ir_to_string(arg) for arg in arg_types])};', llvm_data)
                if not result:
                    raise TypeError(f'Function {full_name} not does not have ({' '.join([ir_to_string(arg) for arg in arg_types])}) arguments type match')
                llvm_name = result.group(1)
            elif ':' in llvm_data:
                result : Optional[re.Match] = re.search(rf'([a-zA-Z_][a-zA-Z0-9_]*)\:{','.join([ir_to_string(arg) for arg in arg_types])};', llvm_data)
                if not result:
                    raise TypeError(f'Function {full_name} not does not have ({' '.join([ir_to_string(arg) for arg in arg_types])}) arguments type match')
            return_type : ir.Type = ir.VoidType()
            match return_type_id:
                case 'str':
                    return_type = self.type_string
                case 'int':
                    return_type = ir.IntType(32)
                case 'bool':
                    return_type = ir.IntType(1)
            # Check if already declared
            func = self.module.globals.get(llvm_name)
            if not func:
                func_type = ir.FunctionType(return_type, arg_types)
                func = ir.Function(self.module, func_type, name=llvm_name)
            return self.builder.call(func, arg_vals)

        elif kind == 'int':
            return ir.Constant(int32, expr[1])
        
        elif kind == 'string':
            data = bytearray(expr[1].encode("utf8") + b'\0')
            str_type = ir.ArrayType(ir.IntType(8), len(data))
            global_str = ir.GlobalVariable(self.module, str_type, name=f"str{len(self.module.global_values)}")
            global_str.global_constant = True
            global_str.initializer = ir.Constant(str_type, data)
            ptr = self.builder.bitcast(global_str, self.type_string)
            return ptr
        
        elif kind == 'binop':
            op, left, right = expr[1], expr[2], expr[3]
            lval = self.compile_expr(left)
            rval = self.compile_expr(right)

            if op == '+':
                if lval.type == self.type_string and rval.type == self.type_string:
                    llvm_name : str = 'core_string_concat'
                    func = self.module.globals.get(llvm_name)
                    if not func:
                        func = ir.Function(self.module, ir.FunctionType(self.type_string, [self.type_string, self.type_string]), name=llvm_name)
                    return self.builder.call(func, [lval, rval])
                return self.builder.add(lval, rval)
            elif op == '-':
                return self.builder.sub(lval, rval)
            elif op == '*':
                return self.builder.mul(lval, rval)
            elif op == '/':
                return self.builder.sdiv(lval, rval)  # signed division
            else:
                raise NotImplementedError(f"Unsupported operator: {op}")

        elif kind == 'var':
            var_name = expr[1]
            if var_name not in self.variables:
                raise NameError(f"Undefined variable: {var_name}")
            ptr = self.variables[var_name]
            return self.builder.load(ptr)

        elif kind == 'bool':
            return ir.Constant(ir.IntType(1), 1 if expr[1] else 0)

        else:
            raise NotImplementedError(f"Expr kind {kind} not implemented")

    def add_c_main(self):
        # Define: int main() { return _exec(); }
        func_ty = ir.FunctionType(ir.IntType(32), [])
        main_fn = ir.Function(self.module, func_ty, name="main")
        block = main_fn.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)

        # Call _exec
        exec_fn = self.module.get_global("_exec")
        ret_val = builder.call(exec_fn, [])
        builder.ret(ret_val)

def ir_to_string(ir_type) -> str:
    if isinstance(ir_type, ir.IntType):
        if ir_type.width == 1:
            return 'bool'
        elif ir_type.width == 32:
            return 'int'
    elif isinstance(ir_type, ir.PointerType):
        return 'str'
    return 'NULL'