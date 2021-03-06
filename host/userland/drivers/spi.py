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

""" SPI

Facilitates communication with the SPI core independent of communication
medium

For more details see:

http://wiki.cospandesign.com/index.php?title=Wb_spi

"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

import time

from array import array as Array

from userland import olympus

#Register Constants
CONTROL             = 0
CLOCK_RATE          = 1
CLOCK_DIVIDER       = 2
SLAVE_SELECT        = 3
READ_DATA0          = 4
READ_DATA1          = 5
READ_DATA2          = 6
READ_DATA3          = 7
WRITE_DATA0         = 8
WRITE_DATA1         = 9
WRITE_DATA2         = 10
WRITE_DATA3         = 11

#Control/Status bit values
CONTROL_CHARACTER_LENGTH  = 1 << 0
CONTROL_GO_BUSY           = 1 << 8
CONTROL_RX_NEGATIVE       = 1 << 9
CONTROL_TX_NEGATIVE       = 1 << 10
CONTROL_LSB_ENABLE        = 1 << 11
CONTROL_INTERRUPT_ENABLE  = 1 << 12
CONTROL_AUTO_SLAVE_SEL    = 1 << 13

class SPIError(Exception):
  """SPIError
    
    Errors associated with SPI
      SPI bus busy
      Incorrect settings
  """
  def __init__(self, value):
    self.value = value
  def __str__ (self):
    return repr(self.value)


class SPI:
  """SPI
    
    communication with SPI core
  """

  def __init__(self, olympus, dev_id=None, debug=False):
    self.dev_id = dev_id
    self.o = olympus
    self.debug = debug
    print "device id: %d" % dev_id

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
    control_array = self.o.read(self.dev_id, CONTROL, 1) 
    control = control_array[0] << 24 | control_array[1] << 16 | control_array[2] << 8 | control_array[3]

    return control

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
    control_array = Array('B', [0x00, 0x00, 0x00, 0x00])
    control_array[0]  = (control >> 24) & 0xFF
    control_array[1]  = (control >> 16) & 0xFF
    control_array[2]  = (control >> 8) & 0xFF
    control_array[3]  = (control) & 0xFF
    self.o.write(self.dev_id, CONTROL, control_array)



  def get_character_length(self):
    """get_character_length
      
    gets the length of a character transaction

    Args:
      Nothing

    Returns:
      32-bit value of the length of the character:
        0x001 = 1
        0x002 = 2
        ...
        0x07F = 127
        0x080 = 128

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "get character length"

    control = self.get_control()
    char_len = control & 0x07F
    if char_len == 0x00:
      char_len = 0x0080

    return char_len

  def set_character_length(self, character_length):
    """set_character_length
      
    sets the length of a character transaction

    Args:
      Length of a charater transaction
        0x001 = 1
        0x002 = 2
        ...
        0x07F = 127
        0x080 = 128

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "set character length to %d" % character_length
    
    if character_length >= 0x080:
      character_length = 0x00
   

    control = self.get_control()

    control = control & (~0x007F)
    control = control | character_length
    self.set_control(control)

  def set_tx_polarity(self, positive):
    """set_tx_polarity

    sets what clock edge the TX will shift data out

    Args:
      positive: 
          True = positive edge
          False = negative edge

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if positive:
      control = control & ~(CONTROL_TX_NEGATIVE)
    else:
      control = control | CONTROL_TX_NEGATIVE

    self.set_control(control)

  def is_tx_polarity_positive(self):
    """is_tx_polarity_positive

    returns True if the TX polarity is positive

    Args:
      Nothing

    Return:
      True: Positive Tx Polarity
      False: Negative TX polarity

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if (control & CONTROL_TX_NEGATIVE) > 0:
      return False
    return True

  def set_rx_polarity(self, positive):
    """set_rx_polarity

    sets what clock edge the RX will shift data in

    Args:
      positive: 
          True = positive edge
          False = negative edge

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if positive:
      control = control & ~(CONTROL_RX_NEGATIVE)
    else:
      control = control | CONTROL_RX_NEGATIVE

    self.set_control(control)

  def is_rx_polarity_positive(self):
    """is_rx_polarity_positive

    returns True if the RX polarity is positive

    Args:
      Nothing

    Return:
      True: Positive Tx Polarity
      False: Negative RX polarity

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if (control & CONTROL_RX_NEGATIVE) > 0:
      return False
    return True



  def start_transaction(self):
    """start_transaction
      
    starts a spi read/write transaction

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
      SPIError: SPI core is not ready
    """
    if self.debug:
      print "start a transaction"

    control = self.get_control()
    if (control & CONTROL_GO_BUSY) > 0:
      raise SPIError("SPI Not Ready") 

    control = control | CONTROL_GO_BUSY 
    self.set_control(control)

  def is_busy(self):
    """is_busy
      
    returns true if the core is busy with a transaction

    Args:
      Nothing

    Returns:
      True: Busy
      False: Ready

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "is busy"

    control = self.get_control()
    #    print "\t\tcontrol: %X" % control
    if (control & CONTROL_GO_BUSY) > 0:
      return True
    return False

  def enable_interrupt(self):
    """enable_interrupt
      
    enables the core to raise interrupts when a transaction is complete

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "Enable interrupt"

    control = self.get_control()
    if (control & CONTROL_GO_BUSY) > 0:
      raise SPIError("SPI Not Ready") 

    control = control | CONTROL_INTERRUPT_ENABLE
    self.set_control(control)


  def is_interrupt_enabled(self):
    """is_interrupt_enbled

    returns True if the interrupt is enabled

    Args:
      Nothing

    Returns:
      True: if interrupt is enabled
      False: interrupt is not enabled

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "interrupt enabled"

    control = self.get_control()
    if (control & CONTROL_INTERRUPT_ENABLE) > 0:
      return True
    
    return False



  def disable_interrupt(self):
    """disable_interrupt
      
    disable the SPI interrupt

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """

    if self.debug:
      print "Disable interrupt"

    control = self.get_control()
    if (control & CONTROL_GO_BUSY) > 0:
      raise SPIError("SPI Not Ready") 

    control = control & ~(CONTROL_INTERRUPT_ENABLE)
    self.set_control(control)

  def is_lsb_enabled(self):
    """is_lsb

    is the bit order reveresed
      (least significant bit first)

    Args:
      Nothing

    Return:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """

    control = self.get_control()
    if control & CONTROL_LSB_ENABLE: 
      return True

    return False


  def set_lsb_enable(self, enable):
    """set_lsb_enable

    set the lsb bit
      (eanble least significant bit first

    Args:
      Nothing

    Return:
      Nothing

    Raises:
      OlympusCommError
    """

    control = self.get_control()
    if enable:
      control = control | CONTROL_LSB_ENABLE

    else:
      control = control & ~(CONTROL_LSB_ENABLE)

    self.set_control(control)

  def get_clock_rate(self):
    """get_clock_rate
      
    gets the clock rate of the design (this is used in setting the clock divider

    Args:
      Nothing

    Returns:
      32-bit value indicating the clock_rate of the system
        Example: 100000000 = 100MHz clock

    Raises:
      OlympusCommError: Error in communication
    """

    if self.debug:
      print "get clock rate"

    clock_rate_array = self.o.read(self.dev_id, CLOCK_RATE, 1)
    clock_rate = clock_rate_array[0] << 24 | clock_rate_array[1] << 16 | clock_rate_array[2] << 8 | clock_rate_array[0]
    return clock_rate

  def get_clock_divider(self):
    """get_clock_divider
      
    gets the clock rate of the divider

    Args:
      Nothing

    Returns:
      32-bit clock divider value

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "get clock divider"

    clock_divider_array = self.o.read(self.dev_id, CLOCK_DIVIDER, 1)
    #print "In clock divider Array: %s" % str(clock_divider_array)
    clock_divider = clock_divider_array[0] << 24 | clock_divider_array[1] << 16 | clock_divider_array[2] << 8 | clock_divider_array[3]
    #print "In clock divider: %d" % clock_divider
    return clock_divider



  def set_clock_divider(self, clock_divider):
    """set_clock_divider
      
    set the clock divider

    Args:
      clock_divider: 32-bit value to write into the register

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "set clock divider"

    clock_divider_array = Array('B', [0x00, 0x00, 0x00, 0x00])
    clock_divider_array[0] = (clock_divider >> 24) & 0xFF
    clock_divider_array[1] = (clock_divider >> 16) & 0xFF
    clock_divider_array[2] = (clock_divider >> 8) & 0xFF
    clock_divider_array[3] = (clock_divider) & 0xFF
    if self.debug:
      print "Divider out value: %s" % str(clock_divider_array)
    self.o.write(self.dev_id, CLOCK_DIVIDER, clock_divider_array)


  def set_spi_clock_rate(self, spi_clock_rate):
    """set_spi_clock_rate
      
    attempts to set the clock rate to the clock value

    Args:
      clock_rate: 32-bit value to write into the register
        Ex: 1000000: 1MHz

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "set clock divider"

   
    clock_rate = self.get_clock_rate()
    spi_clock_rate = spi_clock_rate * 2
    
    divider = clock_rate/(spi_clock_rate)

    if divider == 0:
      divider = 1
    
    self.set_clock_divider(divider)


  def get_spi_clock_rate(self):
    """get_spi_clock_rate
    
    get the clock rate from the system

    Args:
      Nothing

    Returns:
      Clock Rate

    Raises:
      OlympusCommError: Error in communication

    """
    clock_rate = self.get_clock_rate()
    divider = self.get_clock_divider()
    print "divider: %d" % divider
    
    value = (clock_rate / (divider + 1)) * 2
    return value

  def set_auto_ss_control(self, enable):
    """set_auto_ss_select_mode
    
    allow the core to control slave select

    Args:
      enable: 
        True: enable auto select mode
        False: Manual select mode

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    control =  self.get_control()
    if enable:
      control = control | CONTROL_AUTO_SLAVE_SEL

    else:
      control = control & ~(CONTROL_AUTO_SLAVE_SEL)

    self.set_control(control)

  def is_auto_ss(self):
    """is_auto_ss

    check if auto ss is set

    Args:
      Nothing

    Return:
      True: Auto SS is set
      False: Auto SS is not set

    Raises:
      OlympusCommError
    """
    control = self.get_control()
    if (control & CONTROL_AUTO_SLAVE_SEL) > 0:
      return True
    return False


  def get_slave_select_raw(self):
    """get_slave_select_raw
      
    get the raw slave select value from the register

    Args:
      Nothing

    Returns:
      32-bit slave select register

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "get slave select raw"

    slave_select_array = self.o.read(self.dev_id, SLAVE_SELECT, 1)
    slave_select = slave_select_array[0] << 24 | slave_select_array[1] << 16 | slave_select_array[2] << 8| slave_select_array[3]
    return slave_select

  def set_slave_select_raw(self, slave_select):
    """set_slave_select_raw
      
    sets the slave select register

    Args:
      slave_select: 32-bit value to be written to the slave select register
        Ex: 0x00000001: select slave 0

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "set slave select raw %X" % slave_select

    slave_select_array = Array('B', [0x00, 0x00, 0x00, 0x00])
    slave_select_array[0] = (slave_select >> 24) & 0xFF
    slave_select_array[1] = (slave_select >> 16) & 0xFF
    slave_select_array[2] = (slave_select >> 8) & 0xFF
    slave_select_array[3] = (slave_select) & 0xFF
    self.o.write(self.dev_id, SLAVE_SELECT, slave_select_array)


  def set_spi_slave_select(self, slave_bit, enable):
    """set_spi_slave
      
    enable an individual SPI slave

    Args:
      slave_bit: a bit value of the slave to enable
        Ex: 0x02 : Enable slave 1
      enable: True or False value that enables/disables the selected slave

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "enable spi slave"

    slave_select = self.get_slave_select_raw()
    if enable:
      slave_select = slave_select | (1 << slave_bit)
    else:
      slave_select = slave_select & ~(1 << slave_bit) 
    
    self.set_slave_select_raw(slave_select)



  def is_spi_slave_selected(self, slave_bit):
    """is_spi_slave_selected
      
    reads the slave select of the specified slave bit

    Args:
      slave_bit: a bit value of the slave to check if enabled

    Returns:
      True: Selected
      False: Not Selected

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "is spi slave enabled"
 
    slave_select = self.get_slave_select_raw()
    if (slave_select & (1 << slave_bit)) > 0 :
      return True

    return False


   
  def get_read_data(self, read_length):
    """get_read_data
      
    get the read data from the SPI core, due to the behavior of SPI the user should specify the amount of data to return
    Generally a SPI transaction will consist of writing to a register and then sending out bytes until the read value is
    read in

    Args:
      read_length: length of the data in bytes to return

    Returns:
      An array of bytes of data

    Raises:
      OlympusCommError: Error in communication
    """


    if self.debug:
      print "get read data"

    #first get the length of the character from the slave device
    char_len = (self.get_character_length() / 8)
      #XXX: There can be a local shadow copy here so I don't have to keep
      #XXX: (cont) reading from the control register



    #read all the read data
    read_array0 = self.o.read(self.dev_id, READ_DATA0, 1) 
    read_array1 = self.o.read(self.dev_id, READ_DATA1, 1) 
    read_array2 = self.o.read(self.dev_id, READ_DATA2, 1) 
    read_array3 = self.o.read(self.dev_id, READ_DATA3, 1) 
    if self.debug:
      print "read data:\n\t%s\n\t%s\n\t%s\n\t%s" % (str(read_array0), str(read_array1), str(read_array2), str(read_array3))
    #only read the data that is relavent to
    #Example Character length == 8, then only read the 8 bits and return that value to the caller
    read_data = Array('B')
    read_data.extend(read_array3)
    read_data.extend(read_array2)
    read_data.extend(read_array1)
    read_data.extend(read_array0)

    if self.debug:
      print "Assembled read data: %s" % str(read_data)

    read_data = read_data[len(read_data) - read_length :len(read_data)]
    
    if self.debug:
      print "Assembled read data: %s" % str(read_data)
    return read_data


  def set_write_data(self, write_data):
    """set_write_data
      
    Sets the write data

    Args:
      write_data: Array of bytes

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """


    if self.debug:
      print "set write data"

    #this write data is in the form of an array and should be the correct
    #length that corresponds to the character length
    char_len = (self.get_character_length() / 8)
    if char_len == 0:
      char_len = 1
  
    if self.is_lsb_enabled():
      if self.debug:
        print "LSB Enabled"
      while char_len > write_data:
        write_data.insert(0, 0xFF)

      while (len(write_data) % 4) != 0:
        write_data.insert(0, 0x00)

    else:
      #MSB first
      if self.debug:
        print "MSB Enabled"
        print "Write length = %d, Charlen/8 = %d" % (len(write_data), char_len)
      while char_len > len(write_data) :
        write_data.append(0xFF)

      while (len(write_data) % 4) != 0:
        write_data.insert(0, 0x00)

    if self.debug:  
      print "write data: %s" % str(write_data)

    if len(write_data) == 4:
      self.o.write(self.dev_id, WRITE_DATA0, write_data[0:4])
      if self.debug:
        print "R0: %s" % str(write_data[0:4])
    elif len(write_data) == 8:
      self.o.write(self.dev_id, WRITE_DATA0, write_data[4:8])
      self.o.write(self.dev_id, WRITE_DATA1, write_data[0:4])
      if self.debug:
        print "R0: %s" % str(write_data[4:8])
        print "R1: %s" % str(write_data[0:4])
    elif len(write_data) == 12:
      self.o.write(self.dev_id, WRITE_DATA0, write_data[8:12])
      self.o.write(self.dev_id, WRITE_DATA1, write_data[4:8])
      self.o.write(self.dev_id, WRITE_DATA2, write_data[0:4])
      if self.debug:
        print "R0: %s" % str(write_data[8:12])
        print "R1: %s" % str(write_data[4:8])
        print "R2: %s" % str(write_data[0:4])
    elif len(write_data) == 16:
      self.o.write(self.dev_id, WRITE_DATA0, write_data[12:16])
      self.o.write(self.dev_id, WRITE_DATA0, write_data[8:12])
      self.o.write(self.dev_id, WRITE_DATA1, write_data[4:8])
      self.o.write(self.dev_id, WRITE_DATA2, write_data[0:4])
      if self.debug:
        print "R0: %s" % str(write_data[12:16])
        print "R1: %s" % str(write_data[8:12])
        print "R2: %s" % str(write_data[4:8])
        print "R3: %s" % str(write_data[0:4])
    else:
      raise SPIError("Write data is incorrect length!")

