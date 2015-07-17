import ast

from functools import singledispatch

from django.template.base import TextNode

from . import util


@singledispatch
def generate_expression(node, compiler_state):
    return generate_fallback(node, compiler_state)


@generate_expression.register(TextNode)
def _(node, compiler_state):
    return util.copy_location(
        ast.Str(s=node.s),
        node
    )


def generate_nodelist(nodelist, compiler_state):
    return [
        util.wrap_emit_expr(
            generate_expression(n, compiler_state),
            compiler_state)
        for n in nodelist
    ]


def generate_fallback(node, compiler_state):
    render_attr = ast.Attribute(
        value=compiler_state.add_ivar(node),
        attr='render',
        ctx=ast.Load())

    render_call = util.copy_location(
        ast.Call(
            func=render_attr,
            args=[compiler_state.context_expr],
            keywords=[]),
        node)

    return render_call
