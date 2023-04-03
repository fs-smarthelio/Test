from setuptools import find_packages, setup

setup(
    name='smarthelio_shared',
    packages=find_packages(include=['smarthelio_shared']),
    install_requires=['pandas', 'requests', 'pvlib', 'numpy', 'rdtools', 'wheel'],
    version='1.0.0',
    description='SmartHelio shared',
    author='SmartHelio',
    license='MIT',
)
