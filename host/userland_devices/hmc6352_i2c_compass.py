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

""" I2C

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

from array import array as Array

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from userland import olympus
from userland.dionysus import dionysus
from userland.drivers import i2c
from userland.drivers import gpio

I2C_ADDRESS             = 0x21

#I2C Regiser Addresses
RAM_WRITE_ADDRESS       = 0x47
RAM_READ_ADDRESS        = 0x67
HEADING_ADDRESS         = 0x41

#HMC6352 RAM Addresses
RAM_ADDRESS_OP_MODE     = 0x74
RAM_ADDRESS_OUT_MODE    = 0x4E

HEADING_READ_SIZE       = 2 
MAGNETIC_READ_SIZE      = 2

OP_MODE_READ_SIZE       = 1
OUT_MODE_READ_SIZE      = 1

MODE_1HZ                = 0x00
MODE_5HZ                = 0x20
MODE_10HZ               = 0x40
MODE_20HZ               = 0x60

MODE_PERIODIC_SET       = 0x10

MODE_STANDBY            = 0x00
MODE_QUERY              = 0x01
MODE_CONTINUOUS         = 0x02

OUT_MODE_HEADING        = 0x00
OUT_MODE_RAW_MAGNETIC_X = 0x01
OUT_MODE_RAW_MAGNETIC_Y = 0x02
OUT_MODE_MAGNETIC_X     = 0x03
OUT_MODE_MAGNETIC_Y     = 0x04

class CompassError(Exception):
  """OlympusCommError
    
    Errors associated with COMPASS
      Incorrect settings
  """
  def __init__(self, value):
    self.value = value
  def __str__ (self):
    return repr(self.value)


class HMC6352:
  """HMC632

  Communicates the he HMC6352 compass over I2C
  """
  
  def __init__(self, oly, i2c_dev_index):
    self.o = oly
    self.i2c = i2c.I2C(oly, i2c_dev_index)

  def read_compass_heading(self):
    """read_compass_heading

    returns a heading in 10th's of a degree

    Args:
      Nothing

    Returns:
      float number representing the heading

    Raises:
      OlympusCommError: Error in communication
      I2CError: Error in I2C communication
    """
    write_data = Array('B', [HEADING_ADDRESS])
    read_data = self.i2c.read_from_i2c(I2C_ADDRESS, write_data, HEADING_READ_SIZE)

    #process the data
    heading_int = 0
    heading_int = read_data[0] << 8 | read_data[1]

    heading = heading_int * 0.1

    return heading

  def read_magnetic_value(self):
    """read_magnetic_value

    returns a signed integer of the magnetic settings

    Args:
      Nothing

    Returns:
      signed integer of magnetic heading

    Raises:
      OlympusCommError: Error in communication
      I2CError: Error in I2C communication
    """
    write_data = Array('B', [HEADING_ADDRESS])
    read_data = self.i2c.read_from_i2c(I2C_ADDRESS, write_data, HEADING_READ_SIZE)

    #process the data
    h_string = read_data.tostring()

    value = struct.unpack('h', h_string)

    return value

  def set_operation_mode(self, mode):
    """set_operation_mode

    sets the mode of the compass mode, supported modes are:

    Args:
      mode: modes can be or'ed together
        Frequencies:
          MODE_1HZ
          MODE_5HZ
          MODE_10HZ
          MODE_20HZ

        Periodic Reset
          MODE_PERIODIC_SET

        Operation:
          MODE_STANDBY
          MODE_QUERY
          MODE_CONTINUOUS

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
      I2CError: Error in I2C communication
      CompassError: User specified an invaid mode
    """
    if (mode & 0x80) > 0: 
      raise CompassError("bit 7 should be set to 0")
    if (mode & 0x08) > 0:
      raise CompassError("bit 3 should be set to 0")
    if (mode & 0x04) > 0:
      raise CompassError("bit 2 should be set to 0")
    if (mode & 0x03) == 0x03:
      raise CompassError("Operation Mode invalid")

    write_data('B', [RAM_WRITE_ADDRESS, RAM_ADDRESS_OP_MODE, mode])
    self.i2c.write_to_i2c(I2C_ADDRESS, write_data)


  def get_operation_mode(self):
    """get_operation_mode
 
    gets the compass operation mode
 
    Args:
      Nothing
 
    Returns:
      Integer represeting the specfiied mode
        Frequencies:
          MODE_1HZ
          MODE_5HZ
          MODE_10HZ
          MODE_20HZ

        Periodic Reset
          MODE_PERIODIC_SET

        Operation:
          MODE_STANDBY
          MODE_QUERY
          MODE_CONTINUOUS
 
    Raises:
      OlympusCommError: Error in communication
      I2CError: Error in I2C communication
    """
 
    write_data = Array('B', [RAM_READ_ADDRESS, RAM_ADDRESS_OP_MODE])
    read_data = self.i2c.read_from_i2c(I2C_ADDRESS, write_data, OP_MODE_READ_SIZE)
    value = read_data[0]
    return value

  def print_operation_mode(self, mode):
    """print_operation_mode
    
    prints out the operation mode in a readible format

    Args:
      mode: operation mode

    Returns:
      Nothing

    Raises:
      Nothing
    """
    print "Operation Mode (%X)" % mode
    print "Update rate:\t",
    if (mode & 0x60) == MODE_1HZ:
      print "1 Hz"
    if (mode & 0x60) == MODE_5HZ:
      print "5 Hz"
    if (mode & 0x60) == MODE_10HZ:
      print "10 Hz"
    if (mode & 0x60) == MODE_20HZ:
      print "20 Hz"

    print "Periodic:\t",
    if (mode & 0x10) == MODE_PERIODIC_SET:
      print "set"
    else:
      print "reset"

    print "Operation Mode:\t",
    if (mode & 0x03) == MODE_STANDBY:
      print "standby"
    if (mode & 0x03) == MODE_QUERY:
      print "query"
    if (mode & 0x03) == MODE_CONTINUOUS:
      print "continuous"
    if (mode & 0x03) == 0x03:
      print "illegal mode"

  def set_output_mode(self, out_mode):
    """set_output_mode

    sets the output mode of the compass mode, supported modes are:

    Args:
      mode: the following modes are supported
        MODE_HEADING
        MODE_RAW_MAGNETIC_X
        MODE_RAW_MAGNETIC_Y
        MODE_MAGNETIC_X
        MODE_MAGNETIC_Y

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
      I2CError: Error in I2C communication
      CompassError: User specified an invaid mode
    """
    if out_mode > 0x04:
      raise CompassError("Illigal output mode")

    write_data = Array('B', [RAM_WRITE_ADDRESS, RAM_ADDRESS_OUT_MODE, out_mode])
    self.i2c.write_to_i2c(I2C_ADDRESS, write_data)


  def get_output_mode(self):
    """get_output_mode

    gets the output mode of the compass

    Args:
      Nothing

    Returns:
      MODE_HEADING
      MODE_RAW_MAGNETIC_X
      MODE_RAW_MAGNETIC_Y
      MODE_MAGNETIC_X
      MODE_MAGNETIC_Y

    Raises:
      OlympusCommError: Error in communication
      I2CError: Error in I2C communication
    """
    write_data = Array('B', [RAM_READ_ADDRESS, RAM_ADDRESS_OUT_MODE])
    read_data = self.i2c.read_from_i2c(I2C_ADDRESS, write_data, OUT_MODE_READ_SIZE)
    value = read_data[0]
    return value

  def print_output_mode(self, out_mode):
    """print_output_mode

    prints out the output mode of the compass

    Args:
      out_mode: output mode

    Returns:
      Nothing

    Raises:
      Nothing
    """
    print "Output Mode (%X)" % out_mode
    format_mode = out_mode & 0x07

    if format_mode == OUT_MODE_HEADING:
      print "\t\tHeading"
    if format_mode == OUT_MODE_RAW_MAGNETIC_X:
      print "\t\tRaw Magnetic X Value"
    if format_mode == OUT_MODE_RAW_MAGNETIC_Y:
      print "\t\tRaw Magnetic Y Value"
    if format_mode == OUT_MODE_MAGNETIC_X:
      print "\t\tMagnetic X Value"
    if format_mode == OUT_MODE_MAGNETIC_Y:
      print "\t\tMagnetic Y Value"


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

  compass = HMC6352(oly, i2c_index)

  mode = compass.get_operation_mode() 
  print ""
  compass.print_operation_mode(mode)
  print ""

  out_mode = compass.get_output_mode()
  compass.print_output_mode(out_mode)

  heading = compass.read_compass_heading()
  print "Heading: %f" % heading

  print ""
  print "Set raw X Mode"
  compass.set_output_mode(OUT_MODE_RAW_MAGNETIC_X)

  value = compass.read_magnetic_value()
  print "Value: %d" % value

  compass.set_output_mode(OUT_MODE_HEADING)
