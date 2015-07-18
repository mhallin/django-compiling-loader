import ast

from django.template import defaulttags

from .generator import generate_expression, generate_nodelist
from . import util, generator_smartif


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
