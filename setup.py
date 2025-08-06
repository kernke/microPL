# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages

setup(name="MicroPL",
      version="0.1",
      packages=find_packages(),
      install_requires=[
          "numpy",
          "pylablib",
          "pyqtgraph",
          #"msl"
      ])