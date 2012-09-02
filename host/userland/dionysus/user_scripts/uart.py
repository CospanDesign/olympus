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

""" UART

Facilitates communication with the UART core independent of communication
medium

For more details see:

http://wiki.cospandesign.com/index.php?title=Wb_uart

TODO: Implement soft flowcontrol
"""
import time
from array import array as Array

import olympus

#Register Constants
CONTROL             = 0
STATUS              = 1
PRESCALER           = 2
CLOCK_DIVIDER       = 3
WRITE_AVAILABLE     = 4
WRITE_DATA          = 5
READ_COUNT          = 6
READ_DATA           = 7

#Control Bit values
CONTROL_RESET       = 1 << 0
CONTROL_RTS_CTS_FC  = 1 << 1
CONTROL_DTS_DSR_FC  = 1 << 2
CONTROL_INT_READ    = 1 << 3
CONTROL_INT_WRITE   = 1 << 4

#Status Bit values
STATUS_OVFL_TX      = 1 << 0
STATUS_OVFL_RX      = 1 << 1
STATUS_UFL_RX       = 1 << 2
STATUS_INT_READ     = 1 << 3
STATUS_INT_WRITE    = 1 << 4

class UART:
  """UART
  
    communication with a UART core
  """

  def __init__(self, olympus, dev_id = None, debug=False):
    self.dev_id = dev_id
    self.o = olympus
    self.debug = debug
    self.status = 0
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

  def get_status(self):
    """get_status

    get the status of the UART

    *** NOTE: 
    *** because the status is reset by the core
    *** the status should only be read once
    *** Read the status with get_status
    *** then perform the tests on the status

    Args:
      Nothing

    Return:
      32-bit status value

    Raises:
      OlympusCommError: Error in communication
    """
    status_array = self.o.read(self.dev_id, STATUS, 1) 

    self.status = status_array[0] << 24 | status_array[1] << 16 | status_array[2] << 8 | status_array[3]
    return self.status


  def is_read_overflow(self):
    """is_read_overflow

    if read overfow

    *** NOTE: 
    *** because the status is reset by the core
    *** the status should only be read once
    *** Read the status with get_status
    *** then perform the tests on the status

    Args:
      Nothing

    Return:
      True: empty
      False: not empty

    Raises:
      OlympusCommError
    """
    #status = self.get_status()
    if ((self.status & STATUS_OVFL_RX) > 0):
      return True
    return False

  def is_write_overflow(self):
    """is_write_overflow

    if write is buffer overflowed

    *** NOTE: 
    *** because the status is reset by the core
    *** the status should only be read once
    *** Read the status with get_status
    *** then perform the tests on the status

    Args:
      Nothing

    Return:
      True: Overflow
      False: No Overflow

    Raises:
      OlympusCommError
    """
    #status = self.get_status()
    if ((self.status & STATUS_OVFL_TX) > 0):
      return True
    return False

  def is_read_underflow(self):
    """is_read_underflow

    Read too many bytes from the read

    *** NOTE: 
    *** because the status is reset by the core
    *** the status should only be read once
    *** Read the status with get_status
    *** then perform the tests on the status

    Args:
      Nothing

    Return:
      True: read underflow
      False: not read underflow

    Raises:
      OlympusCommError
    """
    #status = self.get_status()
    if ((self.status & STATUS_UFL_RX) > 0):
      return True
    return False

  def is_read_interrupt(self):
    """is_read_interrupt

    test if a read interrupt has occured

    *** NOTE: 
    *** because the status is reset by the core
    *** the status should only be read once
    *** Read the status with get_status
    *** then perform the tests on the status

    Args:
      Nothing

    Return:
      True: read interrupt
      False: read interrupt did not occure

    Raises:
      OlympusCommError

    """
    #status = self.get_status()
    if ((self.status & STATUS_INT_READ) > 0):
      return True
    return False

  def is_write_interrupt(self):
    """is_write_interrupt

    test if a write interrupt has occured

    *** NOTE: 
    *** because the status is reset by the core
    *** the status should only be read once
    *** Read the status with get_status
    *** then perform the tests on the status

    Args:
      Nothing

    Return:
      True: write interrupt
      False: not write interrupt

    Raises:
      OlympusCommError
    """
    #status = self.get_status()
    if ((self.status & STATUS_INT_WRITE) > 0):
      return True
    return False

  def write_string(self, string = ""):
    """write_string
    
    Writes a string of data over the UART

    Args:
      string: String to send

    Return:
      Nothing

    Raises:
      OlympusCommError
    """
    if self.debug:
      print "Writing a string"

    data = Array('B')
    data.fromstring(string)
    self.write_raw(data)

  def write_raw(self, data = Array('B')):
    """write_raw

    formats the data to write to the UART device

    the format of the data can be found on

    http://wiki.cospandesign.com/index.php?title=Wb_uart#Write_Data

    Args:
      data: data (in raw byte array) to send down to the UART

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "Writing to the UART device"


    length = len(data)

    data_array = Array('B')
    data_array.extend([((length >> 8) & 0xFF), (((length) & 0xFF))])
    data_array.extend(data)

    print "sending: %s" % str(data_array)
    print "Length: %d" % length

    pad = (len(data_array) % 4)
    for i in range (0, pad):
      data_array.extend([0])

    self.o.write(self.dev_id, WRITE_DATA, data_array)

  def read_string(self, count = 1):
    """read_string
    
    Read a string of characters

    Args:
      count: the number of characters and returns a string
              if -1 read all characters

    Returns:
      string

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "read_string"

    data = Array('B')
    if count == -1:
      data = self.read_all_data()
    else:
      data = self.read_raw(count)
    
    string = data.tostring()
    return string

  def read_raw(self, count = 1):
    """read_raw

    reads the number of bytes specified by count from the UART and
    extracts/returns only the raw bytes to the user

    Args:
      count: the number of bytes to read from the UART core, if
        left blank this will read just one byte

    Returns:
      An array of raw bytes read from the core

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "Reading %d bytes" % count

    count_array = Array('B', [0x00, 0x00, 0x00, 0x00])
    count_array[0]  = (count >> 24) & 0xFF
    count_array[1]  = (count >> 16) & 0xFF
    count_array[2]  = (count >> 8)  & 0xFF
    count_array[3]  = (count) & 0xFF
    self.o.write(self.dev_id, READ_COUNT, count_array)

    if count <= 2:
      count = 1
    else:
      #count = ((count - 2) / 4) + 1
      count = (count / 4) + 1

    print "Output byte count:\n" + str(count)

    data_array = self.o.read(self.dev_id, READ_DATA, count)

    return data_array

  def get_read_count(self):
    """get_read_count

    reads the number of bytes available in the read FIFO

    Args:
      Nothing

    Returns:
      Number of bytes available in the read FIFO

    Raises:
      OlympusCommError
    """
    if self.debug:
      print "getting the bytes to read"

    in_data = self.o.read(self.dev_id, READ_COUNT, 1)
    print "in_data: " + str(in_data)
    return in_data[0] << 24 | in_data[1] << 16 | in_data[2] << 8 | in_data[3]

  def read_all_data(self):
    """read_all_data
    
    reads all the data in the UART read FIFO

    Uses 'get_read_count' to find the number of bytes available
    then read those number of bytes and return them to the user

    Args:
      Nothing

    Returns:
      An array of raw bytes read from the core

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "read all the data in the UART input FIFO"

    count = self.get_read_count()
    return self.read_raw(count)

  def get_write_available(self):
    """get_write_available
    
    returns the number of bytes that can be written into the write buffer

    Args:
      Nothing

    Returns:
      Number of bytes that can be written into the write buffer

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "getting available space in the write buffer"

    in_data = self.o.read(self.dev_id, WRITE_AVAILABLE, 1)
    print "write available: " + str(in_data)
    return in_data[0] << 24 | in_data[1] << 16 | in_data[2] << 8 | in_data[3]

  def get_baudrate(self):
    """get_baudrate

    returns the baudrate of the UART
    
    This function performs the calculations required to extract the baudrate
    from the value within the UART core.

    For details on the calculations see:
    
    http://wiki.cospandesign.com/index.php?title=Wb_uart#Prescaler

    Args:
      Nothing

    Return:
      The baudrtate: e.g.: 57600

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "getting baurdrate"

    prescaler_array = self.o.read(self.dev_id, PRESCALER, 1)
    prescaler = prescaler_array[0] << 24 | prescaler_array[1] << 16 | prescaler_array[2] << 8 | prescaler_array[3]
    print "prescaler: %d" % prescaler
    clock_divide_array = self.o.read(self.dev_id, CLOCK_DIVIDER, 1)
    clock_divide = clock_divide_array[0] << 24 | clock_divide_array[1] << 16 | clock_divide_array[2] << 8 | clock_divide_array[3]
    print "clock divide: %d" % clock_divide
    
    if prescaler > 0:
      return prescaler / clock_divide
    return -1


  def set_baudrate(self, baudrate=57600):
    """set_baudrate
      
    sets the baudrate of the UART core
    
    This function performs the required calculations to generate the correct
    clock value used by the low level core.

    For details on the calculations see:

    http://wiki.cospandesign.com/index.php?title=Wb_uart#Clock_Divider

    Args:
      baudrate: e.g.: 57600

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "setting baudrate"

    prescaler_array = self.o.read(self.dev_id, PRESCALER, 1)
    prescaler = prescaler_array[0] << 24 | prescaler_array[1] << 16 | prescaler_array[2] << 8 | prescaler_array[3]

    clock_divide = prescaler / baudrate

    clock_divide_array = Array('B', [0x00, 0x00, 0x00, 0x00])

    clock_divide_array[0] = (clock_divide >> 24) & 0xFF
    clock_divide_array[1] = (clock_divide >> 16) & 0xFF
    clock_divide_array[2] = (clock_divide >> 8) & 0xFF
    clock_divide_array[3] = (clock_divide) & 0xFF

    self.o.write(self.dev_id, CLOCK_DIVIDER, clock_divide_array)

  def enable_hard_flowcontrol(self):
    """enable_hard_flowcontrol

    enables the use of CTS/RTS hardware flow control

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "setting cts/rts flowcontrol"
    control = self.get_control()
    control = control | CONTROL_RTS_CTS_FC
    self.set_control(control)



  def enable_soft_flowcontrol(self):
    """enable_soft_flowcontrol
    
    enables the use of XON XOFF software flow control

    ***NOTE THIS FUNCTION IS NOT IMPLEMENTED IN THE CORE YET***

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    Exception("Soft flow control not implemented yet!")

  def disable_flowcontrol(self):
    """disable_flowcontrol

    disable flow control (this is the default setting)

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    if self.debug:
      print "Disable flow control"
    control = self.get_control()
    control = control & ~(CONTROL_RTS_CTS_FC | CONTROL_DTR_DSR_FC)
    self.set_control(control)


  def enable_read_interrupt(self):
    """enable_read_interrupt

    enable the read interrupt for the UART
    """
    if self.debug:
      print "Enable the read interrupt"

    control = self.get_control()
    control = control | CONTROL_INT_READ
    self.set_control(control)



  def disable_read_interrupt(self):
    """disable_read_interrupt

    disable the read interrupt for the UART
    """
    if self.debug:
      print "Disable the read interrupt"

    control = self.get_control()
    control = control & ~CONTROL_INT_READ
    self.set_control(control)


  def enable_write_interrupt(self):
    """enable_write_interrupt

    Enable the write interrupt
    """
    if self.debug:
      print "Enable the write interrupt"

    control = self.get_control()
    control = control | CONTROL_INT_WRITE
    self.set_control(control)

  def disable_write_interrupt(self):
    """disable_write_interrupt

    Disable the write interrupt
    """
    if self.debug:
      print "Disable the write interrupt"

    control = self.get_control()
    control = control & ~CONTROL_INT_WRITE
    self.set_control(control)


  def disable_interrupts(self):
    """disable_interrupts

    Disable all interrupts
    """
    if self.debug:
      print "Disable interrupts"

    control = self.get_control()
    control = control & ~(CONTROL_INT_WRITE | CONTROL_INT_READ)
    self.set_control(control)


  def unit_test(self):
    """unit_test

    Run the unit test of the UART
    """
 
    print "Testing UART config"
    baudrate = self.get_baudrate()
    print "Initial baudrate = %d" % baudrate
 
    print "Setting baudrate to 115200"
    self.set_baudrate(115200)
 
    print "Testing if baudrate is correct"
    if self.get_baudrate() > (115200 - (115200 * .01)) and self.get_baudrate() < (115200 + (115200 * .01)) :
      print "Baudrate is within 1% of target"
    else:
      print "Baudrate is not correct!"
 
    print "Changing baurdrate to initial version"
    self.set_baudrate(baudrate)
 
    print "\tXXXX: Cannot test hardware flow control!"
 
    print "Writing a string"
    self.write_string("COSPAN DESIGN ROXORS TEH BIG ONE!!1!\n")

    time.sleep(1)

    print "Read: %s: " % self.read_string(-1)

    
    print "disable all interrupts"
    self.disable_interrupts()
    print "Testing receive interrupt"
    self.enable_read_interrupt()
 
    print "Waiting 10 second for receive interrupts"
    if self.o.wait_for_interrupts(1) > 0:
      if self.o.is_interrupt_for_slave(self.dev_id):
        print "Found a read interrupt"

      print "Read: %s" % self.read_string(-1)
 
    self.disable_read_interrupt()
 
    print "Testing write interrupt"
    self.enable_write_interrupt()
    print "Waiting 1 second for write interrupts"
    if self.o.wait_for_interrupts(1) > 0:
      if self.o.is_interrupt_for_slave(self.dev_id):
        print "Found a write interrupt!"
 
    self.disable_write_interrupt()
 
    print "Testing write"

    print "Writing the maximum amount of data possible"
    write_max = self.get_write_available() - 2
    print "Max: %d" % write_max
    data_out = Array('B')
    num = 0
    try:
      for i in range (0, write_max):
        num = (i) % 255
        if (i / 256) % 2 == 1:
          data_out.append( 255 - (num))
        else:
          data_out.append(num)


    except OverflowError as err:
      print "Overflow Error: %d >= 256" % num
      sys.exit(1)
    self.write_raw(data_out)

    print "Testing read: Type something"


    time.sleep(3)
    
    fail = False
    fail_count = 0
    data = self.read_all_data()

    if len(data_out) != len(data):
      print "data_in length not equal to data_out length:"
      print "\totugoing: %d incomming: %d" % (len(data_out), len(data))
      fail = True
 
    else:
      for i in range (0, len(data_out)):
        if data[i] != data_out[i]:
          fail = True
          print "Mismatch at %d: READ DATA %d != WRITE DATA %d" % (i, data[i], data_out[i])
          fail_count += 1


    if len(data) > 0:
      print "Read some data from the UART"
      print "data (raw): %s" % str(data)
      print "data (string): %s" % str(data.tostring())


    if not fail:
      print "Memory test passed!"
    elif (fail_count == 0):
      print "Data length of data_in and data_out do not match"
    else:
      print "Failed: %d mismatches" % fail_count


    self.write_raw(data_out)
    print "look for the status conditions"
    print "Status: " + hex(self.get_status())
    
    if self.is_read_overflow():
      print "Read overflow"


      

