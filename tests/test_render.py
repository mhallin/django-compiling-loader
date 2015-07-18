import pytest
import string

from django.template.base import Template, Context, VariableDoesNotExist
from hypothesis import given, strategies as st

from compiling_loader import compile_template


def assert_equal(s, ctx_dict={}, should_equal=None):
    original = Template(s)
    original_raises = False
    original_result = None

    try:
        original_result = original.render(Context(ctx_dict))
    except VariableDoesNotExist:
        original_raises = True

    compiled = compile_template(Template(s), 'test.html')
    compiled_raises = False
    compiled_result = None

    try:
        compiled_result = compiled.render(Context(ctx_dict))
    except VariableDoesNotExist:
        compiled_raises = True

    assert original_raises == compiled_raises
    assert original_result == compiled_result

    if should_equal is not None:
        assert should_equal == compiled_result


def test_empty():
    assert_equal('')


@given(st.text())
def test_plain(s):
    assert_equal(s)


@given(st.text(min_size=1, alphabet=string.ascii_letters),
       st.text() | st.integers() | st.floats())
def test_variable(var, value):
    assert_equal('{{ ' + var + ' }}', {})
    assert_equal('{{ ' + var + ' }}', {var: value})
    assert_equal('{{ ' + var + '|upper }}', {})
    assert_equal('{{ ' + var + '|upper }}', {var: value})
    assert_equal('{{ ' + var + '|default:"empty" }}', {})
    assert_equal('{{ ' + var + '|default:"empty" }}', {var: value})
    assert_equal('{{ ' + var + '|default:other }}', {})
    assert_equal('{{ ' + var + '|default:other }}', {var: value})
    assert_equal('{{ ' + var + '|default:other }}', {'other': 'test'})
    assert_equal('{{ ' + var + '|default:other }}',
                 {var: value, 'other': 'test'})


@pytest.mark.parametrize('s,ctx', [
    ('{{ var }} {{ var }}', {'var': 'testing'}),
    ('{{ var|upper }} {{ var|upper }}', {'var': 'testing'}),
    ('{{ var|first|slugify }}', {'var': ['a banana', 'a thing', 'avocado']}),
    ('{{ var }}', {'var': '<html>'}),
    ('{{ var|default:other }}', {'other': '<html>'})
])
def test_variables(s, ctx):
    assert_equal(s, ctx)


def test_fallback():
    assert_equal('{% blockupper %}testing testing{% endupper %}',
                 should_equal='TESTING TESTING')
