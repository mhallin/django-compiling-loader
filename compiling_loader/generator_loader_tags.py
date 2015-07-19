import ast

from django.template import loader_tags

from .generator import generate_expression, generate_nodelist
from . import util


class BlockWrapper:
    def __init__(self, context, block_name):
        self.context = context
        self.block_name = block_name

    def super(self):
        block_context = self.context.render_context.get(
            loader_tags.BLOCK_CONTEXT_KEY)

        if block_context is None:
            raise AttributeError(
                'No block context; maybe invalid block.super call?')

        block = block_context.get_block(self.block_name)

        if block is None:
            return ''

        return block(self.context)


def _block_method_name(name):
    return 'block_render_{}'.format(name)


def _emit_block_render_method(node, state):
    body = generate_nodelist(node.nodelist, state)

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

    # with context.push():
    #    if block_context is not None:
    #        block = block_context.pop(name)
    #    <body>
    #    if block_context is not None:
    #        block_context.push(name, block)
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
        body=[
            ast.If(
                test=ast.Compare(
                    left=ast.Name(id=block_context_var, ctx=ast.Load()),
                    ops=[ast.IsNot()],
                    comparators=[ast.NameConstant(value=None)]),
                body=[
                    ast.Assign(
                        targets=[ast.Name(id=block_var, ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(
                                    id=block_context_var,
                                    ctx=ast.Load()),
                                attr='pop',
                                ctx=ast.Load()),
                            args=[ast.Str(s=node.name)],
                            keywords=[])),
                ],
                orelse=[]),
        ]
        + body
        + [
            ast.If(
                test=ast.Compare(
                    left=ast.Name(id=block_context_var, ctx=ast.Load()),
                    ops=[ast.IsNot()],
                    comparators=[ast.NameConstant(value=None)]),
                body=[
                    ast.Expr(value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(
                                id=block_context_var,
                                ctx=ast.Load()),
                            attr='push',
                            ctx=ast.Load()),
                        args=[
                            ast.Str(s=node.name),
                            ast.Name(id=block_var, ctx=ast.Load()),
                        ],
                        keywords=[])),
                ],
                orelse=[]),
        ])

    state.add_render_function(
        [block_context_assign, with_context_push],
        _block_method_name(node.name))


@generate_expression.register(loader_tags.BlockNode)
def _generate_block_node(node, state):
    _emit_block_render_method(node, state)

    block_context_var = state.new_local_var()
    block_var = state.new_local_var()
    result_var = state.new_local_var()

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

    # with context.push():
    #     context['block'] = BlockWrapper(context, name)
    #     result = block()
    with_block = ast.With(
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
        body=[
            ast.Assign(
                targets=[
                    ast.Subscript(
                        value=state.context_expr,
                        slice=ast.Index(value=ast.Str(s='block')),
                        ctx=ast.Store())
                ],
                value=ast.Call(
                    func=state.add_import(
                        'compiling_loader.generator_loader_tags',
                        'BlockWrapper'),
                    args=[
                        state.context_expr,
                        ast.Str(s=node.name),
                    ],
                    keywords=[])),
            ast.Assign(
                targets=[
                    ast.Name(id=result_var, ctx=ast.Store()),
                ],
                value=ast.Call(
                    func=ast.Name(id=block_var, ctx=ast.Load()),
                    args=[state.context_expr],
                    keywords=[])),
        ])

    # result
    result_var_load = util.copy_location(
        ast.Name(id=result_var, ctx=ast.Load()),
        node)

    preamble = [block_context_assign, block_assign, with_block]

    return util.copy_location(preamble, node), result_var_load


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

    preamble = [block_context_insert, block_context_assign, add_blocks_call]

    return util.copy_location(preamble, node), \
        util.copy_location(parent_render, node)


@generate_expression.register(loader_tags.IncludeNode)
def _generate_include_node(node, state):
    template_var = state.new_local_var()
    values_var = state.new_local_var()

    # template = node.template.resolve(context)
    template_assign = ast.Assign(
        targets=[ast.Name(id=template_var, ctx=ast.Store())],
        value=ast.Call(
            func=ast.Attribute(
                value=state.add_ivar(node.template),
                attr='resolve',
                ctx=ast.Load()),
            args=[state.context_expr],
            keywords=[]))

    # if not callable(getattr(template, 'render', None)):
    #     template = get_template(template)
    template_lookup = ast.If(
        test=ast.UnaryOp(
            op=ast.Not(),
            operand=ast.Call(
                func=ast.Name(id='callable', ctx=ast.Load()),
                args=[
                    ast.Call(
                        func=ast.Name(id='getattr', ctx=ast.Load()),
                        args=[
                            ast.Name(id=template_var, ctx=ast.Load()),
                            ast.Str(s='render'),
                            ast.NameConstant(value=None),
                        ],
                        keywords=[]),
                ],
                keywords=[])),
        body=[
            ast.Assign(
                targets=[ast.Name(id=template_var, ctx=ast.Store())],
                value=ast.Call(
                    func=state.add_import(
                        'django.template.loader', 'get_template'),
                    args=[ast.Name(id=template_var, ctx=ast.Load())],
                    keywords=[])),
        ],
        orelse=[])

    # values = {
    #     name: var.resolve(context),
    #     ...
    # }
    values_kvs = [
        (
            ast.Str(s=name),
            util.generate_resolve_variable(var, state, False)
        )
        for name, var in node.extra_context.items()
    ]

    values_assign = ast.Assign(
        targets=[ast.Name(id=values_var, ctx=ast.Store())],
        value=ast.Dict(
            keys=[k for k, _ in values_kvs],
            values=[v for _, v in values_kvs]))

    preamble = [template_assign, template_lookup, values_assign]

    if node.isolated_context:
        # template.render(context.new(values))
        result_expr = ast.Call(
            func=ast.Attribute(
                value=ast.Name(id=template_var, ctx=ast.Load()),
                attr='render',
                ctx=ast.Load()),
            args=[
                ast.Call(
                    func=ast.Attribute(
                        value=state.context_expr,
                        attr='new',
                        ctx=ast.Load()),
                    args=[ast.Name(id=values_var, ctx=ast.Load())],
                    keywords=[]),
            ],
            keywords=[])
    else:
        result_var = state.new_local_var()

        # with context.push(**value):
        #     result = template.render(context)
        with_block = ast.With(
            items=[
                ast.withitem(
                    context_expr=ast.Call(
                        func=ast.Attribute(
                            value=state.context_expr,
                            attr='push',
                            ctx=ast.Load()),
                        args=[],
                        keywords=[],
                        kwargs=ast.Name(id=values_var, ctx=ast.Load())),
                    optional_vars=None),
            ],
            body=[
                ast.Assign(
                    targets=[ast.Name(id=result_var, ctx=ast.Store())],
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=template_var, ctx=ast.Load()),
                            attr='render',
                            ctx=ast.Load()),
                        args=[state.context_expr],
                        keywords=[]))
            ])

        preamble.append(with_block)

        # result
        result_expr = ast.Name(id=result_var, ctx=ast.Load())

    return util.copy_location(preamble, node), \
        util.copy_location(result_expr, node)
