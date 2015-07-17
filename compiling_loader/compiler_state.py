import ast

EMIT_ARG_NAME = '$emit$'
CONTEXT_ARG_NAME = '$context$'


class CompilerState:
    def __init__(self):
        self._ivar_counter = 0
        self.ivars = {}

    def add_ivar(self, value):
        key = '$val{}$'.format(self._ivar_counter)
        self._ivar_counter += 1

        self.ivars[key] = value

        return ast.Attribute(
            value=ast.Name(
                id='self',
                ctx=ast.Load()),
            attr=key,
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
