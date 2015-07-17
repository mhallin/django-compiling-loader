import time
import timeit


def run_bench(source, context):
    native_timer = timeit.Timer(
        timer=time.process_time,
        stmt='template.render(context)',
        setup='''
from django.template.base import Template, Context
template = Template(''' + repr(source) + ''')
context = Context(''' + repr(context) + ''')
''')

    compiled_timer = timeit.Timer(
        timer=time.process_time,
        stmt='template.render(context)',
        setup='''
from django.template.base import Template, Context
from compiling_loader import compile_template
src_template = Template(''' + repr(source) + ''')
context = Context(''' + repr(context) + ''')
template = compile_template(src_template, name='test.html')
''')

    print('Starting benchmark')

    iterations = 100

    native_time = native_timer.timeit(iterations)
    compiled_time = compiled_timer.timeit(iterations)

    print('Django native: {:>.4}'.format(native_time))
    print('Compiled:      {:>.4} {}%'.format(
        compiled_time,
        round(100 * compiled_time / native_time)))


if __name__ == '__main__':
    from django.conf import settings
    settings.configure()

    run_bench('test {{ var|upper|lower|slugify }}' * 1000, {'var': 'bummy'})
