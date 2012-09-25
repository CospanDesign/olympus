#! /usr/bin/python

#Distributed under the MIT licesnse.
#Copyright (c) 2011 Dave McCoy (dave.mccoy@cospandesign.com)

#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in 
#the Software without restriction, including without limitation the rights to 
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
#of the Software, and to permit persons to whom the Software is furnished to do 
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all 
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
#SOFTWARE.

""" Logic Analyzer

Facilitates communication with the HMC6352 module, and example can be found
at sparkfun.com:

https://www.sparkfun.com/products/7915?

This core uses the I2C core and userland driver for details on the i2c
driver:

http://wiki.cospandesign.com/index.php?title=Wb_i2c

"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

import time
import sys
import os
import struct
import argparse

from array import array as Array

from userland import olympus
from userland.dionysus import dionysus
from userland.drivers import i2c
from userland.drivers import gpio

DESCRIPTION = "\n" + \
"Interface with the logic analyzer core\n" + \
"\n" + \
"Can be used in one of two ways:\n" + \
"\tAn Olympus Peripheral:\tAccessed in the same way as other slaves\n" + \
"\tIndependent UART device:\tUsed to interface with the \n"

EPILOG = "\n" + \
"Examples:\n" + \
"\n"
  



if __name__ == "__main__":
  #parser = argparse.ArgumentParser()
  #parser.parse_args()

  #parser.add_argument("echo")
  #args = parser.parse_args()
  #print args.echo
  print EPILOG



