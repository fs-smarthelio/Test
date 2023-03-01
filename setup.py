from setuptools import find_packages, setup

setup(
    name='smarthelio-shared',
    packages=find_packages(include=['smarthelio-shared']),
    install_requires=['pandas', 'requests', 'pvlib'],
    version='1.0.0',
    description='SmartHelio shared',
    author='SmartHelio',
    license='MIT',
)