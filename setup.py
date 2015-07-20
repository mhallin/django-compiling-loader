from setuptools import setup, find_packages

setup(
    name='django-compiling-loader',
    version='0.0.1',
    packages=find_packages(exclude=['test_proj']),

    url='https://github.com/mhallin/django-compiling-loader',
    description='A bytecode compiling template loader for Django',
    long_description=open('README.rst').read(),

    author='Magnus Hallin',
    author_email='mhallin@gmail.com',

    license='BSD',

    extras_require={
        'test': [
            'pytest~=2.7.2',
            'pytest-cov~=1.8.1',
            'pytest-django~=2.8.0',
            'Django~=1.7.0'
        ],
        'dist': [
            'twine',
            'wheel'
        ]
    },

    classifiers=[
        'Development Status :: 4 - Beta',

        'Framework :: Django',
        'Framework :: Django :: 1.7',

        'Intended Audience :: Developers',

        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',

        'Topic :: Software Development :: Compilers',
    ],

    keywords='django performance template',
)
