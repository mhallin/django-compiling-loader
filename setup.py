from setuptools import setup, find_packages

setup(
    name='compiling_loader',
    version='0.0.1',
    packages=find_packages(exclude=['tests']),

    extras_require={
        'test': [
            'pytest',
            'pytest-cov',
        ],
    },
)
