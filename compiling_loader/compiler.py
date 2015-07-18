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
        return self._callback(self, context)


def convert_template(template, state):
    body = generator.generate_nodelist(template.nodelist, state)

    f = state.make_render_function_def(body, name='render')

    m = ast.copy_location(ast.Module(), body[0])
    m.body = (state.imports
              + state.helper_functions
              + [f])

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
