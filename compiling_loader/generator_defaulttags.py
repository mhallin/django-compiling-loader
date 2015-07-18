import ast

from django.template import defaulttags

from .generator import generate_expression, generate_nodelist
from . import util


def _generate_if_condition(condition, state):
    return ast.Call(
        func=ast.Attribute(
            value=state.add_ivar(condition),
            attr='eval',
            ctx=ast.Load()),
        args=[state.context_expr],
        keywords=[])


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

            ast_node.test = _generate_if_condition(condition, state)
            ast_node.body = generate_nodelist(nodelist, state)
        else:
            ast_node.orelse = generate_nodelist(nodelist, state)

    print(ast.dump(ast_node))

    return util.copy_location(orig_ast_node, node)
