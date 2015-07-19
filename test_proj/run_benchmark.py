#!/usr/bin/env python
import os
import random
import time

TIMER = time.perf_counter

NATIVE_LOADER_SETTINGS = (
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
)

COMPILED_LOADER_SETTINGS = (
    ('django.template.loaders.cached.Loader', [
        ('compiling_loader.Loader', [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]),
    ]),
)


def switch_loader_settings(new_param):
    from django.conf import settings
    from django.template import loader

    settings.TEMPLATE_LOADERS = new_param
    loader.template_source_loaders = None


def run_timings(template_name, iterations, ctx_dict):
    from django.template import Context
    from django.template.loader import get_template

    template = get_template(template_name)
    print('Found template {} for name {}'.format(template, template_name))
    # print('rendered: {}'.format(template.render(Context(ctx_dict))))

    start_time = TIMER()
    for i in range(iterations):
        template.render(Context(ctx_dict))
    end_time = TIMER()

    return (end_time - start_time) / iterations


def random_style():
    return random.choice([
        '', 'font-weight: bold', 'color: red', 'text-transform: uppercase',
    ])


def random_data():
    return random.choice([
        '', 'Test data 123',
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean a turpis mattis libero ornare malesuada. Maecenas eu feugiat tortor. Suspendisse potenti. Ut egestas neque pretium, porttitor nibh nec, viverra purus. Mauris et justo iaculis, euismod neque sed',
        10 * 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean a turpis mattis libero ornare malesuada. Maecenas eu feugiat tortor. Suspendisse potenti. Ut egestas neque pretium, porttitor nibh nec, viverra purus. Mauris et justo iaculis, euismod neque sed'
    ])


def generate_test_data(count):
    return [
        {'style': random_style(), 'data': random_data()}
        for _ in range(count)
    ]


def run_bench():
    main_count = 10000
    main_ctx = {}

    loop_count = 20
    loop_ctx = {'data': generate_test_data(2000)}

    switch_loader_settings(NATIVE_LOADER_SETTINGS)
    native_main = run_timings('benchmark/main.html', main_count, main_ctx)
    native_loop = run_timings('benchmark/loop.html', loop_count, loop_ctx)

    switch_loader_settings(COMPILED_LOADER_SETTINGS)
    compiled_main = run_timings('benchmark/main.html', main_count, main_ctx)
    compiled_loop = run_timings('benchmark/loop.html', loop_count, loop_ctx)

    print('Native main template:   {:.5}'.format(1000 * native_main))
    print('Compiled main template: {:.5}'.format(1000 * compiled_main))
    print('Fractional time: {:.3}'.format(compiled_main / native_main))

    print('Native loop template:   {:.5}'.format(1000 * native_loop))
    print('Compiled loop template: {:.5}'.format(1000 * compiled_loop))
    print('Fractional time: {:.3}'.format(compiled_loop / native_loop))


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_proj.settings")

    import django

    django.setup()

    run_bench()
