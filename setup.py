#!/usr/bin/env python

from setuptools import setup, find_packages

with open('VERSION', 'r', encoding='utf-8') as f :
    version = f.read()

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(name='terminal-temple'
      ,url='https://github.com/BU-Neuromics/terminal_temple'
      ,version=version
      ,description='Another cute little puzzle for teaching basic-to-intermediate command line usage'
      ,long_description=long_description
      ,long_description_content_type="text/markdown"
      ,author='Adam Labadorf'
      ,author_email='labadorf@bu.edu'
      ,license='MIT'
      ,packages=find_packages()
      ,package_data={'terminal_temple': ['data/*']}
      ,python_requires='>=3.6'
      ,install_requires=[
        'future'
        ,'fabulous'
        ,'pillow'
        ,'docopt'
        ,'inflect'
        ,'networkx'
        ,'setuptools'
        ,'numpy'
      ]
      ,entry_points={
        'console_scripts': [
          'terminal_temple=terminal_temple:main'
        ]
      }
      ,classifiers=[
          # How mature is this project? Common values are
          #   3 - Alpha
          #   4 - Beta
          #   5 - Production/Stable
          'Development Status :: 5 - Production/Stable',

          # Indicate who your project is intended for
          'Intended Audience :: Education',
          'Topic :: Education',

          # Pick your license as you wish (should match "license" above)
          'License :: OSI Approved :: MIT License',

          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
      ]
     )

