import ast

from django.template import defaulttags

from .generator import generate_expression, generate_nodelist
from . import util, generator_flt_expr, generator_smartif, ast_builder


@generate_expression.register(defaulttags.IfNode)
def _generate_if_node(node, state):
    ast_node = ast.If(test=None, body=[], orelse=[])
    orig_ast_node = ast_node

    for condition, nodelist in node.conditions_nodelists:
        if condition is not None:
            if ast_node.test is not None:
                new_ast_node = ast.If(test=None, body=[], orelse=[])
                ast_node.orelse = [new_ast_node]
                ast_node = new_ast_node

            ast_node.test = generator_smartif.generate_condition(
                condition, state)
            ast_node.body = generate_nodelist(nodelist, state)
        else:
            ast_node.orelse = generate_nodelist(nodelist, state)

    return [], util.copy_location(orig_ast_node, node)


@generate_expression.register(defaulttags.ForNode)
def _generate_for_node(node, state):
    parent_loop_var = ast_builder.new_local_var(state, 'parent_loop')
    values_var = ast_builder.new_local_var(state, 'values')
    len_values_var = ast_builder.new_local_var(state, 'len_values')

    asts = []

    # parent_loop = context.get('forloop', {})
    asts.append(ast_builder.build_stmt(
        state,
        lambda b: b.assign(
            parent_loop_var,
            b.context.get('forloop', b.dict({})))))

    # values = <resolve filter expression>(node.sequence, context)
    asts.append(ast_builder.build_stmt(
        state,
        lambda b: b.assign(
            values_var,
            generator_flt_expr.generate_filter_expression(
                node.sequence, state))))

    # if values is None:
    #     values = []
    asts.append(ast_builder.build_stmt(
        state,
        lambda b: b.if_(
            b.is_(values_var, None),
            b.assign(values_var, b.list([])))))

    # if not hasattr(values, '__len__'):
    #    values = list(values)
    asts.append(ast_builder.build_stmt(
        state,
        lambda b: b.if_(
            b.not_(b[hasattr](values_var, '__len__')),
            b.assign(values_var, b[list](values_var)))))

    # len_values = len(values)
    asts.append(ast_builder.build_stmt(
        state,
        lambda b: b.assign(len_values_var, b[len](values_var))))

    # with context.push():
    #     if len_values == 0:
    #         <render_nodelist_empty>
    #     else:
    #         <render_forloop_body>
    asts.append(ast_builder.build_stmt(
        state,
        lambda b: b.with_(
            b.context.push(),
            b.if_(
                len_values_var == 0,
                _generate_for_node_empty_nodelist(node, state),
                _generate_for_node_body(
                    node, state,
                    parent_loop_var, values_var, len_values_var)))))

    return asts, None


def _generate_for_node_empty_nodelist(node, state):
    result = generate_nodelist(node.nodelist_empty, state)

    return result if result else [ast.Pass()]


def enumerate_with_loop_dict(values, len_values, loop_dict):
    for i, item in enumerate(values):
        loop_dict['counter0'] = i
        loop_dict['counter'] = i + 1
        loop_dict['revcounter'] = len_values - i
        loop_dict['revcounter0'] = len_values - i - 1
        loop_dict['first'] = (i == 0)
        loop_dict['last'] = (i == len_values - 1)

        yield i, item


def _generate_for_node_body(node,
                            state,
                            parent_loop_var,
                            values_var,
                            len_values_var):
    asts = []

    loop_dict_var = ast_builder.new_local_var(state, 'loop_dict')
    loop_i_var = ast_builder.new_local_var(state, 'i')
    loop_item_var = ast_builder.new_local_var(state, 'item')

    # <if node.is_reversed>:
    #     values = reversed(values)
    if node.is_reversed:
        asts.append(ast_builder.build_stmt(
            state,
            lambda b: b.assign(values_var, b[reversed](values_var))))

    # loop_dict = context['forloop'] = {'parentloop': parent_loop}
    asts.append(ast_builder.build_stmt(
        state,
        lambda b: b.assign(
            [loop_dict_var, b.context['forloop']],
            b.dict({'parentloop': parent_loop_var}))))

    # for i, item in enumerate_with_loop_dict(values, len_values, loop_dict):
    #     <if len(loopvars) == 1>:
    #         context[loopvar] = item
    #     <else>:
    #         <for li, loopvar in enumerate(node.loopvars)>:
    #             context[loopvar] = item[li]
    #     <generate nodelists>

    # Start with variable unpacking asts:
    if len(node.loopvars) == 1:
        unpack_asts = [ast_builder.build_stmt(
            state,
            lambda b: b.assign(b.context[node.loopvars[0]], loop_item_var))]
    else:
        unpack_asts = [
            ast_builder.build_stmt(
                state,
                lambda b: b.try_(
                    b.assign(b.context[loopvar], loop_item_var[li]),
                    b.except_(b[TypeError], None, b.pass_())))
            for li, loopvar in enumerate(node.loopvars)
        ]

    asts.append(ast_builder.build_stmt(
        state,
        lambda b: b.for_(
            b.tuple([loop_i_var, loop_item_var]),
            b[enumerate_with_loop_dict](
                values_var, len_values_var, loop_dict_var),
            unpack_asts + generate_nodelist(node.nodelist_loop, state))))

    return asts
