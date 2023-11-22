from setuptools import find_packages, setup

setup(
    name='smarthelio_shared',
    packages=find_packages(include=['smarthelio_shared']),
    install_requires=['urllib3<2.0.0', 'pandas', 'requests', 'pvlib', 'numpy', 'rdtools', 'wheel', 'pytz'],
    version='1.11.4',
    description='SmartHelio shared',
    author='SmartHelio',
    license='MIT',
)
