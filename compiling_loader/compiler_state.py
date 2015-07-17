import ast
import collections.abc

EMIT_ARG_NAME = '$emit$'
CONTEXT_ARG_NAME = '$context$'


class CompilerState:
    def __init__(self):
        self._ivar_counter = 0
        self.ivars = {}
        self._ivar_values = {}

        self._local_var_counter = 0
        self._global_var_counter = 0

        self.imports = []
        self._imported_names = {}

    def add_ivar(self, value):
        if value in self._ivar_values:
            key = self._ivar_values[value]
        else:
            key = '$val{}$'.format(self._ivar_counter)
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
