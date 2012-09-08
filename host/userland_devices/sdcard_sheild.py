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

""" OLED

Facilitates communication with the OLED core independent of communication
medium

For more details see:

http://wiki.cospandesign.com/index.php?title=Wb_spi

"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

import time
import sys
import os

from array import array as Array

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from userland import olympus
from userland.dionysus import dionysus
from userland.drivers import spi

SLAVE_SELECT_BIT = 0
COMMAND_LENGTH = 64

#COMMANDS
CMD_RESET       = Array('B', [0x40, 0x00, 0x00, 0x00, 0x00])
CMD_INIT        = Array('B', [0x41, 0x00, 0x00, 0x00, 0x00])
CMD_READ_VOLT   = Array('B', [0x48, 0x00, 0x00, 0x01, 0xAA])
CMD_READ_CSD    = Array('B', [0x49, 0x00, 0x00, 0x00, 0x00])
CMD_READ_STATUS = Array('B', [0x41, 0x00, 0x00, 0x00, 0x00])


#Register Definitions
R1_IDLE_STATE     = 1 << 0
R1_ERASE_RESET    = 1 << 1
R1_ILLEGAL_CMD    = 1 << 2
R1_CRC_ERR        = 1 << 3
R1_ERASE_SEQ_ERR  = 1 << 4
R1_ADDR_ERR       = 1 << 5
R1_PARAM_ERR      = 1 << 6

class SDCARD:

  def __init__(self, oly, spi_dev_index):
    self.o = oly
    self.spi = spi.SPI(oly, spi_dev_index)
#    self.spi.set_spi_clock_rate(1000000)
    self.spi.set_spi_clock_rate(100000)
    self.spi.set_tx_polarity(False)
    self.spi.set_rx_polarity(True)
    #clear slave select bits
    
  def initialize(self):
    self.spi.set_auto_ss_control(False)
    self.spi.set_slave_select_raw(0x00)
#    self.spi.set_auto_ss_control(False)
    self.spi.set_character_length(80)
    self.spi.start_transaction()
    while self.spi.is_busy():
      print ".",
      time.sleep(0.01)

    self.spi.set_auto_ss_control(True)
    self.spi.set_spi_slave_select(SLAVE_SELECT_BIT, True)


  def generate_crc(self, data):
    crc = 0
    bits = len(data) * 8
    value = 0

    for d in data:
      value = (value << 8) | d

    #print "Value: %s" % bin(value)
    #print "Length = %d" % (len(bin(value)) - 1)
    #print "Bits: %d" % bits

    while bits > 0:
      bits -= 1
      crc = (crc << 1) ^ (0, 9) [((crc >> 6) ^ (value >> bits)) & 1]
      #print "CRC: %X" % (0xFF & crc)

    crc = crc << 1
    crc = crc | 1 
    crc = crc & 0xFF
    #print "CRC: %X" % crc
    return crc

  def print_r1_response(self, r1):
    print "R1 (%X) States:" % r1
    if (r1 & R1_IDLE_STATE) > 0:
      print "\tIDLE"
    if (r1 & R1_ERASE_RESET) > 0:
      print "\tERASE RESET"
    if (r1 & R1_ILLEGAL_CMD) > 0:
      print "\tILLEGAL COMMAND"
    if (r1 & R1_CRC_ERR) > 0:
      print "\tCRC ERROR"
    if (r1 & R1_ADDR_ERR) > 0:
      print "\tADDRESS ERROR"
    if (r1 & R1_PARAM_ERR) > 0:
      print "\tPARAMETER ERROR"
  

  def send_command(self, command, length):
    self.spi.set_character_length(length)
    crc = self.generate_crc(command)
    data = Array('B', command)
    data.append(crc)
    self.spi.set_write_data(command)
    self.spi.start_transaction()
    while self.spi.is_busy():
      print ".",
      time.sleep(0.01)
    read_data = self.spi.get_read_data(length)
    print "read_data: %s" % str(read_data)
    return read_data[len(command) + 1:]

  def get_r1_response(self, data):
    r1 = 0xFF
    for i in range (0, len(data)):
      if data[i] < 0x08:
        r1 = data[i]

    self.print_r1_response(r1)
    return r1


  def reset(self):
    print "Reset card"
    read_data = self.send_command(CMD_RESET, (len(CMD_RESET) + 3) * 8)
    print "Read data: %s" % str(read_data)
    self.get_r1_response(read_data)

  def read_voltage_range(self):
#    print "Read Volage range"
#    read_data = self.send_command(CMD_READ_VOLT, COMMAND_LENGTH + 32)
#    print "Read data: %s" % str(read_data)
#    self.get_r1_response(read_data)


    
    self.spi.set_character_length(COMMAND_LENGTH + 32)
    crc = self.generate_crc(CMD_READ_VOLT)
    data = Array('B', CMD_READ_VOLT)
    data.append(crc)

    self.spi.set_write_data(data)
    self.spi.start_transaction()
    while self.spi.is_busy():
      print ".",
      time.sleep(0.01)
  
    read_data = self.spi.get_read_data(COMMAND_LENGTH + 32)
    r1 = 0xFF
    index = 0
    for i in range (0, len(read_data)):
      if read_data[i] < 0x08:
        r1 = read_data[i]
        index = i
        #print "index: %d" % i

    self.print_r1_response(r1)
    print "read data: %s" % str(read_data)
  

  def read_status(self):
    print "Read status"
    """
    self.spi.set_character_length(COMMAND_LENGTH + 32)
    crc = self.generate_crc(CMD_READ_STATUS)
    data = Array('B', CMD_READ_STATUS)
    data.append(crc)
    self.send_command(data)
    read_data = self.spi.get_read_data(COMMAND_LENGTH + 32)
    r1 = 0xFF
    index = 0
    for i in range (0, len(read_data)):
      if read_data[i] < 0x08:
        r1 = read_data[i]
        index = i
        #print "index: %d" % i

    self.print_r1_response(r1)
    print "read data: %s" % str(read_data)
    """

  


if __name__ == "__main__":
  dyn = dionysus.Dionysus()
  dyn.ping()
  dyn.read_drt()
  gpio_index = 0
  spi_index = 0
  num_devices = dyn.get_number_of_devices()
  for dev_index in range (0, num_devices):
    device_id = dyn.get_device_id(dev_index)
    dev_offset = dyn.get_device_address(dev_index)

    if device_id == 1:
      gpio_index = dev_offset

    if device_id == 4:
      spi_index = dev_offset

  if (spi_index == 0):
    print "Couldn't find the ID of SPI device"
    sys.exit(1)

  print "Found both devices, starting SDCARD"
  print "SPI index: %d" % spi_index
  sdcard = SDCARD(dyn, spi_index)

  sdcard.initialize()
  sdcard.reset()
  sdcard.read_voltage_range()
  sdcard.read_status()



 
