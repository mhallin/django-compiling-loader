import ast
import os.path

from . import generator, compiler_state


def convert_template(template, state):
    body = generator.generate_nodelist(template.nodelist, state)

    state.add_render_function(body, name='render')

    module = state.build_module()

    return module


def compile_template(template):
    state = compiler_state.CompilerState()
    ast_mod = convert_template(template, state)
    code_mod = compile(ast_mod, os.path.basename(template.origin.name), 'exec')

    g = {}
    exec(code_mod, g, g)

    instance = g['CompiledTemplate']()

    for key, val in state.ivars.items():
        setattr(instance, key, val)

    return instance
