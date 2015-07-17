import pytest

from django.template.base import Template, Context

from compiling_loader import compile_template


def assert_equal(s, ctx_dict={}):
    original = Template(s)
    original_result = original.render(Context(ctx_dict))

    compiled = compile_template(Template(s), 'test.html')
    compiled_result = compiled.render(Context(ctx_dict))

    assert original_result == compiled_result


def test_empty():
    assert_equal('')


def test_simple():
    assert_equal(' test ') == ' test '


@pytest.mark.parametrize('s,ctx', [
    ('{{ var }}', {}),
    ('{{ var }}', {'var': 'test'})
])
def test_variables(s, ctx):
    assert_equal(s, ctx)
