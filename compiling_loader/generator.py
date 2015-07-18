import ast

from functools import singledispatch

from django.template import base

from . import util, generator_flt_expr


@singledispatch
def generate_expression(node, compiler_state):
    return generate_fallback(node, compiler_state)


@generate_expression.register(base.TextNode)
def _generate_text_node(node, compiler_state):
    return [], util.copy_location(
        ast.Str(s=node.s),
        node
    )


@generate_expression.register(base.VariableNode)
def _generate_variable_node(node, compiler_state):
    filter_expression = node.filter_expression

    output = generator_flt_expr.generate_filter_expression(
        filter_expression,
        compiler_state)

    render_value_func_name = compiler_state.add_import(
        'django.template.base', 'render_value_in_context')

    return [], util.copy_location(
        ast.Call(
            func=render_value_func_name,
            args=[output, compiler_state.context_expr],
            keywords=[]),
        node)


def generate_nodelist(nodelist, compiler_state):
    stmt_lists = [
        util.wrap_emit_expr(
            generate_expression(n, compiler_state),
            compiler_state)
        for n in nodelist
    ]
    return [
        stmt
        for stmt_list in stmt_lists
        for stmt in stmt_list
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

    return [], render_call
