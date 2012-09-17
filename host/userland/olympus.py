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

""" olympus

Abstract interface for working the the Olympus FPGA images

This only defines the functions required for communiction, in order to
implement a new board a user must implement all the required functions

"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

#! /usr/bin/python
import time
import random
import sys
import os
import string
import json
from array import array as Array

#put olympus in the system path
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "cbuilder/drt"))
import drt as drt_controller
from drt import DRTManager


class OlympusCommError(Exception):
  """OlympusCommError
    
    Errors associated with communication
      Response Timeout
      Incorrect settings
  """
  def __init__(self, value):
    self.value = value
  def __str__ (self):
    return repr(self.value)


class Olympus:
  """Olympus
  
  Abstract class and must be overriden by a class that will implement
  device specific functions such as initialize, read, write, and ping
  """

  read_timeout  = 3
  interrupts = 0
  interrupt_address = 0
  
  def __init__(self, debug = False):
    self.name = "Olympus"
    self.debug = debug
    if debug:
      print "Debug Enabled"
    self.drt_manager = DRTManager()

  def __del__(self):
    print "Closing Olympus"


  """initialize

  This function will not be implemented within this abstract class and must be
  implemented within the lower concrete class that is device speific
  def initialize(self):
    AssertionError("initialize function is not implemented")
  """

  def set_timeout(self, timeout):
    """set_timeout

    Sets the timeout (in seconds) of the read

    Args:
      timeout: new timeout

    Returns:
      Nothing

    Raises:
      Nothing
    """
    self.timeout = timeout

  def get_timeout(self):
    """get_timeout
      
    Returns the read/write timeout in case of an error

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      Nothing
    """
    return self.timeout

  def read_register(self, device_id, address):
    """read_register

    Reads a single register from the read command and then converts it to an
    integer

    Args:
      device_id:  Device identification number, this number is found in the DRT
      address:  Address of the register/memory to read

    Returns:
      32-bit unsigned integer

    Raises:
      OlympusCommError: Error in communication
    """
    register_array = self.read(device_id, address, 1) 
    return register_array[0] << 24 | register_array[1] << 16 | register_array[2] << 8 | register_array[3]


  def read(self, device_id, address, length = 1, mem_device = False):
    """read

    Generic read command used to read data from an Olympus image, this will be
    overriden based on the communication method with the FPGA board

    standard methods include

    UART, FTDI Synchronous FIFO, Cypress USB 3.0 Interface, Beaglebone Memory
    interface

    Args:
      length: Number of 32 bit words to read from the FPGA
      device_id:  Device identification number, this number is found in the DRT
      address:  Address of the register/memory to read
      mem_device: Whether the device is on the memory bus or the peripheral bus

    Returns:
      A byte array containing the raw data returned from Olympus

    Raises:
      AssertionError: This function must be overriden by a board specific
      implementation
    """
    raise AssertionError("read function is not implemented")

  def read_memory(self, address, size):
    """read_memory

    Reads a byte array of the specified size from the specified address from
    memory

    Args:
      address: Starting location o memory to read from
      size: total number of 32-bit words to read

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    return self.read(0, address, size, mem_device=True)

  def write_register(self, device_id, address, value):
    """write_register

    Writes a single register from a 32-bit unsingned integer

    Args:
      device_id:  Device identification number, this number is found in the DRT
      address:  Address of the register/memory to read
      value:  32-bit unsigned integer to be written into the register

    Return: Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    register_array = Array('B', [0x00, 0x00, 0x00, 0x00])
    register_array[0]  = (value >> 24) & 0xFF
    register_array[1]  = (value >> 16) & 0xFF
    register_array[2]  = (value >> 8) & 0xFF
    register_array[3]  = (value) & 0xFF
    self.write(device_id, address, register_array)


  def write_memory(self, address, data):
    """write_memory

    Writes the byte of array of bytes down to the memory of the bus

    Args:
      address: Starting location of memory to write to
      data: A byte array of raw values to write to the memory

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    self.write(0, address, data, mem_device = True)

  def write(self, device_id, address, data = None, mem_device = False):
    """write
    
    Generic write command usd to write data to an Olympus image, this will be
    overriden based on the communication method with the specific FPGA board

    Args:
      device_id: Device identification number, found in the DRT
      address: Address of the register/memory to read
      mem_device: True if the device is on the memory bus
      data: Array of raw bytes to send to the device

    Returns:
      Nothing

    Raises:
      AssertionError: This function must be overriden by a board specific
      implementation
    """
    raise AssertionError("write function is not implemented")


  def read_drt(self):
    """read_drt
      
    Read the contents of the DRT

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      OlympusCommError: When a failure of communication is detected
    """
    data = Array('B')
    data = self.read(0, 0, 8)
    num_of_devices  = drt_controller.get_number_of_devices(data)
    len_to_read = num_of_devices * 8

    data = self.read(0, 0, len_to_read + 8)
    self.drt_manager.set_drt(data)

  def pretty_print_drt(self):
    """pretty_print_drt
    
    Prints out the DRT with colors and beauty

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      Nothing
    """
    self.drt_manager.pretty_print_drt()

  def get_number_of_devices(self):
    """get_number_of_devices

    Returns the number of devices found on the DRT

    Args:
      Nothing

    Returns:
      The number of devices on the DRT

    Raises:
      Nothing
    """
    return self.drt_manager.get_number_of_devices()

  def get_device_id(self, device_index):
    """get_device

    From the index within the DRT return the ID of this device

    Args:
      device_index: index of the device

    Returns:
      Standard device ID

    Raises:
      Nothing
    """
    return self.drt_manager.get_id_from_index(device_index)

  def get_device_address(self, device_index):
    """get_device_address

    From the index within the DRT return the address of where to find this 
    device

    Args:
      device_index: index of the device

    Returns:
      32-bit address of the device

    Raises:
      Nothing
    """
    return self.drt_manager.get_address_from_index(device_index)

  def get_device_size(self, device_index):
    """get_device_size

    Gets the size of the peripheral/memory

    if peripheral gets the number of registers associated with ti
    if memory gets the size of the memory

    Args:
      device_index: index of the device

    Returns:
      size

    Raises:
      Nothing
    """
    return self.drt_manager.get_size_from_index(device_index)

  def is_memory_device(self, device_index):
    """is_memory_device
    
    Queries the DRT to see if the device is on the memory bus or the 
    peripheral bus

    Args:
      device_index: Index of the device to test

    Returns:
      True: Device is on the memory bus
      False: Device is on the peripheral bus

    Raises:
      Nothing
    """
    return self.drt_manager.is_memory_device(device_index)

  def get_total_memory_size(self):
    """get_total_memory_size

    adds all the contiguous memory peripherals together and returns the
    total size
  
    Note: this memory must start at address 0

    Args:
      Nothing

    Returns:
      Size of the total memory

    Raises:
      DRTError: DRT Not defined
    """
    return self.drt_manager.get_total_memory_size()

  def ping(self):
    """ping

    Pings the Olympus image

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      AssertionError: This function must be overriden by a board specific
      OlympusCommError: When a failure of communication is detected
    """
    raise AssertionError("Ping function is not implemented")

  def reset(self):
    """reset

    Software reset the Olympus FPGA Master, this may not actually reset the
    entire FPGA image

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      AssertionError: This function must be overriden by a board specific
      implementation
      OlympusCommError: A failure of communication is detected
    """
    raise AssertionError("Reset function not implemented")

  def wait_for_interrupts(self, wait_time = 1):
    """wait_for_interrupts
    
    listen for interrupts for the specified amount of time

    Args:
      wait_time: the amount of time in seconds to wait for an interrupt

    Returns:
      True: Interrupts were detected
      False: No interrupts detected

    Raises:
      AssertionError: This function must be overriden by a board specifific
      implementation
    """
    raise AssertionError("wait_for_interrupts function i not implemented")

  def is_interrupt_for_slave(self, device_id):
    """is_interrupt_for_slave

    Test to see if the interrupt is for the specified slave

    Args:
      device_id:  device to test for

    Returns:
      True: interrupt is for device
      False: interrupt is not for the device

    Raises:
      Nothing
    """
    #print "interrupts: %X" % self.interrupts
    if ( (1 << device_id) & self.interrupts) > 0:
      return True
    return False

