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

""" I2S

Facilitates communication with the I2S core independent of communication
medium

For more details see:

http://wiki.cospandesign.com/index.php?title=Wb_i2s

"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

import time

from array import array as Array

from userland import olympus

#Register Constants
CONTROL         = 0
STATUS          = 1
CLOCK_RATE      = 2
CLOCK_DIVISOR   = 3
MEM_0_BASE      = 4
MEM_0_SIZE      = 5
MEM_1_BASE      = 6
MEM_1_SIZE      = 7

#Control bit values
CONTROL_ENABLE            = 1 << 0
CONTROL_INTERRUPT_ENABLE  = 1 << 1

#Status bit values
STATUS_MEM_0_EMPTY        = 1 << 0
STATUS_MEM_1_EMPTY        = 1 << 1


class I2SError(Exception):
  """I2SError
    
    Errors associated with I2S
      I2S Starved
      Incorrect settings
  """
  def __init__(self, value):
    self.value = value
  def __str__ (self):
    return repr(self.value)

class I2S:
  """I2S
    
    communication with I2S core
  """

  def __init__ (self, olympus, dev_id=None, debug=False):
    self.dev_id = dev_id
    self.o = olympus
    self.debug = debug
    self.status = 0
    print "device id: %d" % dev_id

  def set_dev_id(self, dev_id):
    self.dev_id = dev_id

  def get_control(self):
    """get_control

    read the control register

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


  def get_status(self):
    """get_status

    read the status register

    Args:
      Nothing

    Return:
      32-bit status register value

    Raises:
      OlympusCommError: Error in communication
    """
    return self.o.read_register(self.dev_id, STATUS)

  def get_available_memory_blocks(self):
    """get_available_memory_blocks

    reads the status of the I2S core and determine whether the memory
    blocks are available, Returns a value between 0 and 2

    Args;
      Nothing

    Returns:
      0 = No blocks free
      1 = block 0 is free
      2 = block 1 is free
      3 = both block 0 and 1 are free

    Raises
      OlympusCommError: Error in communication
    """
    status = self.get_status()
    return status & (STATUS_MEM_0_EMPTY | STATUS_MEM_1_EMPTY)

  def enable_i2s(self, enable):
    """enable_i2s
    
    Enable the I2C core

    Args:
      enable:
        True
        False

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if enable:
      control = control | CONTROL_ENABLE
    else:
      control = control & (~CONTROL_ENABLE)

    self.set_control(control)

  def is_i2s_enabled(self):
    """is_i2s_enabled

    returns true if i2s is enabled

    Args:
      Nothing

    Returns:
      True: Enabled
      False: Not Enabled

    Raises:
      OlympusCommError: Error in communication
    """
    return ((self.get_control() & CONTROL_ENABLE) > 0)

  def enable_interrupt(self, enable):
    """enable_interrupts

    Enable interrupts upon completion of sending a byte and arbitrattion lost

    Args:
      enable:
        True
        False

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if enable:
      control = control | CONTROL_INTERRUPT_ENABLE
    else:
      control = control & (~CONTROL_INTERRUPT_ENABLE)

    self.set_control(control)

  def is_interrupt_enabled(self):
    """is_i2c_enabled

    returns true if i2c is enabled

    Args:
      Nothing

    Returns:
      True: Enabled
      False: Not Enabled

    Raises:
      OlympusCommError: Error in communication
    """
    return ((self.get_control() & CONTROL_INTERRUPT_ENABLE) > 0)

  def print_command(self,command):
    """print_command

    print out the command in an easily readible format

    Args:
      status: The command to print out

    Returns:
      Nothing

    Raises:
      OlympsCommError: Error in communiction
    """
    print "Command (%X): " % command
    if (command & COMMAND_ENABLE) > 0:
      print "\tENABLE"
    if (command & COMMAND_ENABLE_INTERRUPT) > 0:
      print "\tENABLE INTERRUPT"



  def print_status(self, status):
    """print_status

    print out the status in an easily readible format

    Args:
      status: The status to print out

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """

    print "Status (%X): " % status
    if (status & STATUS_MEM_0_EMPTY) > 0:
      print "\tMEMORY 0 IS EMPTY"
    if (status & STATUS_MEM_1_EMPTY) > 0:
      print "\tMEMORY 1 IS EMPTY"


  def get_memory_base(self, base_index):
    """get_memory_base

    returns the address of the memory base

    Args:
      base_index: 0 or 1 indicating which memory block to get

    Returns:
      32-bit address of the memory base

    Raises:
      OlympusCommError: Error in communication
      I2SError: base is not equal to 0 or 1
    """
    if base_index < 0 or base_index > 1:
      raise I2SError("Illegal base address, only values 0 and 1 are accepted")

    if (base_index == 0):
      return self.o.read_register(self.dev_id, MEM_0_BASE)

    else:
      return self.o.read_register(self.dev_id, MEM_1_BASE)


  def set_memory_base(self, base_index, memory_base):
    """set_memory_base

    sets the memory base address for the base index memory block

    Args:
      base_index: 0 or 1 incidcating which memory block to set
      memory_base: 32-bit address to set the base

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communiction
      I2SError: base is not equal to 0 or 1
    """
    if base_index < 0 or base_index > 1:
      raise I2SError("Illegal base address, only values 0 and 1 are accepted")

    if (base_index == 0):
      self.o.write_register(self.dev_id, MEM_0_BASE, memory_base)
    else:
      self.o.write_register(self.dev_id, MEM_1_BASE, memory_base)


  def set_memory_size(self, base_index, memory_size):
    """set_memory_size

    Sets the size of the memory written at the associated base index
    
    Args:
      base_index: 0 or 1 indicating which memory block to set
      memory_base: 32-bit value indicating the size of the memory written

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
      I2SError: base is not equal to 0 or 1
    """
    if base_index == 0:
      self.o.write_register(self.dev_id, MEM_0_SIZE, memory_size)
    else:
      self.o.write_register(self.dev_id, MEM_1_SIZE, memory_size)

  def get_memory_count(self, base_index):
    """set_memory_size

    gets the number of dwords left to read from memory
    
    Args:
      base_index: 0 or 1 indicating which memory block to set

    Returns:
      32-bit value of the number of dwords left to read

    Raises:
      OlympusCommError: Error in communication
      I2SError: base is not equal to 0 or 1
    """
    if base_index == 0:
      return self.o.read_register(self.dev_id, MEM_0_SIZE)

    return self.o.read_register(self.dev_id, MEM_1_SIZE)


  def get_clock_rate(self):
    """get_clock_rate

    returns the clock rate from the module

    Args:
      Nothing

    Returns:
      32-bit representation of the clock

    Raises:
      OlympusCommError: Error in communication
    """
    return self.o.read_register(self.dev_id, CLOCK_RATE)


  def get_clock_divisor(self):
    """get_clock_divisor

    returns the clock divisor from the module

    Args:
      Nothing

    Returns:
      32-bit representation of the clock divisor

    Raises:
      OlympusCommError: Error in communication
    """
    return self.o.read_register(self.dev_id, CLOCK_DIVISOR)

  def set_custom_sample_rate(self, sample_rate, audio_bits=24, channels=2):
    """set_custom_sample_rate
    
    sets the clock divisor to generate the custom sample rate

    Args:
      sample_rate: desired sample rate of I2S audio data
      channels: 1, or 2 are supported right now

    Return:
      Nothing

    Raises:
      OlympusCommError: Error in communication
      I2SError: channels is not 1 or 2 (default 2)
    """
    if (channels < 1 or channels > 2):
      raise I2SError ("Channels can only be 1 or 2 at this time")

    clock_rate = self.get_clock_rate()
    divisor = clock_rate / ((sample_rate * audio_bits * channels) + 1)
    self.set_clock_divisor(divisor)

  def get_sample_rate(self, audio_bits=24, channels=2):
    """get_sample_rate

    return the sample rate of the i2s player

    Args:
      channels: 1 (mono) or 2 (stereo) (default 2)

    Return:
      Frequency of the sample rate

    Raises:
      OlympusCommError: Error in communication
      I2SError: channels is not 1 or 2 (default 2)
    """
    if (channels < 1 or channels > 2):
      raise I2SError ("Channels can only be 1 or 2 at this time")


    clock_rate = self.get_clock_rate()
    divisor = self.get_clock_divisor()
    sample_rate = clock_rate / ((divisor * audio_bits * channels) + 1)
    return sample_rate
 

  def write_all_audio_data(self, audio_data, block_size=-1):
    """write_audio_data

    writes the raw PCM data to memory, the memory data is in the format of:

    32-bits

    31: left = 0, right = 1 channel
    30 - 24: Reserved
    23 - 0: Audio data

    This will automatically detect where the memory should be written, it will set
    up interrupts and attempt to continuously write down data to the device.

    if the user does not specify the block_size the size will be calculated from
    
    block_size = memory_1_base - memory_0_base

    Args:
      audio_data: Array of bytes corresponding to the audio data in the format
                  described above
      block_size: if specified the size of the blocks to write

    Returns:
      Nothing

    Raises:   
      OlympusCommError: Error in communication
      I2SError: 
        block_size > memory_1_base - memory_0_base
        block_size + memory_1_base > memory_size
    """
    memory_0_base = self.get_memory_base(0)
    memory_1_base = self.get_memory_base(1)
    max_size = memory_1_base - memory_0_base
    if block_size == -1:
      block_size = max_size

    total_memory_size = self.o.get_total_memory_size()

    if memory_1_base + block_size > total_memory_size:
      raise I2SError ("Block size is too large for memory Mem Base: " + \
                      " Mem 1 Base: 0x%08X " % memory_1_base + \
                      " Block Size: 0x%08X " % block_size + \
                      " Total Size: 0x%08X " % total_memory_size)


    #clear the current size in the device
    self.enable_i2s(False)
    self.set_memory_size(0, 0)
    self.set_memory_size(1, 0)

    self.enable_i2s(True)
    self.enable_interrupt(True)
    position = 0
    base_index = 0

    #writing to the screen may take too long...
    prev_percent = 0.0
    percent_complete = 0.0
    total_length = len(audio_data)

    while(len(audio_data[position:]) > 0): 
      size = block_size
      #see if there is enough audio data for the entire block size
      if len(audio_data[position:]) < block_size: 
        size = len(audio_data[position, -1])
 
      #check to see if there is an available memory block
      available_blocks = self.get_available_memory_blocks()
      if (available_blocks == STATUS_MEM_0_EMPTY):
        print "Memory block 0 available"
        #memory block 0 is available
        self.o.write_memory(memory_0_base, audio_data[position: position + size])
        self.set_memory_size(0, size)
        position = position + size

      elif (available_blocks == STATUS_MEM_1_EMPTY): 
        print "Memory block 1 available"
        #memory block 1 is available
        self.o.write_memory(memory_1_base, audio_data[position: position + size])
        self.set_memory_size(1, size)
        position = position + size

      elif (available_blocks == 3):
        print "Both Blocks are available"
        #both blocks are available
        self.o.write_memory(memory_0_base, audio_data[position: position + size])
        self.set_memory_size(0, size)
        position = position + size

        size = block_size
        #see if there is enough audio data for the entire block size
        if len(audio_data[position:]) < block_size: 
          size = len(audio_data[position:])

        if (size > 0):
          #memory block 1 is available
          self.o.write_memory(memory_1_base, audio_data[position: position + size])
          self.set_memory_size(1, size)
          position = position + size

      #precent_complete = ((position * 100.0) / (total_length * 1.0))
      #if (prev_percent != percent_complete):
        #print "position:0x%08X" % position
        #print "total: 0x%08X" % total_length
      print "percent sent to the core: %f" % ((position * 100.0)/(total_length * 1.0) )
        #prev_precent = perent_complete

      #wait for interrupt
      self.o.wait_for_interrupts(wait_time=10)



