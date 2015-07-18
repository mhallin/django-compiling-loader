from setuptools import setup, find_packages

setup(
    name='compiling_loader',
    version='0.0.1',
    packages=find_packages(exclude=['test_proj']),

    extras_require={
        'test': [
            'pytest~=2.7.2',
            'pytest-cov~=1.8.1',
            'pytest-django~=2.8.0',
            'Django~=1.7.0'
        ],
    },
)
