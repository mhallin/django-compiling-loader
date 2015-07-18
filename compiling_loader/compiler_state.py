import ast
import collections.abc

EMIT_ARG_NAME = '$emit$'
CONTEXT_ARG_NAME = '$context$'


class CompilerState:
    def __init__(self):
        self._ivar_counter = 0
        self.ivars = {}
        self._ivar_values = {}

        self._ivar_var_counter = 0
        self._ivar_var_values = {}

        self._local_var_counter = 0
        self._global_var_counter = 0

        self.imports = []
        self._imported_names = {}

        self.helper_functions = []
        self._helper_function_counter = 0

    def add_helper_function(self, body):
        name = '$helper{}$'.format(self._helper_function_counter)
        self._helper_function_counter += 1

        function_def = ast.FunctionDef(
            name=name,
            body=body,
            args=ast.arguments(
                args=[
                    ast.arg(arg='self'),
                    ast.arg(arg=EMIT_ARG_NAME),
                    ast.arg(arg=CONTEXT_ARG_NAME),
                ],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]),
            decorator_list=[],
        )

        self.helper_functions.append(function_def)

        return ast.Call(
            func=ast.Name(
                id=name,
                ctx=ast.Load()),
            args=[
                ast.Name(id='self', ctx=ast.Load()),
                ast.Name(id=EMIT_ARG_NAME, ctx=ast.Load()),
                ast.Name(id=CONTEXT_ARG_NAME, ctx=ast.Load()),
            ],
            keywords=[])

    def add_ivar_var(self, var):
        if isinstance(var, str):
            var_name = var
        else:
            var_name = var.var

        if var_name in self._ivar_var_values:
            key = self._ivar_var_values[var_name]
        else:
            key = 'ivar_var_{}'.format(self._ivar_var_counter)
            self._ivar_var_counter += 1

            self.ivars[key] = var

            self._ivar_var_values[var_name] = key

        return ast.Attribute(
            value=self.self_expr,
            attr=key,
            ctx=ast.Load())

    def add_ivar(self, value):
        if value in self._ivar_values:
            key = self._ivar_values[value]
        else:
            key = 'ivar_{}'.format(self._ivar_counter)
            self._ivar_counter += 1

            self.ivars[key] = value

            if isinstance(value, collections.abc.Hashable):
                self._ivar_values[value] = key

        return ast.Attribute(
            value=self.self_expr,
            attr=key,
            ctx=ast.Load())

    def new_local_var(self):
        key = '$local{}$'.format(self._local_var_counter)
        self._local_var_counter += 1

        return key

    def add_import(self, module, func):
        location = (module, func)

        if location not in self._imported_names:
            key = '$global{}$'.format(self._global_var_counter)
            self._global_var_counter += 1

            self.imports.append(ast.ImportFrom(
                module=module,
                names=[
                    ast.alias(
                        name=func,
                        asname=key),
                ]))
            self._imported_names[location] = key

        return ast.Name(
            id=self._imported_names[location],
            ctx=ast.Load())

    @property
    def context_expr(self):
        return ast.Name(
            id=CONTEXT_ARG_NAME,
            ctx=ast.Load())

    @property
    def emit_expr(self):
        return ast.Name(
            id=EMIT_ARG_NAME,
            ctx=ast.Load())

    @property
    def self_expr(self):
        return ast.Name(
            id='self',
            ctx=ast.Load())
