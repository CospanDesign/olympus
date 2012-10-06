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

""" test_dionysus

Main userland communication tool with the Dionysus board

"""
__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

""" Changelog:
  
08/30/2012
  -Initial Commit

"""

import time
import random
import sys
import os
import string
import json
import getopt 
from array import array as Array

from userland import olympus
from userland.olympus import OlympusCommError
from userland.dionysus.dionysus import Dionysus
from userland.drivers import uart
from userland.drivers import gpio
from userland.drivers import spi
from userland.drivers import i2c
from userland.drivers import console
from userland.drivers import i2s
from userland.drivers import logic_analyzer
from userland.drivers import gtp_test

#TEST CONSTANTS
MEM_SIZE = 1100
TEST_MEM_SIZE = 2097151

   
TEST_GPIO = False
TEST_UART = False
TEST_I2C = False
TEST_SPI = False
TEST_MEMORY = True
TEST_CONSOLE = False
TEST_I2S = False
TEST_LOGIC_ANALYZER = False
TEST_GTP = False

def test_memory(dyn, dev_index):
  print "testing memory @ %d" % dev_index
  mem_bus = dyn.is_memory_device(dev_index)
  if mem_bus:
    print "Memory is on Memory bus"
  else:
    print "Memory is on Peripheral bus"

  print "Testing short write"
  data_out  = Array('B', [0xAA, 0xBB, 0xCC, 0xDD, 0x55, 0x66, 0x77, 0x88])
  print "out data: %s" % str(data_out)
  print "hex: "
  for i in range (0, len(data_out)):
    print str(hex(data_out[i])) + ", ",
  print " "

  dyn.write_memory(0, data_out)

  print "Testing short read"
  data_in = dyn.read_memory(0, 2)
  print "mem data: %s" % str(data_in)
  print "hex: "
  for i in range (0, len(data_in)):
    print str(hex(data_in[i])) + ", ",
  print " "



  print "Testing a write/read at the end of memory"
  dev_size = dyn.get_device_size(dev_index)
  print "writing to memory location 0x%08X" % (dev_size - 8)
  dyn.write_memory(dev_size - 8, data_out)
  print "reading from memory location 0x%08X" % (dev_size - 8)
  data_in = dyn.read_memory(dev_size - 8, 2)

  print "mem data: %s" % str(data_in)
  print "hex: "
  for i in range (0, len(data_in)):
    print str(hex(data_in[i])) + ", ",
  print " "

  dev_size = (dyn.get_device_size(dev_index) / 4)
  print "Memory size: 0x%X" % (dyn.get_device_size(dev_index))
  
  data_out = Array('B')
  num = 0
  try:
    for i in range (0, 4 * dev_size):
      num = (i) % 255
      #if (i / 256) % 2 == 1:
      #  data_out.append( 255 - (num))
      #else:
      data_out.append(num)


  except OverflowError as err:
    print "Overflow Error: %d >= 256" % num
    sys.exit(1)
 
  print "Writing %d bytes of data" % (len(data_out))
  dyn.debug = True
  dyn.write_memory(0, data_out)
  dyn.debug = False
  #dyn.write(dev_index, 0, data_out, mem_bus)
  print "Reading %d bytes of data" % (len(data_out))
  data_in = dyn.read_memory(0, len(data_out) / 4)
  #data_in = dyn.read(dev_index, 0, len(data_out) / 4, mem_bus)

  print "Comparing values"
  fail = False
  fail_count = 0
  if len(data_out) != len(data_in):
    print "data_in length not equal to data_out length:"
    print "\totugoing: %d incomming: %d" % (len(data_out), len(data_in))
    fail = True

  else:
    for i in range (0, len(data_out)):
      if data_in[i] != data_out[i]:
        fail = True
        #print "Mismatch at %d: READ DATA %d != WRITE DATA %d" % (i, data_in[i], data_out[i])
        fail_count += 1

  if not fail:
    print "Memory test passed!"
  elif (fail_count == 0):
    print "Data length of data_in and data_out do not match"
  else:
    print "Failed: %d mismatches" % fail_count



