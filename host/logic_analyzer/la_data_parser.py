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

""" Logic Analyzer Data Parser

Reads in the raw values from the Logic Analyzer and creaes a vcd file from it
"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

import time
from array import array as Array

def create_vcd_buffer(data, signal_dict = {}, count = 32):
  print "create a VCD file"

  if len(signal_dict.keys()) == 0:
    for i in range (0, count): 
      signal_dict["signal%d" % i] = 1

  buf = ""
  buf += set_vcd_header()
  buf += set_signal_names(signal_dict)
  buf += set_waveforms(data, signal_dict) 

  return buf


def set_signal_names (signal_dict):
  #in the future I should come up with a good name for this
  buf = ""

  #set the scope
  buf += "$scope\n"
  buf += "$module logic_analyzer\n"
  buf += "$end\n"
  buf += "\n"

  offset = 0
  for i in range (0, 32):
    name = "signal%d" % i
    buf += "$var wire %d %c %s $end\n" % (signal_dict[name], 33 + offset, name)
    offset += 1
    
  #pop off the scope stack
  buf += "\n"
  buf += "$upscope\n"
  buf += "$end\n"
  buf += "\n"

  #end the signal name definitions
  buf += "$enddefinitions\n"
  buf += "$end\n"
 
  return buf

def set_vcd_header ():
  #set date
  buf = ""
  buf += "$date\n"
  buf += time.strftime("%b %d, %Y %H:%M:%S") + "\n"
  buf += "$end\n"
  buf += "\n"

  #set version
  buf += "$version\n"
  buf += "Olympus Logic Analyzer V0.1\n"
  buf += "$end\n"
  buf += "\n"

  #set the timescale
  buf += "$timescale\n"
  buf += "1 ns\n"
  buf += "$end\n"
  buf += "\n"

  return buf

def set_waveforms(data, signal_dict):
  buf = ""
  keys = signal_dict.keys() 
  #put the first waveform down
  buf += "#0\n"
  for i in range (0, 32):
    buf += "%d%c\n" % (((data[0] >> i) & 0x01), (33 + i))

  #go through all the values for every time instance and look for changes
  print "Data Length: %d" % len(data)
  length = len(data)
  for i in range (1, len(data) - 1):
    if (data[i - 1] != data[i]):
      #there is a difference at this time
      buf += "#%d\n" % i
      for j in range (0, 32):
        if ((data[i - 1] >> j) & 0x01) != ((data[i] >> j) & 0x01):
          buf += "%d%c\n" % (((data[i] >> j) & 0x01), (33 + j))

  buf += "#%d\n" % length 
  for i in range (0, 32):
    buf += "%d%c\n" % (((data[-1] >> i) & 0x01), (33 + i))

 
  return buf

