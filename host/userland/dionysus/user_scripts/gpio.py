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

""" GPIO

Facilitates communication with the GPIO core independent of communication
medium

For more details see:

http://wiki.cospandesign.com/index.php?title=Wb_gpio

TODO: Implement debounce
"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

import time
from array import array as Array

import olympus
from olympus import OlympusCommError


#Register Constants
GPIO_PORT           = 0
GPIO_OUTPUT_ENABLE  = 1
INTERRUPTS          = 2
INTERRUPT_ENABLE    = 3
INTERRUPT_EDGE      = 4


class GPIO:
  """GPIO
    
    communication with a GPIO core
  """

  def __init__(self, olympus, dev_id = None, debug=False):
    self.dev_id = dev_id
    self.o = olympus
    self.debug = debug

  def set_dev_id(self, dev_id):
    self.dev_id = dev_id

  def set_port_direction(self, direction_mask):
    """set_port_diretion

    Set the direction of the port

    Args:
      direction_mask: 32-it value that will set the direction of the port

    Return:
      Nothing

    Raises:
      OlympusCommError
    """
    if self.debug:
      print "Writing GPIO direction"

    direction_value = Array('B', [0x00, 0x00, 0x00, 0x00])

    direction_value[0] = (direction_mask >> 24) & 0xFF
    direction_value[1] = (direction_mask >> 16) & 0xFF
    direction_value[2] = (direction_mask >> 8) & 0xFF
    direction_value[3] = (direction_mask) & 0xFF


    self.o.write(self.dev_id, GPIO_OUTPUT_ENABLE, direction_value)

  def set_port_raw(self, value):
    """set_port_raw
    
    Set multiple GPIO output values

    Args:
      value: 32-bit value that will replace the current ports

    Return:
      Nothing

    Raises:
      OlympusCommError
    """
    port_value = Array('B', [0x00, 0x00, 0x00, 0x00])

    port_value[0] = (value >> 24) & 0xFF
    port_value[1] = (value >> 16) & 0xFF
    port_value[2] = (value >> 8) & 0xFF
    port_value[3] = (value) & 0xFF


    if self.debug:
      print "Writing GPIO raw value"
    self.o.write(self.dev_id, GPIO_PORT, port_value)

  def get_port_raw(self):
    """get_port_raw
    
    Get multiple GPIO input values

    Args:
      Nothing

    Return:
      32-bit value representing the port values

    Raises:
      OlympusCommError
    """
    if self.debug:
      print "Reading GPIO raw value"

    port = self.o.read(self.dev_id, GPIO_PORT, 1)
    port_raw = port[0] << 24 | port[1] << 16 | port[2] << 8 | port[3]

    return port_raw

  def set_bit_value(self, bit, value):
    """set_bit_value
    
    Sets an individual bit with the speified value (1, or 0)

    Args:
      bit: the bit of the port to set
      value: 1 or 0

    Return:
      Nothing

    Raises:
      OlympusCommError
    """
    if self.debug:
      print "Setting individual bit value"

    port_raw = self.get_port_raw()
    
    bit_shifted = 0x00000000
    bit_shifted = 1 << bit

    if self.debug:
      print "Value: %d" % value
      print "Bit: %d" % bit
      print "bit shift value %X" % bit_shifted
      print "port value: %X" % port_raw

    if value > 0:
      port_raw = port_raw | bit_shifted

    else:
      port_raw = port_raw & (~bit_shifted)

    if self.debug:
      print "New port value: %X" % port_raw

    self.set_port_raw(port_raw)

  def get_bit_value(self, bit):
    """get_bit_value
    
    Gets an individual bit

    Args:
      bit: index of the bit to get

    Returns:
      1, 0

    Raises:
      OlympusCommError
    """

    if self.debug:
      print "getting individual bit value"
    port = self.get_port_raw()
 
    bit_shifted = 1 << bit

    if (bit_shifted & port) > 0:
      return 1

    return 0


  def set_interrupt_enable(self, interrupt_enable):
    """set_interrupt_enable

    Enables/Disables interrupts

    Args:
      interrupt_enable: 32-bit enable (1), disable(0) mask

    Return:
      Nothing

    Raises:
      OlympusComError
    """
    if self.debug:
      print "Setting interrupt mask"

    interrupt_array = Array('B', [0x00, 0x00, 0x00, 0x00])

    interrupt_array[0] = (interrupt_enable >> 24) & 0xFF
    interrupt_array[1] = (interrupt_enable >> 16) & 0xFF
    interrupt_array[2] = (interrupt_enable >> 8) & 0xFF
    interrupt_array[3] = (interrupt_enable) & 0xFF

    self.o.write(self.dev_id, INTERRUPT_ENABLE, interrupt_array)

  def get_interrupt_enable(self):
    """get_interrupt_enable

    Returns the interrupt mask

    Args:
      Nothing

    Returns:
      32-bit interrupt mask value

    Raises:
      Nothing
    """
    level_array = self.o.read(self.dev_id, INTERRUPT_ENABLE, 1)
    interrupt_edge = 0
    interrupt_edge = level_array[0] << 24 | level_array[1] << 16 | level_array[2] << 8 | level_array[3]
    return interrupt_edge

  def set_interrupt_edge(self, interrupt_edge):
    """set_interrupt_edge

    Interrupt triggers on high (1) or low (0)

    Args:
      Interrupt_level: 32-bit enable (1), disable (0) mask

    Return:
      Nothing

    Raises:
      OlympusCommError
    """
    if self.debug:
      print "Setting interrupt level"

    edge_array = Array('B', [0x00, 0x00, 0x00, 0x00])

    edge_array[0] = (interrupt_edge >> 24) & 0xFF
    edge_array[1] = (interrupt_edge >> 16) & 0xFF
    edge_array[2] = (interrupt_edge >> 8) & 0xFF
    edge_array[3] = (interrupt_edge) & 0xFF

    self.o.write(self.dev_id, INTERRUPT_EDGE, edge_array)

  def get_interrupt_edge(self):
    """get_interrupt_edge

    Returns the interrupt level

    Args:
      Nothing

    Returns:
      32-bit value contiaining the interrupt level

    Raises:
      OlympusCommError
    """
    edge_array = self.o.read(self.dev_id, INTERRUPT_EDGE, 1)
    interrupt_edge = 0
    interrupt_edge = edge_array[0] << 24 | edge_array[1] << 16 | edge_array[2] << 8 | edge_array[3]
    return interrupt_edge

  def get_interrupts(self):
    """get_interrupts

    Returns a 32-bit value representing the interrupts on the specified pins

    Args:
      Nothing

    Returns:
      32-bit value containing the interrupts

    Raises:
      OlympusCommError
    """
    interrupt_array = self.o.read(self.dev_id, INTERRUPTS, 1)
    interrupts = interrupt_array[0] << 24 | interrupt_array[1] << 16 | interrupt_array[2] << 8 | interrupt_array[3]
    return interrupts


def unit_test(oly, dev_index):
  """unit_test

  Run the unit test of the GPIO
  """
  gpio = GPIO(oly, dev_index)

  print "Testing output ports (like LEDs)"

  print "Flashing all the outputs for one second"

  print "Set all the ports to outputs"
  gpio.set_port_direction(0xFFFFFFFF)

  print "Set all the values to 0"
  gpio.set_port_raw(0xFFFFFFFF)
  time.sleep(1)
  gpio.set_port_raw(0x00000000)

  """
  print "flash only one bit"
  period = .1
  for i in range (0, 10):
    gpio.set_bit_value(0, 1)
    time.sleep( (i + 1) * (period / 10.0))
    gpio.set_bit_value(0, 0)
    time.sleep(period - ((i + 1) * (period / 10.0)))
  """

  print "Reading inputs (Like buttons) in 2 second"
  gpio.set_port_direction(0x00000000)
  
  time.sleep(2)
  print "Read value: " + hex(gpio.get_port_raw())
  print "Reading inputs (Like buttons) in 2 second"
  time.sleep(2)
  print "Read value: " + hex(gpio.get_port_raw())


  print "Testing Interrupts, setting interrupts up for positive edge detect"
  gpio.set_interrupt_edge(0xFFFFFFFF)
  gpio.set_interrupt_enable(0xFFFFFFFF)

  print "Waiting for 5 seconds for the interrupts to fire"
  if (gpio.o.wait_for_interrupts(5)):
    if (gpio.o.is_interrupt_for_slave(gpio.dev_id)):
      print "Interrupt for GPIO detected!"
      print "Interrupts: " + hex(gpio.get_interrupts())
      print "Read value: " + hex(gpio.get_port_raw())

    


 
