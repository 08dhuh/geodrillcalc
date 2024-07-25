#! /usr/bin/env python
"""
Set up for the module
"""

from setuptools import setup, find_packages
import os


requirements = ['numpy>=1.0',
                # others,
                'pandas>=2.0'
                ]
# def get_requirements():
#     """
#     Read the requirements from a file
#     """
#     requirements = []
#     if os.path.exists('requirements.txt'):
#         with open('requirements.txt') as req:
#             for line in req:
#                 # skip commented lines
#                 if not line.startswith('#'):
#                     requirements.append(line.strip())
#     return requirements

setup(
    name='geodrillcalc', # the name of the module
    packages=find_packages(), # the location of the module
    version=0.3,
    install_requires=requirements,
    python_requires='>=3.8',
)