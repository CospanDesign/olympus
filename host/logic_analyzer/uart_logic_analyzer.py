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

""" UART Logic Analyzer

Facilitates communication with the Logic Analyzer core through UART

For more details see:

http://wiki.cospandesign.com/index.php?title=Wb_logic_analyzer

"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

import serial
import time
import struct

from array import array as Array

#Command
PING                = 0
WRITE_ENABLE        = 1
READ_ENABLE         = 2
GET_SIZE            = 3
WRITE_TRIGGER       = 4
WRITE_MASK          = 5
WRITE_TRIGGER_AFTER = 6
WRITE_TRIGGER_EDGE  = 7
WRITE_BOTH_EDGES    = 8
WRITE_REPEAT_COUNT  = 9

class UARTLAError (Exception):
  """UARTLAError

  Errors associated with the UART Logic Analyzer
  """
  def __init__(self, value):
    self.value = value
  def __str__ (self):
    return repr(self.value)


class LogicAnalyzer:
  """Logic Analyzer

  Logic Analyzer driver
  """

  def __init__(self, device_name='/dev/ttyUSB0', baudrate = 57600):
    self.s = None
    self.open_serial(device_name, baudrate)

  def open_serial(self, dev_name='/dev/ttyUSB0', baudrate = 57600):
    self.s = serial.Serial(dev_name, baudrate, timeout = 2, stopbits = 2)
    print "Opened!"
    self.s.flush()
    if (self.s is None):
      print ("Error openeing serial port :(")

  def ping(self):
    self.s.flush()
    self.s.write("W%X\n" % PING) 
    response = self.s.read(4)
    self.response_okay(response, "Ping failed")

  def set_enable_capture(self, enable):
    data_out = "W%X" % WRITE_ENABLE
    if enable:
      data_out += "1"
    else:
      data_out += "0"

    data_out += "\n"
    #print "set enable capture %s" % data_out
    self.s.flush()
    self.s.write(data_out);
    response = self.s.read(4)
    self.response_okay(response, "Set capture enable failed")

  def is_enable_set(self):
    data_out = "W%X\n" % READ_ENABLE
    self.s.flush()
    self.s.write(data_out)
    response = self.s.read(5)
    self.response_okay(response, "Is Enabled set failed")
    if response[2] == "0":
      return False
    elif response[2] == "1":
      return True
    
  def set_trigger(self, trigger):
    data_out = "W%X%08X\n" % (WRITE_TRIGGER, trigger)
    self.s.flush()
    self.s.write(data_out);
    response = self.s.read(4)
    self.response_okay(response, "Set Trigger Failed")

  def set_mask(self, mask):
    data_out = "W%X%08X\n" % (WRITE_MASK, mask)
    self.s.flush()
    self.s.write(data_out);
    response = self.s.read(4)
    self.response_okay(response, "Set Mask Failed")

  def set_trigger_after(self, trigger_after):
    data_out = "W%X%08X\n" % (WRITE_TRIGGER_AFTER, trigger_after)
    self.s.flush()
    self.s.write(data_out);
    response = self.s.read(4)
    self.response_okay(response, "Set Trigger After Failed")

  def set_trigger_edge(self, trigger_edge):
    data_out = "W%X%08X\n" % (WRITE_TRIGGER_EDGE, trigger_edge)
    self.s.flush()
    self.s.write(data_out);
    response = self.s.read(4)
    self.response_okay(response, "Set Trigger Edge Failed")

  def set_both_edges(self, both_edges):
    data_out = "W%X%08X\n" % (WRITE_BOTH_EDGES, both_edges)
    self.s.flush()
    self.s.write(data_out);
    response = self.s.read(4)
    self.response_okay(response, "Set Both Edges Failed")

  def set_repeat_count(self, repeat_count):
    data_out = "W%X%08X\n" % (WRITE_REPEAT_COUNT, repeat_count)
    self.s.flush()
    self.s.write(data_out);
    response = self.s.read(4)
    self.response_okay(response, "Set Repeat Count Failed")

  def get_data_length(self):
    data_out = "W%X\n" % GET_SIZE 
    self.s.flush()
    self.s.write(data_out)
    response = self.s.read(12)
    self.response_okay(response, "Get data length failed")

    return (int(response[2:10], 16))


  def response_okay(self, response, response_message):
    if len(response) == 0:
      self.s.flushOutput()
      raise UARTLAError("UART timed out while waiting for response")
    if response[:2] != "RS":
      self.s.flushOutput()
      raise UARTLAError(response_message + ": " + response)

  def capture_data(self, data_length, timeout = 5):
    prev_timeout = self.s.timeout
    self.s.timeout = timeout
    data_length = data_length + 1
    total_length = data_length * 8
    data = ""
    #temp = "0"
    data = self.s.read((data_length * 8) + 2)
    """
    while ((len(data) < total_length) and len(temp) > 0):
      temp = self.s.read(data_length * 8) 
      data += temp
    """

    #print "Expected data size: %d" % (data_length * 8)
    #print "Length of read data: %d" % len(data)
    self.s.flushInput()
    #if len(temp) == 0:
    #  return Array('L')

    if (len(data)) == 0:
      return Array('L')
    #print "Got a response:\n %s" % data
    #print "Got a response"
    self.s.timeout = prev_timeout
    #print "data length: %d" % len(data)
    hex_data = Array('B', data)
    
    data_out = Array('L')

    for i in range (0, data_length):
      data_out.append(  hex_data[(i*8) + 0] << 27 | \
                        hex_data[(i*8) + 1] << 24 | \
                        hex_data[(i*8) + 2] << 20 | \
                        hex_data[(i*8) + 3] << 16 | \
                        hex_data[(i*8) + 4] << 12 | \
                        hex_data[(i*8) + 5] << 8  | \
                        hex_data[(i*8) + 6] << 4  | \
                        hex_data[(i*8) + 7])

    return data_out
      


if __name__ == "__main__":
  print "Openning..."
#  try:
  la = LogicAnalyzer()

  print "Ping..."
  la.ping()
  la.set_enable_capture(False)

  print "Check if enabled..."
  if la.is_enable_set():
    print "Enabled Set"
  else:
    print "Enabled not set"

  print "Set Trigger"
  la.set_trigger(0x00000001)
  la.set_mask(0x00000001)
  la.set_trigger_after(0x00000000)
  la.set_trigger_edge(0x00000000)
  la.set_both_edges(0x00000000)
  la.set_repeat_count(0x00000000)

  print "Get Size: "
  size = la.get_data_length()
  print "Size: %08X" % size

  print "Set Enable"
  la.set_enable_capture(True)
  print "Press a button!"
  data_out = la.capture_data(size)
  if len(data_out) > 0:
    for i in data_out:
      print "0x%08X" % i


#  except UARTLAError as err:
#    print "UART Logic Analyzer Error: %s" % str(err)


  
     
