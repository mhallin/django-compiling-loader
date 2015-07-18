import ast

from django.template import loader_tags

from .generator import generate_expression, generate_nodelist


@generate_expression.register(loader_tags.BlockNode)
def _generate_block_node(node, state):
    block_method_name = 'render_block_' + node.name

    body = generate_nodelist(node.nodelist, state)

    state.add_render_function(body, block_method_name)

    return ast.Call(
        func=ast.Attribute(
            value=ast.Name(id='self', ctx=ast.Load()),
            attr=block_method_name,
            ctx=ast.Load()
        ),
        args=[state.context_expr],
        keywords=[])
