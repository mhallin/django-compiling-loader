import os.path

from . import generator, compiler_state


def convert_template(template, state):
    body = generator.generate_nodelist(template.nodelist, state)

    state.add_render_function(body, name='render')

    module = state.build_module()

    return module


def compile_template(template):
    origin_name = (os.path.basename(template.origin.name)
                   if template.origin else '<unknown>')

    state = compiler_state.CompilerState()
    ast_mod = convert_template(template, state)
    code_mod = compile(ast_mod, origin_name, 'exec')

    g = {}
    exec(code_mod, g, g)

    instance = g['CompiledTemplate']()

    for key, val in state.ivars.items():
        setattr(instance, key, val)

    return instance
