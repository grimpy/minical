#!/usr/bin/env python3
from setuptools import setup

setup(name='minical',
      version='0.1',
      description='Minimal python3 calendar',
      author='Jo De Boeck',
      author_email='deboeck.jo@gmail.com',
      url='http://github.com/grimpy/minical',
      install_requires=['readchar'],
      packages=['minical'],
      entry_points={'console_scripts': ['minical=minical.__main__:main']}
      )
