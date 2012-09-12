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

""" Console

Facilitates communication with the Console core independent of communication
medium

For more details see:

"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

import time

from array import array as Array

from userland import olympus


CONTROL                     = 0
STATUS                      = 1

#Control bit values
CONTROL_EN                  = 1 << 1

class ConsoleError(Exception):
  """ConsoleError
    
    Errors associated with Console
      Incorrect settings
  """
  def __init__(self, value):
    self.value = value
  def __str__ (self):
    return repr(self.value)


class Console:
  """Console
    
    communiction with Console core
  """

  def __init__ (self, olympus, dev_id=None, debug=False):
    self.dev_id = dev_id
    self.o = olympus
    self.debug = debug

  def set_dev_id(self, dev_id):
    self.dev_id = dev_id

  def get_control(self):
    """get_control
    
    reads the control register

    Args:
      Nothing

    Return:
      32-bit control register value

    Raises:
      OlympusCommError: Error in communication
    """
    return self.o.read_register(self.dev_id, CONTROL)

  def set_control(self, control):
    """set_control
    
    write the control register

    Args:
      control: 32-bit control value

    Return:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    self.o.write_register(self.dev_id, CONTROL, control)


  def enable(self, enable):
    """enable
    
    enable the console to take control of the memory bus
 
    Args:
      enable: 
        True (allows the console to control the memory bus
        False (releives control of the memory bus
 
    Returns:
      Nothing
 
    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if enable:
      control = control | CONTROL_EN
    else:
      control = control & (~CONTROL_EN)
    self.set_control(control)

  def is_enabled(self):
    """is_enabled

    returns true if the console is enabled

    Args:
      Nothing

    Returns:
      True if console is enabled

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if (control & CONTROL_EN) > 0:
      return True
    return False

def unit_test(oly, dev_id):
  print "Unit test"
  console = Console(oly, dev_id)

  print "Check if core is enabled"
  print "enabled: " + str(console.is_enabled())

  print "Enable core"
  console.enable(True)

  print "Check if core is enabled"
  print "enabled: " + str(console.is_enabled())

  print "Enable core"
  console.enable(False)

  print "Check if core is enabled"
  print "enabled: " + str(console.is_enabled())


  print "Check to see if the memory has the correct data"
  num_devices = oly.get_number_of_devices()
  for dev_index in range (0, num_devices):
    memory_device = oly.is_memory_device(dev_index)
    dev_offset = oly.get_device_address(dev_index)
    dev_size = oly.get_device_size(dev_index)
    device_id = oly.get_device_id(dev_index)


    if (device_id == 5):
      print "Found a memory device"
      print "Read address 0"

    mem_bus = oly.is_memory_device(dev_index)
    if mem_bus:
      print "Memory is on Memory bus"
    else:
      print "Memory is on Peripheral bus"

    data_in = oly.read(dev_index, 0, 1, mem_bus)
    print "data read: %s" % str(data_in)

