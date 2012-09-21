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

""" Dionysus

Main userland communication tool with the Dionysus board

"""
__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

""" Changelog:
09/21/2012
  -added core dump function to retrieve the state of the master when a crash
  occurs
08/30/2012
  -Initial Commit

"""

import time
import random
import sys
import os
import string
import json

from userland.olympus import Olympus
from userland.olympus import OlympusCommError
from pyftdi.pyftdi.ftdi import Ftdi
from array import array as Array

class Dionysus(Olympus):
  """Dionysus

  Concrete Class that implements Dionysus specific communication functions
  """

  def __init__(self, idVendor=0x0403, idProduct=0x8530, debug = False):
    Olympus.__init__(self, debug)
    self.vendor = idVendor
    self.product = idProduct
    self.dev = Ftdi()
    self._open_dev()

    self.name = "Dionysus"

  def __del__(self):
    self.dev.close()

  def _open_dev(self):
    """_open_dev
    
    Open an FTDI communication channel

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      Exception
    """
    frequency = 30.0E6
#Latency can go down t 2 but when set there is a small chance that there is a crash
    latency = 4
    self.dev.open(self.vendor, self.product, 0)
    # Drain input buffer
    self.dev.purge_buffers()

    # Reset
    # Enable MPSSE mode
    self.dev.set_bitmode(0x00, Ftdi.BITMODE_SYNCFF)
    # Configure clock

    frequency = self.dev._set_frequency(frequency)
    # Set latency timer
    self.dev.set_latency_timer(latency)
    # Set chunk size
    self.dev.write_data_set_chunksize(0x10000)
    self.dev.read_data_set_chunksize(0x10000)

    self.dev.set_flowctrl('hw')
    self.dev.purge_buffers()


  def read(self, device_id, address, length = 1, mem_device = False):
    """read

    read data from the Olympus image

    Args:
      device_id: Device identification number, found in the DRT
      address: Address of the register/memory to read
      mem_device: True if the device is on the memory bus
      length: Number of 32 bit words to read from the FPGA

    Returns:
      A byte array containing the raw data returned from Olympus

    Raises:
      OlympusCommError
    """
    read_data = Array('B')

    write_data = Array('B', [0xCD, 0x02]) 
    if mem_device:
      if self.debug:
        print "memory device"
      write_data = Array ('B', [0xCD, 0x12])
  
    fmt_string = "%06X" % (length) 
    write_data.fromstring(fmt_string.decode('hex'))
    offset_string = "00"
    if not mem_device:
      offset_string = "%02X" % device_id

    write_data.fromstring(offset_string.decode('hex'))

    addr_string = "%06X" % address
    write_data.fromstring(addr_string.decode('hex'))
    if self.debug:
      print "data read string: " + str(write_data)

    self.dev.purge_buffers()
    self.dev.write_data(write_data)

    timeout = time.time() + self.read_timeout
    rsp = Array('B')
    while time.time() < timeout:
      response = self.dev.read_data(1)
      if len(response) > 0:
        rsp = Array('B')
        rsp.fromstring(response)
        if rsp[0] == 0xDC:
          if self.debug:
            print "Got a response"  
          break

    if len(rsp) > 0:
      if rsp[0] != 0xDC:
        if self.debug:
          print "Response not found"  
        raise OlympusCommError("Did not find identification byte (0xDC): %s" % str(rsp))
    else:
      if self.debug:      
        print "No Response found"
      raise OlympusCommError("Timeout while waiting for a response")

    #I need to watch out for the modem status bytes
    read_count = 0
    response = Array('B')
    rsp = Array('B')
    timeout = time.time() + self.read_timeout

    while (time.time() < timeout) and (read_count < (length * 4 + 8)):
      response = self.dev.read_data((length * 4 + 8 ) - read_count)
      temp  = Array('B')
      temp.fromstring(response)
      #print "temp: %s", str(temp)
      if (len(temp) > 0):
        rsp += temp
        read_count = len(rsp)
    
    if self.debug:
      print "read length = %d, total length = %d" % (len(rsp), (length * 4 + 8))
      print "time left on timeout: %d" % (timeout - time.time())

    if self.debug:
      print "response length: " + str(length * 4 + 8)
      print "response status:\n\t" + str(rsp[:8])
      print "response data:\n" + str(rsp[8:])

    return rsp[8:]
    

  def write(self, device_id, address, data=None, mem_device = False):
    """write

    Write data to an Olympus image

    Args:
      device_id: Device identification number, found in the DRT
      address: Address of the register/memory to read
      mem_device: True if the device is on the memory bus
      data: Array of raw bytes to send to the device

    Returns:
      Nothing

    Raises:
      OlympusCommError
    """
    length = len(data) / 4

    # ID 01 NN NN NN OO AA AA AA DD DD DD DD
      # ID = ID BYTE (0xCD)
      # 01 = Write Command
      # NN = Size of write (3 bytes)
      # OO = Offset of device
      # AA = Address (4 bytes)
      # DD = Data (4 bytes)

    #create an array with the identification byte (0xCD)
    #and code for write (0x01)

    data_out = Array('B', [0xCD, 0x01]) 
    if mem_device:
      if self.debug:
        print "memory device"
      data_out = Array ('B', [0xCD, 0x11])
    
    """
    print "write command:\n\t" + str(data_out[:9])
    for i in range (0, len(data_out)):
      print str(hex(data_out[i])) + ", ",
    print " "
    """

 

    #append the length into the frist 32 bits
    fmt_string = "%06X" % (length) 
    data_out.fromstring(fmt_string.decode('hex'))
    offset_string = "00"
    if not mem_device:
      offset_string = "%02X" % device_id
    data_out.fromstring(offset_string.decode('hex'))
    addr_string = "%06X" % address
    data_out.fromstring(addr_string.decode('hex'))
    
    data_out.extend(data)

    """
    #if (self.debug):
    print "data write string:\n"
    print "write command:\n\t" + str(data_out[:9])
    for i in range (0, 9):
      print str(hex(data_out[i])) + ", ",
    print " "
    """


    #print "write data:\n" + str(data_out[9:])

    #avoid the akward stale bug
    self.dev.purge_buffers()

    self.dev.write_data(data_out)
    rsp = Array('B')

    timeout = time.time() + self.read_timeout
    while time.time() < timeout:
      response = self.dev.read_data(1)
      if len(response) > 0:
        rsp = Array('B')
        rsp.fromstring(response)
        if rsp[0] == 0xDC:
          if self.debug:
            print "Got a response"  
          break

    if (len(rsp) > 0):
      if rsp[0] != 0xDC:
        if self.debug:
          print "Response not found"  
        raise OlympusCommError("Did not find identification byte (0xDC): %s" % str(rsp))

    else:
      if self.debug:
        print "No Response"
      raise OlympusCommError("Timeout while waiting for a response")

    response = self.dev.read_data(8)
    rsp = Array('B')
    rsp.fromstring(response)

    if self.debug:
      print "Response: " + str(rsp)

  def ping(self):
    """ping

    Pings the Olympus image

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      OlympusCommError
    """
    data = Array('B')
    data.extend([0XCD, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]);
    if self.debug:
      print "Sending ping...",
    self.dev.write_data(data)
    rsp = Array('B')
    temp = Array('B')

    timeout = time.time() + self.read_timeout

    while time.time() < timeout:
      response = self.dev.read_data(5)
      if self.debug:
        print ".",
      rsp = Array('B')
      rsp.fromstring(response)
      temp.extend(rsp)
      if 0xDC in rsp:
        if self.debug:
          print "Got a response"  
          print "Response: %s" % str(temp)
        break

    if not 0xDC in rsp:
      if self.debug:
        print "ID byte not found in response"  
        print "temp: " + str(temp)
      raise OlympusCommError("Ping response did not contain ID: %s" % str(temp))

    index  = rsp.index(0xDC) + 1

    read_data = Array('B')
    read_data.extend(rsp[index:])
    num = 3 - index
    read_data.fromstring(self.dev.read_data(num))
    if self.debug:
      print "Success!"
    return


  def reset(self):
    """reset

    Software reset the Olympus FPGA Master, this may not actually reset the
    entire FPGA image

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      OlympusCommError: A failure of communication is detected
    """
    data = Array('B')
    data.extend([0XCD, 0x03, 0x00, 0x00, 0x00]);
    if self.debug:
      print "Sending reset..."
    self.dev.purge_buffers()
    self.dev.write_data(data)

  def dump_core(self):
    """dump_core

    reads the state of the wishbone master prior to a reset, useful for
    debugging

    Args:
      Nothing

    Returns:
      Array of 32-bit values to be parsed by core_analyzer

    Raises:
      AssertionError: This function must be overriden by a board specific
      implementation
      OlympusCommError: A failure of communication is detected
    """

    data = Array('B')
    data.extend([0xCD, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]);
    print "Sending core dump request..."

    self.dev.purge_buffers()
    self.dev.write_data(data)

    core_dump = Array('L')
    wait_time = 5
    timeout = time.time() + wait_time

    temp = Array ('B')
    while time.time() < timeout:
      response = self.dev.read_data(1)
      rsp = Array('B')
      rsp.fromstring(response)
      temp.extend(rsp)
      if 0xDC in rsp:
        print "Got a response"  
        break

    if not 0xDC in rsp:
      print "Response not found"  
      raise OlympusCommError("Response Not Found")

    rsp = Array('B')
    read_total = 4
    read_count = len(rsp)

    #get the number of items from the address
    timeout = time.time() + wait_time
    while (time.time() < timeout) and (read_count < read_total):
      response = self.dev.read_data(read_total - read_count)
      temp  = Array('B')
      temp.fromstring(response)
      if (len(temp) > 0):
        rsp += temp
        read_count = len(rsp)

    print "Length of read: %d" % len(rsp)
    print "Data: %s" % str(rsp)
    count  = ( rsp[1] << 16 | rsp[2] << 8 | rsp[3]) * 4
    print "Number of core registers: %d" % (count / 4)

    #get the core dump data
    timeout = time.time() + wait_time
    read_total  = count
    read_count  = 0
    temp = Array ('B')
    rsp = Array('B')
    while (time.time() < timeout) and (read_count < read_total):
      response = self.dev.read_data(read_total - read_count)
      temp  = Array('B')
      temp.fromstring(response)
      if (len(temp) > 0):
        rsp += temp
        read_count = len(rsp)

    print "Length read: %d" % (len(rsp) / 4)
    print "Data: %s" % str(rsp)
    core_data = Array('L')
    for i in range (0, count, 4):
      print "count: %d" % i
      core_data.append(rsp[i] << 24 | rsp[i + 1] << 16 | rsp[i + 2] << 8 | rsp[i + 3])
    
    #if self.debug:
    print "core data: " + str(core_data)

    return core_data



 

  def wait_for_interrupts(self, wait_time = 1):
    """wait_for_interrupts
    
    listen for interrupts for the specified amount of time

    Args:
      wait_time: the amount of time in seconds to wait for an interrupt

    Returns:
      True: Interrupts were detected
      False: No interrupts detected

    Raises:
      Nothing
    """
    timeout = time.time() + wait_time

    temp = Array ('B')
    while time.time() < timeout:
      response = self.dev.read_data(1)
      rsp = Array('B')
      rsp.fromstring(response)
      temp.extend(rsp)
      if 0xDC in rsp:
        if self.debug:
          print "Got a response"  
        break

    if not 0xDC in rsp:
      if self.debug:
        print "Response not found"  
      return False

    read_total = 9
    read_count = len(rsp)

    #print "read_count: %s" % str(rsp)
    while (time.time() < timeout) and (read_count < read_total):
      response = self.dev.read_data(read_total - read_count)
      temp  = Array('B')
      temp.fromstring(response)
      #print "temp: %s", str(temp)
      if (len(temp) > 0):
        rsp += temp
        read_count = len(rsp)

    #print "read_count: %s" % str(rsp)
   

    index  = rsp.index(0xDC) + 1

    read_data = Array('B')
    read_data.extend(rsp[index:])
    #print "read_data: " + str(rsp)

    self.interrupts = read_data[-4] << 24 | read_data[-3] << 16 | read_data[-2] << 8 | read_data[-1]
    
    if self.debug:
      print "interrupts: " + str(self.interrupts)
    return True


  def comm_debug(self):
    """comm_debug

    A function that the end user will probably not interract with
    This is here to simply debug a communication medium

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      Nothing
    """
    #self.dev.set_dtr_rts(True, True)
    #self.dev.set_dtr(False)
    print "CTS: " + str(self.dev.get_cts())
#    print "DSR: " + str(self.dev.get_dsr())
    s1 = self.dev.modem_status()
    print "S1: " + str(s1)


  # self.dev.set_dtr(True)
    #time.sleep(.01)
#   response = self.dev.read_data(7)
#   rsp.fromstring(response)
#   print "rsp: " + str(rsp) 
#     if not self.dev.get_dsr():
#       print "DSR low"


if __name__ == '__main__':
  print "Dionysus: Run through low level comm test"
  dionysus = Dionysus(debug = True)
  dionysus.reset()
  dionysus.ping()
  #dionysus.read(0, 0, 0)
  #dionysus.write(0, 0)

