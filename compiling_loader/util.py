import ast

from django.template.base import VariableDoesNotExist

from . import ast_builder


def copy_location(dest_node, src_node):
    if isinstance(dest_node, (tuple, list)):
        return [copy_location(n, src_node) for n in dest_node]

    if hasattr(src_node, 'source'):
        _, (lineno, col_offset) = src_node.source
    else:
        lineno = 0
        col_offset = 0

    dest_node.lineno = lineno
    dest_node.col_offset = col_offset

    return dest_node


def wrap_emit_expr(ns, state):
    preamble, result = ns

    stmts = []

    for n in preamble + ([result] if result else []):
        if isinstance(n, ast.stmt):
            stmts.append(n)
        else:
            stmts.append(ast_builder.build_stmt(
                state,
                lambda b: b.emit(n)))

    return stmts


def generate_resolve_variable(variable,
                              state,
                              ignore_errors,
                              fallback_value=None):
    if ignore_errors:
        if fallback_value is not None:
            return ast_builder.build_expr(
                state,
                lambda b: b[try_resolve](
                    b.ivars[variable], b.context, fallback_value))
        else:
            return ast_builder.build_expr(
                state,
                lambda b: b[try_resolve](b.ivars[variable], b.context))
    else:
        return ast_builder.build_expr(
            state,
            lambda b: b.ivars[variable].resolve(b.context))


def try_resolve(var, context, or_else=''):
    try:
        return var.resolve(context)
    except VariableDoesNotExist:
        return or_else
