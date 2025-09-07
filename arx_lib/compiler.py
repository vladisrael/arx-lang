from llvmlite import ir, binding
import configparser
import glob
import shutil
import os
import sys
import re
from .data_classes import ArtemisData, TypeEnum
from .converters import ir_to_string, string_to_ir
from typing import Union, List, Tuple, Set, Dict, Optional, ItemsView, Any, Iterator, Iterable

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
        binding.initialize()
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()
        self.module: ir.Module = ir.Module(name='arx')
        self.module.triple = binding.get_default_triple()
        self.target : binding.Target = binding.Target.from_default_triple()
        self.target_machine : binding.TargetMachine = self.target.create_target_machine()
        llvm_ir : str = str(self.module)
        binding_module : binding.ModuleRef = binding.parse_assembly(llvm_ir)
        binding_module.verify()
        self.builder : Optional[ir.IRBuilder] = None
        self.func : Optional[ir.Function] = None
        self.compiler_data: ArtemisData = compiler_data
        self.variables : Dict[str, Tuple[ir.AllocaInstr, ir.Type]] = {}
        self.local_vars: Dict[str, ir.AllocaInstr] = {}
        self.loop_continue_stack: List[ir.Block] = []
        self.loop_break_stack: List[ir.Block] = []
        self.loop_counter : int = 0
        self.function_counter : int = 0
        self.if_counter : int = 0
        self.get_abi_counter : int = 0
        self.extern_c: List[str] = []
        self.extern_functions: Dict[str, dict] = {}

    def get_abi_size_from_ir_type(self, ir_type: ir.Type) -> int:
        if isinstance(ir_type, ir.IntType):
            return ir_type.width // 8
        elif isinstance(ir_type, ir.PointerType):
            return 8
        elif isinstance(ir_type, ir.FloatType):
            return 4
        elif isinstance(ir_type, ir.DoubleType):
            return 8
        elif isinstance(ir_type, ir.ArrayType):
            elem_size = self.get_abi_size_from_ir_type(ir_type.element)
            return elem_size * ir_type.count
        elif isinstance(ir_type, ir.LiteralStructType) or isinstance(ir_type, ir.IdentifiedStructType):
            total_size = 0
            for elem in ir_type.elements:
                total_size += self.get_abi_size_from_ir_type(elem)
            return total_size
        else:
            raise NotImplementedError(f'ABI size calculation not implemented for {ir_type}')
        
    def safe_store(self, value: ir.Value, pointer: ir.AllocaInstr):
        target_type = pointer.type.pointee
        if target_type != value.type:
            if target_type.is_pointer and value.type.is_pointer:
                value = self.builder.bitcast(value, target_type)
            else:
                raise TypeError(f'Cannot assign {value.type} to {target_type}')
        self.builder.store(value, pointer)

    def allocate_and_copy_array(self, elements: list[ir.Value], element_type: ir.Type) -> ir.Value:
        element_count : int = len(elements)
        element_size : int = self.get_abi_size_from_ir_type(element_type)
        total_size : ir.Constant = ir.Constant(TypeEnum.int32, element_count * element_size)
        malloc_fn : ir.Function = self.declare_malloc()
        heap_pointer = self.builder.call(malloc_fn, [self.builder.zext(total_size, TypeEnum.int64)], name='heap_pointer')
        typed_pointer = self.builder.bitcast(heap_pointer, element_type.as_pointer())
        for i, element in enumerate(elements):
            index = ir.Constant(TypeEnum.int32, i)
            element_address = self.builder.gep(typed_pointer, [index], name=f'element_pointer_{i}')
            element_value = element
            if element.type.is_pointer and not element.type == element_type:
                element_value = self.builder.load(element)
            self.safe_store(element_value, element_address)
        return heap_pointer

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
        self.list_struct_type.set_body(
            TypeEnum.int8.as_pointer(),
            TypeEnum.int32,
            TypeEnum.int32,
            TypeEnum.int64,
            TypeEnum.boolean
        )
    
    def declare_malloc(self) -> ir.Function:
        malloc_ty : ir.FunctionType = ir.FunctionType(TypeEnum.int8.as_pointer(), [TypeEnum.int64])
        malloc_fn : ir.Function = self.module.globals.get('malloc')
        if malloc_fn is None:
            malloc_fn = ir.Function(self.module, malloc_ty, name='malloc')
        return malloc_fn

    def declare_list_len(self) -> ir.Function:
        if not hasattr(self, 'list_len_func'):
            fn_type : ir.FunctionType = ir.FunctionType(TypeEnum.int32, [self.list_struct_type.as_pointer()])
            self.list_len_func : ir.Function = ir.Function(self.module, fn_type, name='core_list_len')
        return self.list_len_func

    def call_list_len(self, list_pointer:ir.AllocaInstr) -> ir.CallInstr:
        return self.builder.call(self.declare_list_len(), [list_pointer])

    def declare_list_get(self) -> ir.Function:
        if not hasattr(self, 'list_get_func'):
            fn_type : ir.FunctionType = ir.FunctionType(TypeEnum.int8.as_pointer(), [self.list_struct_type.as_pointer(), TypeEnum.int32])
            self.list_get_func : ir.Function = ir.Function(self.module, fn_type, name='core_list_get')
        return self.list_get_func

    def call_list_get(self, list_pointer:ir.AllocaInstr, index_value:ir.LoadInstr) -> ir.CallInstr:
        return self.builder.call(self.declare_list_get(), [list_pointer, index_value])

    def compile_function(self, node:tuple):
        _, name, parameters, statements, return_type = node
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
            self.safe_store(arg, ptr)
            self.variables[name] = (ptr, arg.type)
        for statement in statements:
            self.compile_statement(statement)
        if self.builder.block.terminator is None:
            raise Exception(f'Missing return in function {name}')
    
    def compile_class(self, node: tuple) -> None:
        _, name, body = node
        fields = [m for m in body if m[0] == 'field']
        methods = [m for m in body if m[0] == 'method']
        struct_type = ir.global_context.get_identified_type(name)
        field_types = [string_to_ir(ftype) for _, ftype, _, _ in fields]
        struct_type.set_body(*field_types)
        self.compiler_data.class_bodies[name] = {
            'fields': fields,
            'methods': methods,
            'struct': struct_type
        }
        self.current_class = name
        for method in methods:
            self.compile_method(name, method)
        self.current_class = None

    def compile_this_access(self, field_name: str):
        field_ptr = self.get_this_field_pointer(field_name)
        return self.builder.load(field_ptr)

    def get_this_field_pointer(self, field_name: str) -> ir.GEPInstr:
        this_ptr = self.local_vars.get('this')
        if not this_ptr:
            raise RuntimeError('this used outside of method')
        class_name = getattr(self, 'current_class', None)
        if not class_name:
            raise RuntimeError('No current_class while compiling this access')
        fields = self.compiler_data.class_bodies[class_name]['fields']
        idx = next((i for i, (_, _, fname, _) in enumerate(fields) if fname == field_name), None)
        if idx is None:
            raise NameError(f'Field {field_name} not found on {class_name}')
        return self.builder.gep(this_ptr, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), idx)])

    def compile_method(self, class_name: str, method_node: tuple) -> None:
        _, return_type, method_name, parameters, statements = method_node
        mangled = f'{class_name}_{method_name}'
        struct_type: ir.IdentifiedStructType = self.compiler_data.class_bodies[class_name]['struct']
        this_ir: ir.PointerType = struct_type.as_pointer()
        param_types = [string_to_ir(t) for _, t, _ in parameters]
        param_names = [n for _, _, n in parameters]
        return_ir = string_to_ir(return_type) if return_type != 'void' else ir.VoidType()
        func_type = ir.FunctionType(return_ir, [this_ir] + param_types)
        function = self.module.globals.get(mangled)
        if not function:
            function = ir.Function(self.module, func_type, name=mangled)
        block = function.append_basic_block('entry')
        builder = ir.IRBuilder(block)
        previous_builder = self.builder
        previous_func = self.func
        self.builder = builder
        self.func = function
        self.local_vars = {}
        args_iter = iter(function.args)
        this_arg = next(args_iter)
        self.local_vars['this'] = this_arg
        for name, llvm_arg in zip(param_names, args_iter):
            a_ptr = builder.alloca(llvm_arg.type)
            builder.store(llvm_arg, a_ptr)
            self.local_vars[name] = a_ptr
        if method_name == '_init':
            fields = self.compiler_data.class_bodies[class_name]['fields']
            for i, (tag, ftype, fname, init_expr) in enumerate(fields):
                field_ptr = self.builder.gep(
                    this_arg,
                    [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)]
                )
                if i < len(param_names):
                    param_val = self.builder.load(self.local_vars[param_names[i]])
                    if field_ptr.type.pointee != param_val.type:
                        param_val = self.builder.bitcast(param_val, field_ptr.type.pointee)
                    builder.store(param_val, field_ptr)
                elif init_expr is not None:
                    value = self.compile_expression(init_expr)
                    if field_ptr.type.pointee != value.type:
                        value = self.builder.bitcast(value, field_ptr.type.pointee)
                    builder.store(value, field_ptr)
        for statement in statements:
            self.compile_statement(statement)
        if return_ir != ir.VoidType() and not builder.block.is_terminated:
            builder.ret(ir.Constant(return_ir, 0))
        elif return_ir == ir.VoidType() and not builder.block.is_terminated:
            builder.ret_void()
        self.builder = previous_builder
        self.func = previous_func

    def compile_statement(self, statement:tuple) -> None:
        kind : str = statement[0]
        match kind:
            case 'expression':
                self.compile_expression(statement[1])
            case 'return':
                print(statement)
                return_value = self.compile_expression(statement[1])
                self.builder.ret(return_value)
            case 'return_void':
                if self.current_function_return_type != 'void':
                    raise TypeError('Void return used in non-void function')
                self.builder.ret_void()
            case 'declare':
                variable_type_str, variable_name, value_expr = statement[1], statement[2], statement[3]
                value = self.compile_expression(value_expr)
                match variable_type_str:
                    case 'int':
                        ptr : ir.AllocaInstr = self.builder.alloca(TypeEnum.int32, name=variable_name)
                        self.safe_store(value, ptr)
                        self.variables[variable_name] = (ptr, value.type)
                    case 'bool':
                        ptr : ir.AllocaInstr = self.builder.alloca(TypeEnum.boolean, name=variable_name)
                        self.safe_store(value, ptr)
                        self.variables[variable_name] = (ptr, value.type)
                    case 'string':
                        ptr : ir.AllocaInstr = self.builder.alloca(TypeEnum.string, name=variable_name)
                        self.safe_store(value, ptr)
                        self.variables[variable_name] = (ptr, value.type)
                    case _:
                        raise NotImplementedError(f'Unsupported type: {variable_type_str}')
            case 'declare_custom':
                type_name, var_name, constructor_call = statement[1], statement[2], statement[3]
                if constructor_call[0] == 'call' and constructor_call[1] == type_name:
                    obj_pointer = self.compile_expression(('object_creation', type_name, constructor_call[2]))
                else:
                    obj_pointer = self.compile_expression(constructor_call)
                self.variables[var_name] = (obj_pointer, obj_pointer.type)
            case 'if_chain':
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
            case 'for_in':
                var_type, var_name, list_name, body = statement[1], statement[2], statement[3], statement[4]
                index_pointer : ir.AllocaInstr = self.builder.alloca(TypeEnum.int32, name=f"{var_name}_index")
                self.safe_store(ir.Constant(TypeEnum.int32, 0), index_pointer)
                conditional_block : ir.Block = self.func.append_basic_block(f'for_conditional_{self.loop_counter}')
                body_block : ir.Block = self.func.append_basic_block(f'for_body_{self.loop_counter}')
                end_block : ir.Block = self.func.append_basic_block(f'for_end_{self.loop_counter}')
                continue_block : ir.Block = self.func.append_basic_block(f'for_continue_{self.loop_counter}')
                self.loop_counter += 1
                self.builder.branch(conditional_block)
                self.builder.position_at_start(conditional_block)
                list_pointer : ir.AllocaInstr = self.variables[list_name][0]
                index_value : ir.LoadInstr = self.builder.load(index_pointer)
                list_len : ir.CallInstr = self.call_list_len(list_pointer)
                cond : ir.ICMPInstr = self.builder.icmp_signed('<', index_value, list_len)
                self.builder.cbranch(cond, body_block, end_block)
                self.builder.position_at_start(body_block)
                element_pointer : ir.CallInstr = self.call_list_get(list_pointer, index_value)
                element_type : ir.Type = string_to_ir(var_type)
                if element_type.is_pointer:
                    element_value = self.builder.bitcast(element_pointer, element_type)
                else:
                    casted_ptr = self.builder.bitcast(
                        element_pointer,
                        element_type.as_pointer()
                    )
                    element_value = self.builder.load(casted_ptr)
                variable_pointer = self.builder.alloca(string_to_ir(var_type), name=var_name)
                self.safe_store(element_value, variable_pointer)
                self.variables[var_name] = (variable_pointer, string_to_ir(var_type))
                self.loop_continue_stack.append(continue_block)
                self.loop_break_stack.append(end_block)
                for for_in_statement in body:
                    self.compile_statement(for_in_statement)
                self.loop_continue_stack.pop()
                self.loop_break_stack.pop()
                self.builder.branch(continue_block)
                self.builder.position_at_start(continue_block)
                new_index = self.builder.add(index_value, ir.Constant(TypeEnum.int32, 1))
                self.safe_store(new_index, index_pointer)
                self.builder.branch(conditional_block)
                self.builder.position_at_start(end_block)
            case 'while':
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
            case 'declare_list':
                element_type, name, expression = statement[1], statement[2], statement[3]
                if expression[0] == 'list_literal':
                    elements = [self.compile_expression(e) for e in expression[1]]
                    llvm_element_type : ir.Type = string_to_ir(element_type)
                    heap_pointer : ir.Value = self.allocate_and_copy_array(elements, llvm_element_type)
                    create_fn_type : ir.FunctionType = ir.FunctionType(
                        self.list_struct_type.as_pointer(),
                        [TypeEnum.int8.as_pointer(), TypeEnum.int32, TypeEnum.int32, TypeEnum.boolean]
                    )
                    create_fn : ir.Function = self.module.globals.get('core_list_create_from')
                    if create_fn is None:
                        create_fn = ir.Function(self.module, create_fn_type, name='core_list_create_from')
                    element_size_bytes : int = self.get_abi_size_from_ir_type(llvm_element_type)
                    list_pointer = self.builder.call(
                        create_fn,
                        [
                            heap_pointer,
                            ir.Constant(TypeEnum.int32, len(elements)),
                            ir.Constant(TypeEnum.int32, element_size_bytes),
                            ir.Constant(TypeEnum.boolean, int(llvm_element_type.is_pointer))
                        ]
                    )
                    self.variables[name] = (list_pointer, self.list_struct_type.as_pointer())
                else:
                    value : ir.CallInstr = self.compile_expression(expression)
                    self.variables[name] = (value, value.type)
            case 'break':
                self.builder.branch(self.loop_break_stack[-1])
            case 'continue':
                self.builder.branch(self.loop_continue_stack[-1])
            case 'assign':
                target : tuple = statement[1]
                expr : tuple = statement[2]
                value : ir.Value = self.compile_expression(expr)
                if isinstance(target, str):
                    if target not in self.variables:
                        raise NameError(f'Variable {target} is not declared')
                    pointer : ir.AllocaInstr = self.variables[target][0]
                    if pointer.type.pointee != value.type:
                        value = self.builder.bitcast(value, pointer.type.pointee)
                    self.safe_store(value, pointer)
                elif target[0] == 'get_attr' and target[1][0] == 'this':
                    field_ptr = self.get_this_field_pointer(target[2])
                    if field_ptr.type.pointee != value.type:
                        value = self.builder.bitcast(value, field_ptr.type.pointee)
                    self.safe_store(value, field_ptr)
                else:
                    raise NotImplementedError(f'Assignment target {target} not implemented')
            case 'class':
                self.compile_class(statement)

    def compile_expression(self, expression:tuple) -> Union[ir.Value, Any]:
        kind : str = expression[0]
        match kind:
            case 'call':
                name = expression[1]
                args = expression[2]
                arg_values = [self.compile_expression(arg) for arg in args]
                if name in self.compiler_data.class_bodies:
                    info = self.compiler_data.class_bodies[name]
                    obj_type = info['struct']
                    obj_pointer : ir.AllocaInstr = self.builder.alloca(obj_type)
                    init_name : str = '_init'
                    init_func_name : str = f'{name}_{init_name}'
                    init_func = self.module.globals.get(init_func_name)
                    if init_func is None:
                        arg_types_llvm = [obj_pointer.type] + [arg.type for arg in arg_values]
                        init_func_type = ir.FunctionType(ir.VoidType(), arg_types_llvm)
                        init_func = ir.Function(self.module, init_func_type, name=init_func_name)
                    self.builder.call(init_func, [obj_pointer] + arg_values)
                    return obj_pointer
                else:
                    func : ir.Function = self.module.globals.get(name)
                    if not func:
                        func_type : ir.FunctionType = ir.FunctionType(int32, arg_values)
                        func : ir.Function = ir.Function(self.module, func_type, name=name)
                    return self.builder.call(func, arg_values)
            case 'call_method':
                obj_name, method, args = expression[1], expression[2], expression[3]
                full_name = f'{obj_name}.{method}'
                if obj_name in self.variables:
                    obj_pointer, obj_type = self.variables[obj_name]
                    class_name = getattr(getattr(obj_type, 'pointee', None), 'name', None)
                    if not class_name:
                        raise RuntimeError(f'Object {obj_name} does not have a valid class type')
                    mangled_name: str = f'{class_name}_{method}'
                    func = self.module.globals.get(mangled_name)
                    if not func:
                        raise NameError(f'Method {mangled_name} not found in module')
                    call_args = [obj_pointer] + [self.compile_expression(arg) for arg in args]
                    return self.builder.call(func, call_args)
                elif full_name in self.extern_functions:
                    overloads = self.extern_functions[full_name]
                    arg_vals = [self.compile_expression(arg) for arg in args]
                    arg_types = tuple(ir_to_string(arg.type) for arg in arg_vals)
                    if arg_types not in overloads:
                        raise TypeError(f'Function {full_name} has no overload matching argument types {arg_types}')
                    llvm_name, return_type_id = overloads[arg_types]
                    return_type: ir.Type = string_to_ir(return_type_id)
                    if return_type_id.startswith('list'):
                        return_type = self.list_struct_type.as_pointer()
                    func: Optional[ir.Function] = self.module.globals.get(llvm_name)
                    if not func:
                        func_type: ir.FunctionType = ir.FunctionType(return_type, [arg.type for arg in arg_vals])
                        func = ir.Function(self.module, func_type, name=llvm_name)
                    return self.builder.call(func, arg_vals)
                else:
                    raise NameError(f'Undefined object or module: {obj_name}')
            case 'call_method_':
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
            case 'int':
                return ir.Constant(TypeEnum.int32, expression[1])
            case 'float':
                return ir.Constant(TypeEnum.float32, expression[1])
            case 'string':
                data : bytearray = bytearray(expression[1].encode('utf8') + b'\0')
                str_type : ir.ArrayType = ir.ArrayType(ir.IntType(8), len(data))
                global_str : ir.GlobalVariable = ir.GlobalVariable(self.module, str_type, name=f'string_{len(self.module.global_values)}')
                global_str.global_constant = True
                global_str.initializer = ir.Constant(str_type, data)
                pointer = self.builder.bitcast(global_str, TypeEnum.string)
                return pointer
            case 'binop':
                operator, left_part, right_part = expression[1], expression[2], expression[3]
                left_value = self.compile_expression(left_part)
                right_value = self.compile_expression(right_part)
                match operator:
                    case '==':
                        if left_value.type == TypeEnum.string and right_value.type == TypeEnum.string:
                            llvm_name: str = 'core_string_equal'
                            func : ir.Function = self.module.globals.get(llvm_name)
                            if not func:
                                func = ir.Function(self.module, ir.FunctionType(TypeEnum.boolean, [TypeEnum.string, TypeEnum.string]), name=llvm_name)
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
                                func = ir.Function(self.module, ir.FunctionType(TypeEnum.string, [TypeEnum.string, TypeEnum.string]), name=llvm_name)
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
            case 'var':
                var_name : str = expression[1]
                if var_name in self.local_vars:
                    ptr : ir.AllocaInstr = self.local_vars[var_name]
                    return self.builder.load(ptr)
                elif var_name in self.variables:
                    ptr : ir.AllocaInstr = self.variables[var_name][0]
                    return self.builder.load(ptr)
                else:
                    raise NameError(f'Undefined variable: {var_name}')
            case 'bool':
                return ir.Constant(ir.IntType(1), 1 if expression[1] else 0)
            case 'object_creation':
                _, class_name, arguments = expression
                info = self.compiler_data.class_bodies.get(class_name)
                if not info:
                    raise NameError(f'Unknown class {class_name}')
                struct_type : ir.IdentifiedStructType = info['struct']
                obj_pointer : ir.AllocaInstr = self.builder.alloca(struct_type)
                init_name : str = '_init'
                ctor_name = f'{class_name}_{init_name}'
                ctor = self.module.globals.get(ctor_name)
                for idx, (tag, ftype, fname, init_expr) in enumerate(info['fields']):
                    if init_expr is not None and not ctor:
                        field_ptr = self.builder.gep(obj_pointer, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), idx)])
                        value: ir.Value = self.compile_expression(init_expr)
                        if field_ptr.type.pointee != value.type:
                            value = self.builder.bitcast(value, field_ptr.type.pointee)
                        self.safe_store(value, field_ptr)
                if ctor:
                    arg_values = [self.compile_expression(arg) for arg in arguments]
                    self.builder.call(ctor, [obj_pointer] + arg_values)
                return obj_pointer
            case 'get_attr':
                obj_expr, field_name = expression[1], expression[2]
                if obj_expr == ('this',):
                    return self.compile_this_access(field_name)
                else:
                    obj_pointer, obj_type = self.variables[obj_expr[0]]
                    class_name = getattr(getattr(obj_type, 'pointee', None), 'name', None)
                    if not class_name:
                        raise RuntimeError(f'Object {obj_expr} does not have a valid class type')
                    struct_type = self.compiler_data.class_bodies[class_name]['struct']
                    idx = next(i for i, f in enumerate(self.compiler_data.class_bodies[class_name]['fields']) if f[2] == field_name)
                    field_ptr = self.builder.gep(obj_pointer, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), idx)])
                    return self.builder.load(field_ptr)
            case _:
                raise NotImplementedError(f'Expresion kind {kind} not implemented')

    def add_c_main(self):
        func_type : ir.FunctionType = ir.FunctionType(TypeEnum.int32, [])
        main_fn : ir.Function = ir.Function(self.module, func_type, name='main')
        block : ir.Block = main_fn.append_basic_block(name='entry')
        builder : ir.IRBuilder = ir.IRBuilder(block)
        exec_fn = self.module.get_global('_exec')
        return_value = builder.call(exec_fn, [])
        builder.ret(return_value)