def unit_test(oly, dev_id):
  print "Unit test!"
  spi = SPI(oly, dev_id)
  clock_rate = spi.get_clock_rate()
  print "Clock Rate: %d" % clock_rate
  char_len = spi.get_character_length()
  print "Character Length: %d" % char_len
  print "Setting character length to 16"
  spi.set_character_length(16)
  print "Read: Character Length: %d" % char_len

  print "is busy? ", 
  is_busy = spi.is_busy()
  if is_busy:
    print "Busy!"
  else:
    print "Not busy"


  print "Enable interrupts"
  spi.enable_interrupt()
  print "Is interrupt enabled? ",
  if spi.is_interrupt_enabled():
    print "Interrupt is enabled!"

  else:
    print "Interrupt is not enabled"



  print "Enable interrupts"
  spi.disable_interrupt()
  print "Is interrupt enabled? ",
  if spi.is_interrupt_enabled():
    print "Interrupt is enabled!"

  else:
    print "Interrupt is not enabled"


  print "Test LSB enable "
  print "Setting enabled to true"

  spi.set_lsb_enable(True)
  print "Is LSB enabled? ",
  if spi.is_lsb_enabled():
    print "LSB Enabled"
  else:
    print "LSB is not enabled"

  print "Setting enabled to false"

  spi.set_lsb_enable(False)
  print "Is LSB enabled? ",
  if spi.is_lsb_enabled():
    print "LSB Enabled"
  else:
    print "LSB is not enabled"


  char_len = spi.get_character_length()
  print "Character Length: %d" % char_len


  #clock rate
  print "Setting clock rate to 1MHz"
  spi.set_spi_clock_rate(1000000)

  print "Reading clock rate"
  clock_rate = spi.get_spi_clock_rate()
  print "Clock rate: %d" % clock_rate


  #get/set TX/RX polarity
  print "Setting TX Polarity to positive"
  spi.set_tx_polarity(True)

  if spi.is_tx_polarity_positive():
    print "TX Polarity is positive"
  else:
    print "TX Polarity is negative"

  print "Setting TX Polarity to negative"
  spi.set_tx_polarity(False)

  if spi.is_tx_polarity_positive():
    print "TX Polarity is positive"
  else:
    print "TX Polarity is negative"

  spi.set_tx_polarity(True)

  print "Setting RX Polarity to positive"
  spi.set_rx_polarity(True)

  if spi.is_rx_polarity_positive():
    print "RX Polarity is positive"
  else:
    print "RX Polarity is negative"

  print "Setting RX Polarity to negative"
  spi.set_rx_polarity(False)

  if spi.is_rx_polarity_positive():
    print "RX Polarity is positive"
  else:
    print "RX Polarity is negative"

  spi.set_rx_polarity(True)





  #slave select
  print "Getting slave select raw"
  slave_select = spi.get_slave_select_raw()
  print "Slave select: %d" % slave_select

  print "Setting slave select raw"
  spi.set_slave_select_raw(0x01)

  print "Getting slave select raw"
  slave_select = spi.get_slave_select_raw()
  print "Slave select: %d" % slave_select

  spi.set_slave_select_raw(0x00)


  #set slave select bit
  print "Checking setting/clearing slave bit"

  print "Checking if bit 2 is set"
  if spi.is_spi_slave_selected(2):
    print "bit 2 is set"
  else:
    print "bit 2 is not set"

  print "Setting bit 2"
  spi.set_spi_slave_select(2, True)

  #set auto select mode
  spi.set_auto_ss_control(True)
  if spi.is_auto_ss():
    print "Auto ss successfully set"
  else:
    print "Auto ss not successfully set"


  print "Checking if bit 2 is set"
  if spi.is_spi_slave_selected(2):
    print "bit 2 is set"
  else:
    print "bit 2 is not set"

  print "Setting Write Data"
  write_data = Array('B', [0x0B])
  spi.set_write_data(write_data)

  print "Getting read data:"
  read_data = spi.get_read_data(16)
  print "Read data: %s" % str(read_data)
  

  print "start a transaction"
  spi.start_transaction()
  
  while spi.is_busy():
    print "busy!"


  print "Getting read data:"
  read_data = spi.get_read_data(16)
  print "Read data: %s" % str(read_data)
  

