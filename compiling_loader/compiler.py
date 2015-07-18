import ast
import os.path

from io import StringIO

from django.template.base import VariableDoesNotExist

from . import generator, compiler_state


class CompiledTemplate(object):
    def __init__(self, callback, state):
        self._callback = callback

        for key, val in state.ivars.items():
            setattr(self, key, val)

    def try_resolve(self, var, context, or_else=''):
        try:
            return var.resolve(context)
        except VariableDoesNotExist:
            return or_else

    def render(self, context):
        buf = StringIO()

        self._callback(self, buf.write, context)

        return buf.getvalue()


def convert_template(template, state):
    body = generator.generate_nodelist(template.nodelist, state)

    if not body:
        body.append(ast.Pass(lineno=1, col_offset=1))

    self_arg = ast.copy_location(ast.arg(), body[0])
    self_arg.arg = 'self'

    emit_arg = ast.copy_location(ast.arg(), body[0])
    emit_arg.arg = compiler_state.EMIT_ARG_NAME

    ctx_arg = ast.copy_location(ast.arg(), body[0])
    ctx_arg.arg = compiler_state.CONTEXT_ARG_NAME

    args = ast.copy_location(ast.arguments(), body[0])
    args.args = [self_arg, emit_arg, ctx_arg]
    args.kwonlyargs = []
    args.kw_defaults = []
    args.defaults = []

    f = ast.copy_location(ast.FunctionDef(), body[0])
    f.name = 'render'
    f.body = body
    f.args = args
    f.decorator_list = []

    m = ast.copy_location(ast.Module(), body[0])
    m.body = state.imports + state.helper_functions + [f]

    ast.fix_missing_locations(m)

    return m, {}


def compile_template(template):
    state = compiler_state.CompilerState()
    ast_mod, var_map = convert_template(template, state)
    code_mod = compile(ast_mod, os.path.basename(template.origin.name), 'exec')

    g = {}
    exec(code_mod, g, g)

    class ConcreteCompiledTemplate(CompiledTemplate):
        __slots__ = ['_callback'] + list(state.ivars.keys())

    return CompiledTemplate(g['render'], state)
