#! /usr/bin/env python
"""
Set up for the module
"""

from setuptools import setup, find_packages
import os


requirements = [
    'numpy>=1.0',
    'pandas>=2.0',
    
]

# Get the current directory
current_dir = os.path.abspath(os.path.dirname(__file__))

# Read the contents of the README.md file
with open(os.path.join(current_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='geodrillcalc',  
    version='0.4.1-alpha', 
    description='Geothermal Wellbore Parameter and Cost Calculation Tool for SGIL Project',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Doran Huh',  
    author_email='08dhuh@gmail.com', 
    url='https://github.com/08dhuh/geodrillcalc', 
    packages=find_packages(), 
    install_requires=requirements,  
    python_requires='>=3.11', 
    classifiers=[
        'Development Status :: 3 - Alpha', 
        'Intended Audience :: Developers', 
        'License :: OSI Approved :: MIT License',  
        'Programming Language :: Python :: 3.11',  
        'Topic :: Scientific/Engineering',  
    ],
)
