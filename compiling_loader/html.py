from django.utils.timezone import template_localtime
from django.utils.formats import localize
from django.utils.encoding import force_text
from django.utils.safestring import SafeData, EscapeData

# These functions mimic the corresponding functions from
# Django itself, but have been tuned in minor ways to squeeze
# a little bit more performance out of them.
#
# Hotspots have been detected by running the run_benchmark.py
# script with profiling turned on, and generating a call graph.


def fast_render_value_in_context(value, context):
    value = template_localtime(value, use_tz=context.use_tz)
    value = localize(value, use_l10n=context.use_l10n)
    value = force_text(value)

    # We know that `str` type is never safe data, and also the
    # most common type to pass through here. Making a type()
    # comparison *before* the isinstance call skips that
    # slow call in many cases.
    if ((context.autoescape and
        (type(value) == str or not isinstance(value, SafeData))) or
            isinstance(value, EscapeData)):
        return conditional_escape(value)
    else:
        return value


# `fast_escape` does not support lazy strings like the original
# `escape` function. However, we know that the text is not lazy
# since this method is only called from functions in this file.
def fast_escape(text):
    # Also, testing if a character is in the array is faster
    # even though it should loop over the array twice. Mabye
    # str.replace always makes a copy of the original string?
    text = text.replace('&', '&amp;') if '&' in text else text
    text = text.replace('<', '&lt;') if '<' in text else text
    text = text.replace('>', '&gt;') if '>' in text else text
    text = text.replace('"', '&quot;') if '"' in text else text
    text = text.replace("'", '&#39;') if "'" in text else text

    return text


# Loke `fast_render_value_in_context`, make a type lookup
# against `str` before calling the more expensive `hasattr`.
def conditional_escape(text):
    if type(text) != str and hasattr(text, '__html__'):
        return text.__html__()
    else:
        return fast_escape(text)
