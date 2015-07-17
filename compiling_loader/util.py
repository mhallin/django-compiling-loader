import ast


def copy_location(dest_node, src_node):
    if hasattr(src_node, 'source'):
        _, (lineno, col_offset) = src_node.source
    else:
        lineno = 0
        col_offset = 0

    dest_node.lineno = lineno
    dest_node.col_offset = col_offset

    return dest_node


def wrap_emit_expr(n, compiler_state):
    if isinstance(n, ast.stmt):
        return n

    emit_call = ast.Call(
        func=compiler_state.emit_expr,
        args=[n],
        keywords=[])

    expr = ast.copy_location(ast.Expr(value=emit_call), n)

    return expr
