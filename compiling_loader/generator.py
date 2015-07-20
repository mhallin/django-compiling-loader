import ast

from functools import singledispatch

from django.template import base

from . import ast_builder, util, generator_flt_expr, html


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

    return [], util.copy_location(
        ast_builder.build_expr(
            compiler_state,
            lambda b: b[html.fast_render_value_in_context](output, b.context)),
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
    render_call = util.copy_location(
        ast_builder.build_expr(
            compiler_state,
            lambda b: b.ivars[node].render(b.context)),
        node)

    return [], render_call
