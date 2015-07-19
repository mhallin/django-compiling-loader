import ast

from django.template import loader_tags

from .generator import generate_expression, generate_nodelist


def _block_method_name(name):
    return 'block_render_{}'.format(name)


def _emit_block_render_method(node, state):
    body = generate_nodelist(node.nodelist, state)

    # with context.push():
    #    <body>
    with_context_push = ast.With(
        items=[
            ast.withitem(
                context_expr=ast.Call(
                    func=ast.Attribute(
                        value=state.context_expr,
                        attr='push',
                        ctx=ast.Load()),
                    args=[],
                    keywords=[]),
                optional_vars=None),
        ],
        body=body)

    state.add_render_function(
        [with_context_push],
        _block_method_name(node.name))


@generate_expression.register(loader_tags.BlockNode)
def _generate_block_node(node, state):
    _emit_block_render_method(node, state)

    block_context_var = state.new_local_var()
    block_var = state.new_local_var()

    # block_context = context.render_context.get(BLOCK_CONTEXT_KEY)
    block_context_assign = ast.Assign(
        targets=[ast.Name(id=block_context_var, ctx=ast.Store())],
        value=ast.Call(
            func=ast.Attribute(
                value=ast.Attribute(
                    value=state.context_expr,
                    attr='render_context',
                    ctx=ast.Load()),
                attr='get',
                ctx=ast.Load()),
            args=[ast.Str(s=loader_tags.BLOCK_CONTEXT_KEY)],
            keywords=[]))

    # if block_context is not None:
    #     block_context.add_blocks({ name: self.render_block_<name> })
    #     block = block_context.get_block(name)
    # else:
    #     block = self.render_block_<name>
    block_assign = ast.If(
        test=ast.Compare(
            left=ast.Name(id=block_context_var, ctx=ast.Load()),
            ops=[ast.IsNot()],
            comparators=[ast.NameConstant(value=None)]),
        body=[
            ast.Expr(value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id=block_context_var, ctx=ast.Load()),
                    attr='add_blocks',
                    ctx=ast.Load()),
                args=[
                    ast.Dict(
                        keys=[ast.Str(s=node.name)],
                        values=[
                            ast.Attribute(
                                value=ast.Name(id='self', ctx=ast.Load()),
                                attr=_block_method_name(node.name),
                                ctx=ast.Load()),
                        ]),
                ],
                keywords=[])),
            ast.Assign(
                targets=[ast.Name(id=block_var, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id=block_context_var, ctx=ast.Load()),
                        attr='get_block',
                        ctx=ast.Load()),
                    args=[ast.Str(s=node.name)],
                    keywords=[])),
        ],
        orelse=[
            ast.Assign(
                targets=[ast.Name(id=block_var, ctx=ast.Store())],
                value=ast.Attribute(
                    value=ast.Name(id='self', ctx=ast.Load()),
                    attr=_block_method_name(node.name),
                    ctx=ast.Load())),
        ])

    # block()
    block_render_call = ast.Call(
        func=ast.Name(id=block_var, ctx=ast.Load()),
        args=[state.context_expr],
        keywords=[])

    return [block_context_assign, block_assign], block_render_call


@generate_expression.register(loader_tags.ExtendsNode)
def _generate_extends_node(node, state):
    for block in node.blocks.values():
        _emit_block_render_method(block, state)

    # if BLOCK_CONTEXT_KEY in context.render_context:
    #     context.render_context[BLOCK_CONTEXT_KEY] = BlockContext()
    block_context_insert = ast.If(
        test=ast.Compare(
            left=ast.Str(s=loader_tags.BLOCK_CONTEXT_KEY),
            ops=[ast.NotIn()],
            comparators=[
                ast.Attribute(
                    value=state.context_expr,
                    attr='render_context',
                    ctx=ast.Load())
            ]),
        body=[
            ast.Assign(
                targets=[
                    ast.Subscript(
                        value=ast.Attribute(
                            value=state.context_expr,
                            attr='render_context',
                            ctx=ast.Load()),
                        slice=ast.Index(
                            value=ast.Str(s=loader_tags.BLOCK_CONTEXT_KEY)),
                        ctx=ast.Store())
                ],
                value=ast.Call(
                    func=state.add_import(
                        'django.template.loader_tags',
                        'BlockContext'),
                    args=[],
                    keywords=[])),
        ],
        orelse=[])

    # block_context variable
    block_context_var_name = state.new_local_var()

    # block_context = context.render_context[BLOCK_CONTEXT_KEY]
    block_context_assign = ast.Assign(
        targets=[
            ast.Name(id=block_context_var_name, ctx=ast.Store()),
        ],
        value=ast.Subscript(
            value=ast.Attribute(
                value=state.context_expr,
                attr='render_context',
                ctx=ast.Load()),
            slice=ast.Index(
                value=ast.Str(s=loader_tags.BLOCK_CONTEXT_KEY)),
            ctx=ast.Load()))

    # [ (name, self.render_block_<name>) for name in node.blocks.keys() ]
    block_render_kvs = [
        (
            ast.Str(s=name),
            ast.Attribute(
                value=ast.Name(id='self', ctx=ast.Load()),
                attr=_block_method_name(name),
                ctx=ast.Load())
        )
        for name in node.blocks.keys()
    ]

    # block_context.add_blocks(
    #     { name: self.render_block_<name> for name in node.blocks.keys() }
    # )
    add_blocks_call = ast.Expr(value=ast.Call(
        func=ast.Attribute(
            value=ast.Name(id=block_context_var_name, ctx=ast.Load()),
            attr='add_blocks',
            ctx=ast.Load()),
        args=[
            ast.Dict(
                keys=[k for k, v in block_render_kvs],
                values=[v for k, v in block_render_kvs])
        ],
        keywords=[]))

    # node.get_parent().render(context)
    parent_render = ast.Call(
        func=ast.Attribute(
            value=ast.Call(
                func=ast.Attribute(
                    value=state.add_ivar(node),
                    attr='get_parent',
                    ctx=ast.Load()),
                args=[state.context_expr],
                keywords=[]),
            attr='render',
            ctx=ast.Load()),
        args=[state.context_expr],
        keywords=[])

    return [
        block_context_insert,
        block_context_assign,
        add_blocks_call], \
        parent_render
