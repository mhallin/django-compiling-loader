import ast

from django.template.base import VariableDoesNotExist


def copy_location(dest_node, src_node):
    if hasattr(src_node, 'source'):
        _, (lineno, col_offset) = src_node.source
    else:
        lineno = 0
        col_offset = 0

    dest_node.lineno = lineno
    dest_node.col_offset = col_offset

    return dest_node


def wrap_emit_expr(n, state):
    if isinstance(n, ast.stmt):
        return n

    emit_call = ast.Call(
        func=state.emit_expr,
        args=[n],
        keywords=[])

    expr = ast.copy_location(ast.Expr(value=emit_call), n)

    return expr


def generate_resolve_variable(variable,
                              state,
                              ignore_errors,
                              fallback_value=None):
    if ignore_errors:
        fallback_arg = []

        if fallback_value:
            fallback_arg = [fallback_value]

        return ast.Call(
            func=state.add_import('compiling_loader.util', 'try_resolve'),
            args=[
                state.add_ivar_var(variable),
                state.context_expr] + fallback_arg,
            keywords=[])
    else:
        return ast.Call(
            func=ast.Attribute(
                value=state.add_ivar_var(variable),
                attr='resolve',
                ctx=ast.Load()),
            args=[state.context_expr],
            keywords=[])


def try_resolve(var, context, or_else=''):
    try:
        return var.resolve(context)
    except VariableDoesNotExist:
        return or_else
