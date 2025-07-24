from llvmlite import ir, binding
import configparser
import glob
import shutil
import os
import sys
import re
from .data_classes import ArtemisData, TypeEnum
from typing import Union, List, Tuple, Set, Dict, Optional, ItemsView, Any

def parse_function_overloads(items:ItemsView[str, str], module_name: str) -> dict:
    externs: dict = {}
    for sig, mapping in items:
        sig : str = sig.strip()
        mapping : str = mapping.strip()

        if not sig or not mapping:
            continue

        func_name, arg_part = (sig.split(':', 1) + [''])[:2]
        func_name : str = func_name.strip()
        arg_types : tuple = tuple(arg.strip() for arg in arg_part.split(',') if arg.strip())

        llvm_name, return_type = map(str.strip, mapping.split('>'))

        key : str = f'{module_name}.{func_name}'
        externs.setdefault(key, {})[arg_types] = (llvm_name, return_type)
    return externs



class ArtemisCompiler:
    def __init__(self, compiler_data: ArtemisData) -> None:
        self.module: ir.Module = ir.Module(name='arx')
        self.module.triple = binding.get_default_triple()
        self.builder : Optional[ir.IRBuilder] = None
        self.func : Optional[ir.Function] = None

        self.compiler_data: ArtemisData = compiler_data

        self.variables : Dict[str, Tuple[ir.AllocaInstr, ir.Type]] = {}
        self.loop_continue_stack: List[ir.Block] = []
        self.loop_break_stack: List[ir.Block] = []
        self.loop_counter : int = 0
        self.function_counter : int = 0
        self.if_counter : int = 0
        self.extern_c: List[str] = []
        self.extern_functions: Dict[str, dict] = {}

    def load_extern_modules(self, using_modules: List[str]) -> None:
        for path in self.compiler_data.map_paths:
            map_files = glob.glob(os.path.join(path, '*.map'))
            for map_file in map_files:
                cfg : configparser.RawConfigParser = configparser.RawConfigParser(delimiters=('='))
                cfg.read(map_file)
                module_name : str = cfg['meta']['name']

                if module_name != 'core' and module_name not in using_modules:
                    continue

                self.extern_c.append(module_name)

                externs : dict = parse_function_overloads(cfg['functions'].items(), module_name)
                for full_name, overloads in externs.items():
                    self.extern_functions.setdefault(full_name, {}).update(overloads)

        self.list_struct_type : ir.IdentifiedStructType = ir.global_context.get_identified_type('List')
        self.list_struct_type.set_body(TypeEnum.int32.as_pointer(), TypeEnum.int32)
    
    def declare_list_len(self) -> ir.Function:
        if not hasattr(self, 'list_len_func'):
            fn_type : ir.FunctionType = ir.FunctionType(TypeEnum.int32, [self.list_struct_type.as_pointer()])
            self.list_len_func : ir.Function = ir.Function(self.module, fn_type, name='core_list_len')
        return self.list_len_func
    
    def call_list_len(self, list_ptr) -> ir.CallInstr:
        list_len_fn : ir.Function = self.declare_list_len()
        return self.builder.call(list_len_fn, [list_ptr])
    
    def declare_list_get(self) -> ir.Function:
        if not hasattr(self, 'list_get_func'):
            fn_type : ir.FunctionType = ir.FunctionType(TypeEnum.int32, [self.list_struct_type.as_pointer(), TypeEnum.int32])
            self.list_get_func : ir.Function = ir.Function(self.module, fn_type, name='core_list_get')
        return self.list_get_func

    def call_list_get(self, list_ptr, index_val):
        list_get_fn = self.declare_list_get()
        return self.builder.call(list_get_fn, [list_ptr, index_val])

    def compile_function(self, name:str, parameters:list, statements:list, return_type:str):
        arg_types : List[ir.Type] = [string_to_ir(parameter_type) for _id, parameter_type, _name in parameters]
        func_type : ir.FunctionType = ir.FunctionType(string_to_ir(return_type), arg_types)
        self.func : ir.Function = ir.Function(self.module, func_type, name=name)
        block : ir.Block = self.func.append_basic_block(f'entry_{self.function_counter}')
        self.function_counter += 1
        self.builder : ir.IRBuilder = ir.IRBuilder(block)

        self.variables = {}
        self.current_function_return_type : str = return_type
        for i, (_id, _type, name) in enumerate(parameters):
            arg = self.func.args[i]
            arg.name = name
            ptr : ir.AllocaInstr = self.builder.alloca(arg.type, name=name)
            self.builder.store(arg, ptr)
            self.variables[name] = (ptr, arg.type)

        for statement in statements:
            self.compile_statement(statement)

        if self.builder.block.terminator is None:
            raise Exception(f'Missing return in function {name}')

    def compile_statement(self, statement:tuple) -> None:
        kind : str = statement[0]
        if kind == 'expression':
            self.compile_expression(statement[1])
        elif kind == 'return':
            return_value = self.compile_expression(statement[1])
            self.builder.ret(return_value)
        elif kind == 'return_void':
            if self.current_function_return_type != 'void':
                raise TypeError('Void return used in non-void function')
            self.builder.ret_void()
        elif kind == 'declare':
            variable_type_str, variable_name, value_expr = statement[1], statement[2], statement[3]
            value = self.compile_expression(value_expr)

            if variable_type_str == 'int':
                ptr : ir.AllocaInstr = self.builder.alloca(TypeEnum.int32, name=variable_name)
                self.builder.store(value, ptr)
                self.variables[variable_name] = (ptr, value.type)
            elif variable_type_str == 'bool':
                ptr : ir.AllocaInstr = self.builder.alloca(TypeEnum.boolean, name=variable_name)
                self.builder.store(value, ptr)
                self.variables[variable_name] = (ptr, value.type)
            elif variable_type_str == 'string':
                ptr : ir.AllocaInstr = self.builder.alloca(TypeEnum.string, name=variable_name)
                self.builder.store(value, ptr)
                self.variables[variable_name] = (ptr, value.type)
            else:
                raise NotImplementedError(f'Unsupported type: {variable_type_str}')
        elif kind == 'if_chain':
            branches = statement[1]
            end_block : ir.Block = self.func.append_basic_block(f'if_end_{self.if_counter}')
            self.if_counter += 1
            has_fallthrough : bool = False

            for i, (condition_expression, statements) in enumerate(branches):
                then_block : ir.Block = self.func.append_basic_block(f'if_then_{i}')
                next_block : ir.Block = self.func.append_basic_block(f'if_next_{i}') if i < len(branches) - 1 else end_block

                if condition_expression is not None:
                    cond_val = self.compile_expression(condition_expression)
                    self.builder.cbranch(cond_val, then_block, next_block)
                else:
                    self.builder.branch(then_block)

                self.builder.position_at_start(then_block)

                for statement in statements:
                    self.compile_statement(statement)

                if self.builder.block.terminator is None:
                    self.builder.branch(end_block)
                    has_fallthrough = True

                if condition_expression is not None:
                    self.builder.position_at_start(next_block)

            if has_fallthrough and not end_block.is_terminated:
                self.builder.position_at_start(end_block)
        elif kind == 'for_in':
            var_type, var_name, list_name, body = statement[1], statement[2], statement[3], statement[4]

            index_ptr : ir.AllocaInstr = self.builder.alloca(TypeEnum.int32, name=f"{var_name}_index")
            self.builder.store(ir.Constant(TypeEnum.int32, 0), index_ptr)

            conditional_block : ir.Block = self.func.append_basic_block(f'for_conditional_{self.loop_counter}')
            body_block : ir.Block = self.func.append_basic_block(f'for_body_{self.loop_counter}')
            end_block : ir.Block = self.func.append_basic_block(f'for_end_{self.loop_counter}')
            continue_block : ir.Block = self.func.append_basic_block(f'for_continue_{self.loop_counter}')
            self.loop_counter += 1

            self.builder.branch(conditional_block)
            self.builder.position_at_start(conditional_block)

            list_ptr : ir.AllocaInstr = self.variables[list_name][0]
            index_value : ir.LoadInstr = self.builder.load(index_ptr)
            list_len : ir.CallInstr = self.call_list_len(list_ptr)
            cond : ir.ICMPInstr = self.builder.icmp_signed('<', index_value, list_len)
            self.builder.cbranch(cond, body_block, end_block)

            self.builder.position_at_start(body_block)

            element : ir.CallInstr = self.call_list_get(list_ptr, index_value)
            variable_ptr : ir.AllocaInstr = self.builder.alloca(TypeEnum.int32, name=var_name)
            self.builder.store(element, variable_ptr)
            self.variables[var_name] = (variable_ptr, string_to_ir(var_type))

            self.loop_continue_stack.append(continue_block)
            self.loop_break_stack.append(end_block)

            for for_in_statement in body:
                self.compile_statement(for_in_statement)
            
            self.loop_continue_stack.pop()
            self.loop_break_stack.pop()
            self.builder.branch(continue_block)

            self.builder.position_at_start(continue_block)
            new_index = self.builder.add(self.builder.load(index_ptr), ir.Constant(TypeEnum.int32, 1))
            self.builder.store(new_index, index_ptr)
            self.builder.branch(conditional_block)

            self.builder.position_at_start(end_block)

        elif kind == 'while':
            condition_expr, body = statement[1], statement[2]

            condition_block: ir.Block = self.func.append_basic_block(f'while_conditional_{self.loop_counter}')
            body_block: ir.Block = self.func.append_basic_block(f'while_body_{self.loop_counter}')
            end_block: ir.Block = self.func.append_basic_block(f'while_end_{self.loop_counter}')
            continue_block: ir.Block = self.func.append_basic_block(f'while_continue_{self.loop_counter}')
            self.loop_counter += 1

            self.builder.branch(condition_block)

            self.builder.position_at_start(condition_block)
            condition_value: ir.Value = self.compile_expression(condition_expr)
            self.builder.cbranch(condition_value, body_block, end_block)

            self.builder.position_at_start(body_block)

            self.loop_break_stack.append(end_block)
            self.loop_continue_stack.append(continue_block)

            for in_while_statement in body:
                self.compile_statement(in_while_statement)

            self.loop_break_stack.pop()
            self.loop_continue_stack.pop()

            self.builder.branch(continue_block)

            self.builder.position_at_start(continue_block)
            self.builder.branch(condition_block)

            self.builder.position_at_start(end_block)

        elif kind == 'declare_list':
            element_type, name, expression = statement[1], statement[2], statement[3]
            if expression[0] == 'list_literal':
                elements = [self.compile_expression(e) for e in expression[1]]

                array_type : ir.ArrayType = ir.ArrayType(TypeEnum.int32, len(elements))
                array_const : ir.Constant = ir.Constant(array_type, elements)

                array_ptr : ir.AllocaInstr = self.builder.alloca(array_type)
                self.builder.store(array_const, array_ptr)
                casted_ptr = self.builder.bitcast(array_ptr, TypeEnum.int32.as_pointer())

                create_fn : ir.Function = ir.Function(self.module,
                    ir.FunctionType(self.list_struct_type.as_pointer(), [TypeEnum.int32.as_pointer(), TypeEnum.int32]),
                    name='core_list_create_int_from'
                )
                list_ptr : ir.CallInstr = self.builder.call(create_fn, [casted_ptr, ir.Constant(TypeEnum.int32, len(elements))])
                self.variables[name] = (list_ptr, self.list_struct_type.as_pointer())
            else:
                value : ir.CallInstr = self.compile_expression(expression)
                self.variables[name] = [value, value.type]

        elif kind == 'break':
            self.builder.branch(self.loop_break_stack[-1])

        elif kind == 'continue':
            self.builder.branch(self.loop_continue_stack[-1])

        elif kind == 'assign':
            var_name : str = statement[1]
            expr : tuple = statement[2]

            value : ir.Constant = self.compile_expression(expr)

            if var_name not in self.variables:
                raise NameError(f'Variable {var_name} is not declared')
            
            ptr : ir.AllocaInstr = self.variables[var_name][0]
            if ptr.type.pointee != value.type:
                raise TypeError(f'Type mismatch in assignment to {var_name} expected {ptr.type} and got {value.type}')
            
            self.builder.store(value, ptr)

    def compile_expression(self, expression:tuple) -> Union[ir.Value, Any]:
        kind : str = expression[0]

        if kind == 'call':
            name : str = expression[1]
            args = expression[2]

            arg_values = [self.compile_expression(arg) for arg in args]
            arg_types = [value.type for value in arg_values]

            func : ir.Function = self.module.globals.get(name)
            if not func:
                func_type : ir.FunctionType = ir.FunctionType(int32, arg_values)
                func : ir.Function = ir.Function(self.module, func_type, name=name)

            return self.builder.call(func, arg_values)
        
        elif kind == 'call_method':
            obj, method, args = expression[1], expression[2], expression[3]
            full_name = f'{obj}.{method}'

            if full_name not in self.extern_functions:
                raise NameError(f'Function {full_name} not found in extern functions')

            overloads = self.extern_functions[full_name]

            arg_vals = [self.compile_expression(arg) for arg in args]
            arg_types = tuple(ir_to_string(arg.type) for arg in arg_vals)

            if arg_types not in overloads:
                raise TypeError(f'Function {full_name} has no overload matching argument types {arg_types}')

            llvm_name, return_type_id = overloads[arg_types]
            return_type : ir.Type = string_to_ir(return_type_id)
            if return_type_id.startswith('list'):
                return_type : ir.Type = self.list_struct_type.as_pointer()

            func : Optional[ir.Function] = self.module.globals.get(llvm_name)
            if not func:
                func_type : ir.FunctionType = ir.FunctionType(return_type, [arg.type for arg in arg_vals])
                func = ir.Function(self.module, func_type, name=llvm_name)

            return self.builder.call(func, arg_vals)

        elif kind == 'int':
            return ir.Constant(TypeEnum.int32, expression[1])

        elif kind == 'string':
            data : bytearray = bytearray(expression[1].encode('utf8') + b'\0')
            str_type : ir.ArrayType = ir.ArrayType(ir.IntType(8), len(data))
            global_str : ir.GlobalVariable = ir.GlobalVariable(self.module, str_type, name=f'string_{
                                           len(self.module.global_values)}')
            global_str.global_constant = True
            global_str.initializer = ir.Constant(str_type, data)
            ptr = self.builder.bitcast(global_str, TypeEnum.string)
            return ptr

        elif kind == 'binop':
            operator, left_part, right_part = expression[1], expression[2], expression[3]
            left_value = self.compile_expression(left_part)
            right_value = self.compile_expression(right_part)

            match operator:
                case '==':
                    if left_value.type == TypeEnum.string and right_value.type == TypeEnum.string:
                        llvm_name: str = 'core_string_equal'
                        func : ir.Function = self.module.globals.get(llvm_name)
                        if not func:
                            func = ir.Function(self.module, ir.FunctionType(TypeEnum.boolean, [
                                            TypeEnum.string, TypeEnum.string]), name=llvm_name)
                        return self.builder.call(func, [left_value, right_value])
                    return self.builder.icmp_signed('==', left_value, right_value)
                case '!=':
                    return self.builder.icmp_signed('!=', left_value, right_value)
                case '<=':
                    return self.builder.icmp_signed('<=', left_value, right_value)
                case '>=':
                    return self.builder.icmp_signed('>=', left_value, right_value)
                case '<':
                    return self.builder.icmp_signed('<', left_value, right_value)
                case '>':
                    return self.builder.icmp_signed('>', left_value, right_value)
                case '+':
                    if left_value.type == TypeEnum.string and right_value.type == TypeEnum.string:
                        llvm_name: str = 'core_string_concat'
                        func : ir.Function = self.module.globals.get(llvm_name)
                        if not func:
                            func = ir.Function(self.module, ir.FunctionType(TypeEnum.string, [
                                            TypeEnum.string, TypeEnum.string]), name=llvm_name)
                        return self.builder.call(func, [left_value, right_value])
                    return self.builder.add(left_value, right_value)
                case '-':
                    return self.builder.sub(left_value, right_value)
                case '*':
                    return self.builder.mul(left_value, right_value)
                case '/':
                    return self.builder.sdiv(left_value, right_value)  # signed division
                case _:
                    raise NotImplementedError(f'Unsupported operator: {operator}')

        elif kind == 'var':
            var_name : str = expression[1]
            if var_name not in self.variables:
                raise NameError(f'Undefined variable: {var_name}')
            ptr : ir.AllocaInstr = self.variables[var_name][0]
            return self.builder.load(ptr)

        elif kind == 'bool':
            return ir.Constant(ir.IntType(1), 1 if expression[1] else 0)

        else:
            raise NotImplementedError(f'Expresion kind {kind} not implemented')

    def add_c_main(self):
        func_type : ir.FunctionType = ir.FunctionType(TypeEnum.int32, [])
        main_fn : ir.Function = ir.Function(self.module, func_type, name='main')
        block : ir.Block = main_fn.append_basic_block(name='entry')
        builder : ir.IRBuilder = ir.IRBuilder(block)

        exec_fn = self.module.get_global('_exec')
        return_value = builder.call(exec_fn, [])
        builder.ret(return_value)

def string_to_ir(string_type: str) -> ir.Type:
    match string_type:
        case 'int':
            return TypeEnum.int32
        case 'int*':
            return TypeEnum.int32.as_pointer()
        case 'bool':
            return TypeEnum.boolean
        case 'str':
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
    elif isinstance(ir_type, ir.PointerType):
        return 'str'
    return 'void'
