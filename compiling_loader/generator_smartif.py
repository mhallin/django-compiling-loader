import ast

from django.template import defaulttags

from . import generator_flt_expr, ast_builder

OPERATORS = {
    'or': lambda x, y: ast.BoolOp(op=ast.Or(), values=[x, y]),
    'and': lambda x, y: ast.BoolOp(op=ast.And(), values=[x, y]),
    'not': lambda x: ast.UnaryOp(op=ast.Not(), operand=x),
    'in': lambda x, y: ast.Compare(left=x, ops=[ast.In()], comparators=[y]),
    'not in': lambda x, y: ast.Compare(
        left=x, ops=[ast.NotIn()], comparators=[y]),
    '=': lambda x, y: ast.Compare(left=x, ops=[ast.Eq()], comparators=[y]),
    '==': lambda x, y: ast.Compare(left=x, ops=[ast.Eq()], comparators=[y]),
    '!=': lambda x, y: ast.Compare(left=x, ops=[ast.NotEq()], comparators=[y]),
    '>': lambda x, y: ast.Compare(left=x, ops=[ast.Gt()], comparators=[y]),
    '>=': lambda x, y: ast.Compare(left=x, ops=[ast.GtE()], comparators=[y]),
    '<': lambda x, y: ast.Compare(left=x, ops=[ast.Lt()], comparators=[y]),
    '<=': lambda x, y: ast.Compare(left=x, ops=[ast.LtE()], comparators=[y]),
}


def generate_condition(condition, state):
    need_try_catch = condition.id in OPERATORS

    cond = _do_generate_condition(condition, state)

    if need_try_catch:
        try_stmt = ast_builder.build_stmt(
            state,
            lambda b: b.try_(
                b.return_(cond),
                b.except_(None, None, b.return_(False))))

        return state.add_helper_function([try_stmt])
    else:
        return cond


def _do_generate_condition(condition, state):
    if isinstance(condition, defaulttags.TemplateLiteral):
        return generator_flt_expr.generate_filter_expression(
            condition.value,
            state,
            fallback_value=ast.NameConstant(value=None))
    if condition.id in OPERATORS:
        return _generate_operator(condition, state)

    raise NotImplementedError('Unknown condition: {}'.format(condition))


def _generate_operator(condition, state):
    op = OPERATORS[condition.id]

    if condition.second is not None:
        return op(
            _do_generate_condition(condition.first, state),
            _do_generate_condition(condition.second, state))
    else:
        return op(
            _do_generate_condition(condition.first, state))
