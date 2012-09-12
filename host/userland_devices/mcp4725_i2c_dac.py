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

""" MCP4725 DAC

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
import math

from array import array as Array

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from userland import olympus
from userland.dionysus import dionysus
from userland.drivers import i2c
from userland.drivers import gpio

I2C_ADDRESS             = 0x60

class MCP4725:
  """MCP4725

  Communicates the he MCP4725 DAC over I2C
  """
  
  def __init__(self, oly, i2c_dev_index):
    self.o = oly
    self.i2c = i2c.I2C(oly, i2c_dev_index)
    self.i2c.set_speed_to_400khz()

  def set_voltage(self, voltage):
    """set_voltage

    sets the voltage of the DAC

    Args:
      voltage: 12 bit voltage to set

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
      I2CError: Error in I2C communication
    """

    write_data = Array('B', [0, 0])
    write_data[0] = (voltage >> 8) & 0xFF
    write_data[1] = (voltage) & 0xFF
    self.i2c.write_to_i2c(I2C_ADDRESS, write_data)

if __name__ == "__main__":
  oly = dionysus.Dionysus()
  oly.ping()
  oly.read_drt()

  i2c_device = 0

  num_devices = oly.get_number_of_devices()

  for dev_index in range (0, num_devices):
    device_id = oly.get_device_id(dev_index)
    dev_offset = oly.get_device_address(dev_index)

    if device_id == 3:
      i2c_index = dev_offset
    
  if i2c_index == 0:
    print "Couldn't find I2C device"
    sys.exit(1)

  print "Found I2C device at index: %d" % i2c_index

  dac = MCP4725(oly, i2c_index)

  value = 0
  direction = 1
  increment = .1
  
  rad = 0.0

  
  try:
    while (1):
 
      if (rad >= (2 * math.pi)):
        rad = 0
 
 
      sval = math.sin(rad)
 
      sval = sval + 1
      sval = sval * (4095.0/2)
 
      value = int(sval)
 
      dac.set_voltage(value)
 
      rad = rad + increment
 
 
 
 
      """
      if direction == 1:
        value = value + increment
      else:
        value = value - increment
 
      if value >= 4095:
        value = 4095
        direction = 0
      
      elif value <= 0:
        value = 0
        direction = 1
 
      """

  except:
    print "Exiting"
