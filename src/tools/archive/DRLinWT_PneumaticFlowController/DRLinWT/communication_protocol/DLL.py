# -*- coding: UTF-8 -*-

from ctypes import *
from numpy.lib.arraysetops import isin
from sympy import *

# ---导入python 外部函数 ctypes
import ctypes
import time
import argparse
import math
import numpy as np


# ---导入Fuyu 二次开发库
fuyudll = windll.LoadLibrary('./AMC4030.dll')


