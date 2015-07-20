import ast
import collections.abc

from . import ast_builder

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

        self.render_methods = {}

    def build_module(self):
        template_class = ast.ClassDef(
            name='CompiledTemplate',
            bases=[],
            keywords=[],
            starargs=None,
            kwargs=None,
            decorator_list=[],
            body=list(self.render_methods.values()),
        )

        module = ast.Module(
            body=self.imports + self.helper_functions + [template_class],
            lineno=1,
            col_offset=0)

        ast.fix_missing_locations(module)

        return module

    def make_function_def(self, body, name):
        return ast.FunctionDef(
            name=name,
            body=body,
            args=ast.arguments(
                args=[
                    ast.arg(arg='self'),
                    ast.arg(arg=CONTEXT_ARG_NAME),
                ],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]),
            decorator_list=[],
        )

    def make_render_function_def(self, body, name):
        buf_var = ast_builder.new_local_var(self, 'buf')

        buf_assign = ast_builder.build_stmt(
            self,
            lambda b: b.assign(buf_var, b.list([])))

        emit_assign = ast_builder.build_stmt(
            self,
            lambda b: b.assign(b.emit, buf_var.append))

        result_return = ast_builder.build_stmt(
            self,
            lambda b: b.return_(b.str('').join(buf_var)))

        return self.make_function_def(
            [buf_assign, emit_assign] + body + [result_return],
            name)

    def add_render_function(self, body, name):
        assert name not in self.render_methods

        self.render_methods[name] = self.make_render_function_def(body, name)

    def add_helper_function(self, body):
        name = '$helper{}$'.format(self._helper_function_counter)
        self._helper_function_counter += 1

        function_def = self.make_function_def(body, name)

        self.helper_functions.append(function_def)

        return ast.Call(
            func=ast.Name(
                id=name,
                ctx=ast.Load()),
            args=[
                ast.Name(id='self', ctx=ast.Load()),
                ast.Name(id=CONTEXT_ARG_NAME, ctx=ast.Load()),
            ],
            keywords=[])

    def add_ivar(self, value):
        if isinstance(value, collections.abc.Hashable) \
                and value in self._ivar_values:
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

    def new_local_var(self, name):
        key = '$local{}_{}$'.format(self._local_var_counter, name)
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
