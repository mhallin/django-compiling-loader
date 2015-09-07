import pytest

from django.utils.safestring import mark_safe, mark_for_escaping
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
    raises = None
    result = None

    try:
        result = original.render(context)
    except (VariableDoesNotExist, AttributeError) as e:
        raises = e

    return raises, result


def render_native(settings, template_name, context):
    settings.TEMPLATE_LOADERS = NATIVE_LOADER_SETTINGS

    return render(settings, template_name, context)


def render_compiled(settings, template_name, context):
    settings.TEMPLATE_LOADERS = COMPILED_LOADER_SETTINGS

    return render(settings, template_name, context)


def assert_rendered_equally(settings, template_name, ctx_dict,
                            expected=None, must_succeed=False):
    native_raises, native_result = render_native(
        settings, template_name, Context(ctx_dict))

    compiled_raises, compiled_result = render_compiled(
        settings, template_name, Context(ctx_dict))

    if bool(native_raises) != bool(compiled_raises):
        if native_raises:
            raise native_raises
        if compiled_raises:
            raise compiled_raises

    assert native_result == compiled_result

    if must_succeed:
        assert not native_raises

    if expected is not None:
        assert native_result == expected


def test_nodelist_present(settings):
    settings.TEMPLATE_LOADERS = COMPILED_LOADER_SETTINGS
    loader.template_source_loaders = None

    template = get_template('tests/for.html')

    assert template.nodelist is not None


@pytest.mark.parametrize('template_name', [
    'tests/empty.html',
    'tests/simple.html',
])
def test_simple_no_context(settings, template_name):
    assert_rendered_equally(settings, template_name, {},
                            must_succeed=True)


@pytest.mark.parametrize('template_name', [
    'tests/var.html',
    'tests/var_default.html',
    'tests/var_default_var.html',
    'tests/var_filters.html',
    'tests/if.html',
    'tests/if_elif.html',
    'tests/if_elif_else.html',
    'tests/if_else.html',
    'tests/if_eq.html',
    'tests/if_eqeq.html',
    'tests/if_or.html',
    'tests/if_and.html',
    'tests/if_not.html',
    'tests/if_in.html',
    'tests/if_not_in.html',
    'tests/if_neq.html',
    'tests/extend_base.html',
    'tests/extend_child_empty.html',
    'tests/extend_child_override.html',
    'tests/extend_child_super.html',
    'tests/extend_child_super_twice.html',
    'tests/extend_child_child_empty.html',
    'tests/extend_base_super.html',
    'tests/include.html',
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
    'tests/if_gt.html',
    'tests/if_ge.html',
    'tests/if_lt.html',
    'tests/if_le.html',
])
@pytest.mark.parametrize('ctx_dict', [
    {},
    {'var': 'not a number'},
    {'var': 5},
    {'var': 10},
    {'var': 15},
])
def test_integer_var(settings, template_name, ctx_dict):
    assert_rendered_equally(settings, template_name, ctx_dict,
                            must_succeed=True)


@pytest.mark.parametrize('template_name', [
    'tests/var.html',
    'tests/var_default_html.html',
    'tests/var_default_var.html',
    'tests/var_filters.html',
    'tests/var_safe_filter.html',
])
@pytest.mark.parametrize('var', [
    'test',
    '<html>',
    mark_safe('<html>'),
    mark_for_escaping('<html>'),
])
@pytest.mark.parametrize('other', [
    'test',
    '<html>',
    mark_safe('<html>'),
    mark_for_escaping('<html>'),
])
def test_var_escaping(settings, template_name, var, other):
    assert_rendered_equally(settings, template_name,
                            {'var': var, 'other': other},
                            must_succeed=True)


@pytest.mark.parametrize('template_name,ctx_dict', [
    ('tests/var.html', {'var': [1, 2, 3]}),
    ('tests/var_default.html', {'var': []}),
    ('tests/var_filters.html', {'var': [1, 2, 3]}),
])
def test_other_types(settings, template_name, ctx_dict):
    assert_rendered_equally(settings, template_name, ctx_dict,
                            must_succeed=True)


@pytest.mark.parametrize('template_name', [
    'tests/for.html',
    'tests/for_no_exist.html',
    'tests/for_empty.html',
    'tests/for_unpack.html',
    'tests/for_reverse.html',
])
@pytest.mark.parametrize('var', [
    [],
    [0],
    ['test', 'another', mark_safe('<mango>'), '<banana>'],
])
def test_lists(settings, template_name, var):
    assert_rendered_equally(settings, template_name, {'var': var},
                            must_succeed=True)


@pytest.mark.parametrize('template_name', [
    'tests/for_nested.html',
])
@pytest.mark.parametrize('var', [
    [],
    [0],
    ['test', 'another', mark_safe('<mango>'), '<banana>'],
])
@pytest.mark.parametrize('var2', [
    [],
    [9],
    ['a', 'bunch', 'of', 'words']
])
def test_two_lists(settings, template_name, var, var2):
    assert_rendered_equally(settings, template_name,
                            {'var': var, 'var2': var2},
                            must_succeed=True)


def test_fallback(settings):
    assert_rendered_equally(
        settings,
        'tests/block_upper.html',
        {},
        expected='\nSOME UPPERCASED TEXT\n'
    )