def unit_test_devices(dyn):
  num_devices = dyn.get_number_of_devices()
  print "Unit Test"
  print "Found %d slaves " % num_devices
  print "Searching for standard devices..."
  for dev_index in range (0, num_devices):
    memory_device = dyn.is_memory_device(dev_index)
    dev_offset = dyn.get_device_address(dev_index)
    dev_size = dyn.get_device_size(dev_index)
    device_id = dyn.get_device_id(dev_index)

    if TEST_GPIO:
      if (device_id == 1):
        print "Found GPIO"
        print "testing GPIO @ %d" % dev_offset
        gpio.unit_test(dyn, dev_offset)

    if TEST_UART:
      if (device_id == 2):
        print "Found UART device"
        print "testing UART @ %d" % dev_offset
        uart = UART(dyn, dev_offset)
        uart.unit_test()

    if TEST_I2C:
      if (device_id == 3):
        print "Fond I2C device"
        print "testing I2C @ %d" % dev_offset
        i2c.unit_test(dyn, dev_offset)

    if TEST_SPI:
      if (device_id == 4):
        print "Found SPI device"
        print "testing SPI @ %d" % dev_offset
        spi.unit_test(dyn, dev_offset)
    
    if TEST_MEMORY:
      if (device_id == 5):
        print "Found a memory device"
        test_memory(dyn, dev_index)

    if TEST_CONSOLE:
      if (device_id == 6):
        print "Found a console device"
        console.unit_test(dyn, dev_offset)

    if TEST_I2S:
      if (device_id == 0x0B):
        print "Found I2S device"
        print "testing I2S @ %d" % dev_offset
        i2s.unit_test(dyn, dev_offset)

    if TEST_LOGIC_ANALYZER:
      if (device_id == 0x0C):
        print "Found Logic Analyzer device"
        print "testing Logic Analyzer @ %d" % dev_offset
        logic_analyzer.unit_test(dyn, dev_offset)
 
    if TEST_GTP:
      if (device_id == 0x0E):
        print "Found Experimental GTP"
        print "testing GTP @ %d" % dev_offset
        gtp_test.unit_test(dyn, dev_offset)
 

 
def usage():
  """prints out a helpful message to the user"""
  print ""
  print "usage: dionysus.py [options]"
  print ""
  print "-h\t--help\t\t\t: displays this help"
  print "-d\t--debug\t\t\t: runs the debug analysis"
  print "-m\t--memory\t\t\t: test only memory"
  print "-l\t--long\t\t\t\t: long memory test"
  print "-t\t--test\t\t\t\t: test"
  print ""


if __name__ == '__main__':
  print "starting..."
  argv = sys.argv[1:]
  mem_only = False
  long_mem_test = False
  test = False

  try:
    dyn = None
    if (len(argv) > 0):
      opts = None
      opts, args = getopt.getopt(argv, "hdmlt", ["help", "debug", "memory", "long", "test"])
      for opt, arg in opts:
        if opt in ("-h", "--help"):
          usage()
          sys.exit()
        elif opt in ("-d", "--debug"):
          print "Debug mode"
          dyn = Dionysus(debug = True)
          dyn.debug_comm()
        elif opt in ("-m", "--memory"):
          mem_only = True
        elif opt in ("-l", "--long"):
          long_mem_test = True
        elif opt in ("-t", "--test"):
          test = True

    if dyn is None:
      dyn = Dionysus(debug = False)

  except IOError, ex:
    print "PyFtdi IOError when openning: " + str(ex)
  except AttributeError, ex:
    print "PyFtdi Attribute Error when openning: " + str(ex)
  except getopt.GetoptError, err:
    print (err)
    usage()


#  try:
  dyn.ping()
  print "Reading DRT"
  dyn.read_drt()
  print "Printing DRT:"


  if test:
    print "Performing Tests:"
    test_all_memory(dyn, TEST_MEM_SIZE)
    sys.exit()

  else:
    dyn.pretty_print_drt()
    unit_test_devices(dyn)

#  except OlympusCommError, ex:
#    print "Communication Error: %s" % str(ex)
  


