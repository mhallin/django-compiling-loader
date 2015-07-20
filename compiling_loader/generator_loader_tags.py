import ast

from django.conf import settings
from django.template import loader_tags, loader

from .generator import generate_expression, generate_nodelist
from . import util, ast_builder, generator_flt_expr


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

    block_context_var = ast_builder.new_local_var(state, 'block_context')
    block_var = ast_builder.new_local_var(state, 'block')

    # block_context = context.render_context.get(BLOCK_CONTEXT_KEY)
    block_context_assign = ast_builder.build_stmt(
        state,
        lambda b: b.assign(
            block_context_var,
            b.context.render_context.get(loader_tags.BLOCK_CONTEXT_KEY)))

    # with context.push():
    #    if block_context is not None:
    #        block = block_context.pop(name)
    #    <body>
    #    if block_context is not None:
    #        block_context.push(name, block)
    with_context_push = ast_builder.build_stmt(
        state,
        lambda b: b.with_(
            b.context.push(),
            [
                b.if_(
                    b.is_not(block_context_var, None),
                    b.assign(block_var, block_context_var.pop(node.name)))
            ] + body + [
                b.if_(
                    b.is_not(block_context_var, None),
                    block_context_var.push(node.name, block_var))
            ]))

    state.add_render_function(
        [block_context_assign, with_context_push],
        _block_method_name(node.name))


@generate_expression.register(loader_tags.BlockNode)
def _generate_block_node(node, state):
    _emit_block_render_method(node, state)

    block_context_var = ast_builder.new_local_var(state, 'block_context')
    block_var = ast_builder.new_local_var(state, 'block')
    result_var = ast_builder.new_local_var(state, 'result')

    # block_context = context.render_context.get(BLOCK_CONTEXT_KEY)
    block_context_assign = ast_builder.build_stmt(
        state,
        lambda b: b.assign(
            block_context_var,
            b.context.render_context.get(loader_tags.BLOCK_CONTEXT_KEY)))

    # if block_context is not None:
    #     block_context.add_blocks({ name: self.render_block_<name> })
    #     block = block_context.get_block(name)
    # else:
    #     block = self.render_block_<name>
    block_assign = ast_builder.build_stmt(
        state,
        lambda b: b.if_(
            b.is_not(block_context_var, None),
            [
                block_context_var.add_blocks(b.dict({
                    node.name: ast.Attribute(
                        value=b.self,
                        attr=_block_method_name(node.name),
                        ctx=ast.Load())
                    })),
                b.assign(block_var, block_context_var.get_block(node.name)),
            ],
            b.assign(block_var, ast.Attribute(
                value=b.self,
                attr=_block_method_name(node.name),
                ctx=ast.Load()))))

    # with context.push():
    #     context['block'] = BlockWrapper(context, name)
    #     result = block(context)
    with_block = ast_builder.build_stmt(
        state,
        lambda b: b.with_(
            b.context.push(),
            [
                b.assign(
                    b.context['block'],
                    b[BlockWrapper](b.context, node.name)),
                b.assign(result_var, block_var(b.context))
            ]))

    # result
    result_var_load = util.copy_location(
        ast_builder.build_expr(state, lambda b: result_var),
        node)

    preamble = [block_context_assign, block_assign, with_block]

    return util.copy_location(preamble, node), result_var_load


