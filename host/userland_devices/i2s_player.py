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

""" i2s player

Plays a song through the I2S core

sends music chunks down to the I2S core

"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

import time
import sys
import os
import wave
import struct
import getopt 

from array import array as Array

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from userland import olympus
from userland.dionysus import dionysus
from userland.drivers import i2s


class I2S_Player:
  """I2S_Player

  Plays music through the I2S device
  """

  def __init__(self, oly, dev_id):
    self.o = oly

    self.i2s = i2s.I2S(oly, dev_id)

 
  def convert_wave_to_i2s(self, wave_filename, debug=False):
    """convert_wave_to_i2s_format

    Converts a wave file into a series of 32-bit dwords
    that can be read by the i2s device

    Args:
      wave_filename: path of the wave file to decode

    Returns:
      An array of bytes suitable to be processed by Olympus

    Raises:
     ValueError: Unsupported number of channels 
     WaveError: File not found

    """
    wf = None
    try: 
      wf = wave.open(wave_filename, 'rb')
    except wave.Error as err:
      print str(err)
      sys.exit(1)

    if debug:
      print "Number of channels: %d" % wf.getnchannels()
      print "Sample Width: %d" % wf.getsampwidth()
      print "getframerate: %d" % wf.getframerate()
      print "number of frames: %d" % wf.getnframes()
      print "type of compression: %s" % wf.getcomptype()

    raw_data = wf.readframes(wf.getnframes())
    total_samples = wf.getnframes() * wf.getnchannels()
    sample_width = wf.getsampwidth()

    wf.close()

    #thanks SaphireSun for this peice of code
    #http://stackoverflow.com/questions/2226853/interpreting-wav-data

    if sample_width == 1: 
      fmt = "%iB" % total_samples # read unsigned chars
    elif sample_width == 2:
      fmt = "%ih" % total_samples # read signed 2 byte shorts
    else:
      raise ValueError("Only supports 8 and 16 bit audio formats.")

    integer_data = struct.unpack(fmt, raw_data)
    del raw_data

    byte_array = Array('B')
 
    if sample_width == 1:
      for i in integer_data:
        #set the bit for left or right channel
        #change the value to a 24-bit audio sample
        value = (integer_data[i] & 0xFF) << 16
 
        byte_array.append((value >> 24) & 0xFF)
        byte_array.append((value >> 16) & 0xFF)
        byte_array.append((value >> 8) & 0xFF)
        byte_array.append(value & 0xFF)
 
 
    elif sample_width == 2:
      lr = False
      for i in range (0, len(integer_data)):
        #set the bit for left or right channel
        value = 0x00000000
        if lr:
          value = 0x80000000
 
        #change the value to a 24-bit audio sample
        value = value | ((integer_data[i] & 0xFFFF) << 8)
 
        byte_array.append((value >> 24) & 0xFF)
        byte_array.append((value >> 16) & 0xFF)
        byte_array.append((value >> 8) & 0xFF)
        byte_array.append(value & 0xFF)
 
        lr = not lr

    #Uncommenting out the next two lines will print LOTS of data
    #for i in range (0, (len(byte_array) / 4)):
    #  print "0x%02X%02X%02X%02X" % (byte_array[(i * 4)], byte_array[(i * 4) + 1], byte_array[(i * 4) + 2], byte_array[(i * 4) + 3])
    return byte_array

  def play_wave_file(self, wave_file):
    """play_wave_file

    plays the given audio wave file

    Args:
      wave_file: the wave file to play

    Returns:
      A beautiful song

    Raises:
      ValueError: Unsupported number of channels 
      WaveError: File not found
    """

    print "Converting Audio to I2S format..."
    byte_array = self.convert_wave_to_i2s(wave_file, debug=True)
    print "Startng music..."
    self.i2s.write_all_audio_data(byte_array)
    print "Fin"

     

def usage():
  """prints out a helpful message to the user"""
  print ""
  print "usage: i2s_player.py [options] <wave filename>"
  print ""



if __name__ == "__main__":
  print "starting I2S player"
  argv = sys.argv[1:]

  oly = dionysus.Dionysus()
  oly.ping()
  oly.read_drt()

  i2s_device = 0

  num_devices = oly.get_number_of_devices()

  for dev_index in range (0, num_devices):
    device_id = oly.get_device_id(dev_index)
    dev_offset = oly.get_device_address(dev_index)

    if device_id == 0x0B:
      i2s_index = dev_offset
    
  if i2s_index == 0:
    print "Couldn't find I2S device"
    sys.exit(1)

  print "Found I2S device at index: %d" % i2s_index

  if (len(argv) == 0):
    usage()
    sys.exit(1)
  else:
    try:
      opts, args = getopt.getopt(argv, "hvdco:", ["help", "verbose", "debug", "compress", "outfile"])
    except getopt.GetoptError, err:
      print (err)
      usage()
      sys.exit(2)

    for opt, arg in opts:
      if opt in ("-h", "--help"):
        usage()
        sys.exit()

  if len(args) == 0:
    print "No input file to process"
    usage()
    sys.exit(1)

  i2s_player = I2S_Player(oly, i2s_index)
  for filename in args:
    print "Processing: %s" % filename
    i2s_player.play_wave_file(filename)

