import ast

from . import util


def generate_filter_expression(filter_expression, state):
    result = util.generate_resolve_variable(
        filter_expression.var,
        state,
        ignore_errors=True)

    for func, args in filter_expression.filters:
        result = _generate_filter(func, result, args, state)

    return result


def _generate_filter(func, first_arg, args, state):
    arg_vals = []

    for lookup, arg in args:
        if not lookup:
            arg_vals.append(state.add_ivar(arg))
        else:
            arg_vals.append(util.generate_resolve_variable(
                arg,
                state,
                ignore_errors=False))

    return ast.Call(
        func=state.add_ivar(func),
        args=[first_arg] + arg_vals,
        keywords=[])
