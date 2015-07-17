import ast

from io import StringIO

from . import generator, compiler_state


class CompiledTemplate(object):
    def __init__(self, callback, state):
        self._callback = callback

        for key, val in state.ivars.items():
            setattr(self, key, val)

    def render(self, context):
        buf = StringIO()

        self._callback(self, buf.write, context)

        return buf.getvalue()


def convert_template(template, state):
    body = generator.generate_nodelist(template.nodelist, state)

    if not body:
        body.append(ast.Pass(lineno=0, col_offset=0))

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
    m.body = [f]

    ast.fix_missing_locations(m)

    print(template.nodelist, ast.dump(f))

    return m, {}


def compile_template(template, name):
    state = compiler_state.CompilerState()
    ast_mod, var_map = convert_template(template, state)
    code_mod = compile(ast_mod, name, 'exec')

    g = {}
    l = {}
    exec(code_mod, g, l)

    return CompiledTemplate(l['render'], state)