@generate_expression.register(loader_tags.ExtendsNode)
def _generate_extends_node(node, state):
    for block in node.blocks.values():
        _emit_block_render_method(block, state)

    # if BLOCK_CONTEXT_KEY in context.render_context:
    #     context.render_context[BLOCK_CONTEXT_KEY] = BlockContext()
    block_context_insert = ast_builder.build_stmt(
        state,
        lambda b: b.if_(
            b.not_in(
                b.str(loader_tags.BLOCK_CONTEXT_KEY),
                b.context.render_context),
            b.assign(
                b.context.render_context[loader_tags.BLOCK_CONTEXT_KEY],
                b[loader_tags.BlockContext]())))

    # block_context variable
    block_context_var = ast_builder.new_local_var(state, 'block_context')

    # block_context = context.render_context[BLOCK_CONTEXT_KEY]
    block_context_assign = ast_builder.build_stmt(
        state,
        lambda b: b.assign(
            block_context_var,
            b.context.render_context[loader_tags.BLOCK_CONTEXT_KEY]))

    # block_context.add_blocks(
    #     { name: self.render_block_<name> for name in node.blocks.keys() }
    # )
    add_blocks_call = ast_builder.build_stmt(
        state,
        lambda b: block_context_var.add_blocks(b.dict({
            name: ast.Attribute(
                value=ast.Name(id='self', ctx=ast.Load()),
                attr=_block_method_name(name),
                ctx=ast.Load())
            for name in node.blocks.keys()
        })))

    if generator_flt_expr.is_constant(node.parent_name):
        # Lookup parent template statically if the referenced
        # name is a constant
        parent_template = loader.get_template(
            generator_flt_expr.get_constant_value(node.parent_name))

        parent_render = ast_builder.build_expr(
            state,
            lambda b: b.ivars[parent_template].render(b.context))
    else:
        # node.get_parent(context).render(context)
        parent_render = ast_builder.build_expr(
            state,
            lambda b: b.ivars[node].get_parent(b.context).render(b.context))

    preamble = [block_context_insert, block_context_assign, add_blocks_call]

    return util.copy_location(preamble, node), \
        util.copy_location(parent_render, node)


@generate_expression.register(loader_tags.IncludeNode)
def _generate_include_node(node, state):
    template_var = ast_builder.new_local_var(state, 'template')
    values_var = ast_builder.new_local_var(state, 'values')

    preamble = []

    if generator_flt_expr.is_constant(node.template):
        # Look up the included template statically if the referenced
        # name is a constant
        template = loader.get_template(
            generator_flt_expr.get_constant_value(node.template))
        preamble.append(ast_builder.build_stmt(
            state,
            lambda b: b.assign(template_var, b.ivars[template])))
    else:
        # template = node.template.resolve(context)
        preamble.append(ast_builder.build_stmt(
            state,
            lambda b: b.assign(
                template_var,
                b.ivars[node.template].resolve(b.context))))

        # if not callable(getattr(template, 'render', None)):
        #     template = get_template(template)
        preamble.append(ast_builder.build_stmt(
            state,
            lambda b: b.if_(
                b.not_(b[callable](b[getattr](template_var, 'render', None))),
                b.assign(template_var, b[loader.get_template](template_var)))))

    # values = {
    #     name: var.resolve(context),
    #     ...
    # }
    preamble.append(ast_builder.build_stmt(
        state,
        lambda b: b.assign(
            values_var,
            b.dict({
                name: util.generate_resolve_variable(var, state, False)
                for name, var in node.extra_context.items()
            }))))

    if node.isolated_context:
        # template.render(context.new(values))
        result_expr = ast_builder.build_expr(
            state,
            lambda b: template_var.render(b.context.new(values_var)))
    else:
        result_var = ast_builder.new_local_var(state, 'result')

        # with context.push(**values):
        #     result = template.render(context)
        with_block = ast_builder.build_stmt(
            state,
            lambda b: b.with_(
                b.context.push(__kwargs=values_var),
                b.assign(result_var, template_var.render(b.context))))

        preamble.append(with_block)

        # result
        result_expr = ast_builder.build_expr(state, lambda b: result_var)

    if not settings.TEMPLATE_DEBUG:
        result_var = ast_builder.new_local_var(state, 'result')

        # try:
        #     <body>
        #     result_var = <result_expr>
        # except:
        #     result_var = ''
        try_stmt = ast_builder.build_expr(
            state,
            lambda b: b.try_(
                preamble + [
                    b.assign(result_var, result_expr)
                ],
                b.except_(None, None, b.assign(result_var, ''))))

        preamble = [try_stmt]

        result_expr = ast_builder.build_expr(state, lambda b: result_var)

    return util.copy_location(preamble, node), \
        util.copy_location(result_expr, node)
