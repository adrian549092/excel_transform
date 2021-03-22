# -*- coding: utf-8 -*-

import re

from setuptools import setup, find_packages

project_name = 'excel_transform'
version = '0.0.0-dev'

with open('README.md') as f:
    readme = f.read()

try:
    with open(f'{project_name}/__init__.py') as f:
        pattern = re.compile(r'__version__\s+=\s+["\'](\S+)["\']')
        for line in f.readlines():
            m = pattern.search(line)
            if m:
                version = m.group(1)
                break
except Exception as e:
    print(f'encountered error opening __init__.py: {e}')

try:
    with open('LICENSE') as f:
        license_content = f.read()
except:
    license_content = ''

try:
    with open('requirements.txt') as f:
        requirements = f.read().splitlines()
except:
    requirements = ''

setup(
    name=project_name,
    version=f'{version}',
    packages=find_packages(exclude=('tests', 'docs')),
    license=license_content,
    author='Adrian Martin',
    url=f'https://github.com/adrian549092/{project_name}',
    author_email='adrian.m138@gmail.com',
    description='This is a tool to generate an excel file based on a provided source excel and transformation mapping',
    long_description=readme,
    install_requires=requirements,
    include_package_data=True,
    entry_points={'console_scripts': [f'{project_name.replace("_", "-")} = {project_name}.__init__:cli']}
)
