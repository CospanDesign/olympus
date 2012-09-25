#! /usr/bin/python

#Distributed under the MIT licesnse.
#Copyright (c) 2012 Dave McCoy (dave.mccoy@cospandesign.com)

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

Facilitates communication with the logic analyzer core, either through the
standard wishbone bus or through the UART core

When used with an Olympus image the logic_analyzer driver is used to
communicate with the core, for more information about the logic analyzer
core please refer to:

http://wiki.cospandesign.com/index.php?title=Logic_analyzer

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
"\tStandalone UART device:\tThis is useful to debug internal signals\n"

EPILOG = "\n" + \
"Examples:\n" + \
"\n" + \
"View a list of UART devices attached to this computer\n" + \
"\tlogic_analyzer.py -l\n" + \
"\n" + \
"Attach to the specified UART\n" + \
"\tlogic_analyzer.py -u /dev/ttyUSB0\n" + \
"\n" + \
"Go through all the UART devices on this computer, open up each UART\n" + \
"send the \'ping\' command, if the device responds then select that\n" + \
"device\n" + \
"\tlogic_analyzer.py -s\n"
  



if __name__ == "__main__":
  parser = argparse.ArgumentParser(
  formatter_class=argparse.RawDescriptionHelpFormatter,
    description=DESCRIPTION,
    epilog=EPILOG
    )

  #parser.add_argument("echo")
  parser.add_argument("-u", "--uart", type=str, default='/dev/ttyUSB0', help="Uses the UART logic analyzer interface specified")
  parser.add_argument("-l", "--list", help="Displays a list of possible UART interfaces to specify", action="store_true")
  parser.add_argument("-s", "--scan", help="Scans for a UART Logic Analyzer", action="store_true")
  parser.parse_args()
  args = parser.parse_args()
  #print EPILOG



