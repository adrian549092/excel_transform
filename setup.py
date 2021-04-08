# -*- coding: utf-8 -*-

import re

from setuptools import setup, find_packages

project_name = 'excel_transform'
version = '0.0.0-dev'

with open('README.md', 'rb') as f:
    readme = f.read().decode("utf8").replace('\r\n', '\n')

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
    with open('requirements.txt') as f:
        requirements = f.read().splitlines()
except:
    requirements = ''

setup(
    name=project_name,
    version=f'{version}',
    packages=find_packages(exclude=('tests', 'docs')),
    license='MIT',
    author='Adrian Martin',
    author_email='adrian.m138@gmail.com',
    url=f'https://github.com/adrian549092/{project_name}',
    description='This is a tool to generate an excel file based on a provided source excel and transformation mapping',
    long_description=readme,
    long_description_content_type='text/markdown',
    install_requires=requirements,
    include_package_data=True,
    entry_points={'console_scripts': [f'{project_name.replace("_", "-")} = {project_name}.__init__:cli']},
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.8'
)
