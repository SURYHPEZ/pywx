# coding: utf-8

import re
from setuptools import setup, find_packages


with open('pywx/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"](?P<version>[^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group('version')

with open('README.md', 'r') as fd:
    readme = fd.read()


setup(
    name='pywx',
    version='version',
    description='Wechat Python Client',
    long_description=readme,
    author='SURYHPEZ',
    author_email='yy19899819@gmail.com',
    url='https://github.com/SURYHPEZ/pywx.git',
    packages=find_packages(),
    include_package_data=True,
    license='MIT',
    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: Chinese (Simplified)',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ),
    install_requires=[
        'requests',
        'gevent',
        'pillow',
        'lxml',
        'six',
        'enum34'
    ]
)
