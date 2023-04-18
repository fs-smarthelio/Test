from setuptools import find_packages, setup

setup(
    name='smarthelio_shared',
    packages=find_packages(include=['smarthelio_shared']),
    install_requires=['pandas', 'requests', 'pvlib', 'numpy', 'rdtools', 'wheel', 'pytz'],
    version='1.4.1',
    description='SmartHelio shared',
    author='SmartHelio',
    license='MIT',
)