def unit_test(oly, dev_id): 
  i2s = I2S(oly, dev_id)
  print "Check if the ore is enabled"
  print "enabled: " + str(i2s.is_i2s_enabled())

  print "Enable core"
  i2s.enable_i2s(True)

  print "Check if the ore is enabled"
  print "enabled: " + str(i2s.is_i2s_enabled())

  print "Check if interrupt is enabled"
  print "enabled: " + str(i2s.is_interrupt_enabled())

  print "Enable interrupt"
  i2s.enable_interrupt(True)
  print "Check if interrupt is enabled"
  print "enabled: " + str(i2s.is_interrupt_enabled())

  print "Get sample frequency"
  sample_rate = i2s.get_sample_rate()
  print "\tSample Rate: %d" % sample_rate

  print "Get Memory 0 base"
  print "\t0x%08X" % i2s.get_memory_base(0)

  print "Get Memory 0 Count"
  print "\t0x%08X" % i2s.get_memory_count(0)

  print "Set Memory 0 Size"
  i2s.set_memory_size(0, 1)

  print "Get Memory 0 Count"
  print "\t0x%08X" % i2s.get_memory_count(0)



  print "Get Memory 1 base"
  print "\t0x%08X" % i2s.get_memory_base(1)

  print "Get Memory 1 Count"
  print "\t0x%08X" % i2s.get_memory_count(1)

  print "Set Memory 0 Size"
#  i2s.set_memory_size(1, 1000)

  print "Get Memory 1 Count"
  print "\t0x%08X" % i2s.get_memory_count(1)

  print "Enable core"
  i2s.enable_i2s(True)

  print "Enable interrupt"
  i2s.enable_interrupt(True)
 

