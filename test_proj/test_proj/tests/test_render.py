import pytest

from django.template.loader import get_template, Context
from django.template import VariableDoesNotExist, loader


NATIVE_LOADER_SETTINGS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

COMPILED_LOADER_SETTINGS = (
    ('compiling_loader.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
)


def render(settings, template_name, context):
    loader.template_source_loaders = None
    original = get_template(template_name)
    original_raises = False
    original_result = None

    try:
        original_result = original.render(context)
    except VariableDoesNotExist:
        original_raises = True

    return original_raises, original_result


def render_native(settings, template_name, context):
    settings.TEMPLATE_LOADERS = NATIVE_LOADER_SETTINGS

    return render(settings, template_name, context)


def render_compiled(settings, template_name, context):
    settings.TEMPLATE_LOADERS = COMPILED_LOADER_SETTINGS

    return render(settings, template_name, context)


def assert_rendered_equally(settings, template_name, ctx_dict, expected=None):
    native_raises, native_result = render_native(
        settings, template_name, Context(ctx_dict))

    compiled_raises, compiled_result = render_compiled(
        settings, template_name, Context(ctx_dict))

    assert native_raises == compiled_raises
    assert native_result == compiled_result

    if expected is not None:
        assert native_result == expected


@pytest.mark.parametrize('template_name', [
    'empty.html',
    'simple.html',
])
def test_simple_no_context(settings, template_name):
    assert_rendered_equally(settings, template_name, {})


@pytest.mark.parametrize('template_name', [
    'var.html',
    'var_default.html',
    'var_default_var.html',
    'var_filters.html',
    'if.html',
    'if_elif.html',
    'if_elif_else.html',
    'if_else.html',
    'if_eq.html',
    'if_eqeq.html',
    'if_or.html',
    'if_and.html',
    'if_not.html',
    'if_in.html',
    'if_not_in.html',
    'if_neq.html',
    'extend_base.html',
    'extend_child_empty.html',
])
@pytest.mark.parametrize('ctx_dict', [
    {},
    {'var': ''},
    {'var': '', 'other': ''},
    {'var': '', 'other': 'other'},
    {'var': 'test'},
    {'var': 'test', 'other': ''},
    {'var': 'test', 'other': 'other'},
    {'other': ''},
    {'other': 'other'},
])
def test_two_vars(settings, template_name, ctx_dict):
    assert_rendered_equally(settings, template_name, ctx_dict)


@pytest.mark.parametrize('template_name', [
    'if_gt.html',
    'if_ge.html',
    'if_lt.html',
    'if_le.html',
])
@pytest.mark.parametrize('ctx_dict', [
    {},
    {'var': 'not a number'},
    {'var': 5},
    {'var': 10},
    {'var': 15},
])
def test_integer_var(settings, template_name, ctx_dict):
    assert_rendered_equally(settings, template_name, ctx_dict)


@pytest.mark.parametrize('template_name', [
    'var.html',
    'var_default_html.html',
    'var_default_var.html',
    'var_filters.html',
])
def test_var_escaping(settings, template_name):
    assert_rendered_equally(settings, template_name, {'var': '<html>'})


@pytest.mark.parametrize('template_name,ctx_dict', [
    ('var.html', {'var': [1, 2, 3]}),
    ('var_default.html', {'var': []}),
    ('var_filters.html', {'var': [1, 2, 3]}),
])
def test_other_types(settings, template_name, ctx_dict):
    assert_rendered_equally(settings, template_name, ctx_dict)


def test_fallback(settings):
    assert_rendered_equally(
        settings,
        'block_upper.html',
        {},
        expected='\nSOME UPPERCASED TEXT\n'
    )
