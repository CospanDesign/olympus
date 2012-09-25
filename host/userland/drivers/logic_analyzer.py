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

""" Logic Analyzer

Facilitates communication with the Logic Analyzer core independent of medium

For more details see:

http://wiki.cospandesign.com/index.php?title=logic_analyzer

"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

import time

from array import array as Array

from userland import olympus

#Register Constants
CONTROL             = 0
STATUS              = 1
TRIGGER             = 2
TRIGGER_MASK        = 3
TRIGGER_AFTER       = 4
REPEAT_COUNT        = 5
DATA_COUNT          = 6

DATA                = 16

#Control Bits
CONTROL_RESET       = 1 << 0
CONTROL_ENABLE_INT  = 1 << 1
CONTROL_ENABLE_LA   = 1 << 2
CONTROL_RESTART_LA  = 1 << 3

#Status Bits
STATUS_FINISHED     = 1 << 0


class LAError (Exception):
  """LAError

  Errors associated with the Logic Analyzer
  """
  def __init__(self, value):
    self.value = value
  def __str__ (self):
    return repr(self.value)

class LogicAnalyzer:
  """LogicAnalyzer

  Logic Analyzer core
  """
  def __init__(self, olympus, dev_id=None, debug=False):
    self.dev_id  = dev_id
    self.o = olympus
    self.debug = debug

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

  def reset(self):
    """reset

    resets the logic analyzer core:
    Note this is different from a normal reset because the logic
    analyzer is designed to analyze internal signals as well
    as external signals and one of the signals that could be
    probed is the reset line, so this function is a local reset

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    control = control | CONTROL_RESET
    self.set_control(control)


  def enable_interrupt(self, enable):
    """enable_interrupts

    enable or disable the interrupt

    Args:
      Nothing

    Returns:
      enable:
        True = Enable interrupt
        False = Disable interrupt

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if enable:
      control = control | CONTROL_ENABLE_INT
    else:
      control = control & ~(CONTROL_ENABLE_INT)
    self.set_control(control)

  def is_interrupt_enabled(self):
    """is_interrupt_enabled

    Returns true if the interrupt is enabled

    Args:
      Nothing

    Returns:
      True: Interrupts is enabled
      False: Interrupt is disabled

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if ((control & CONTROL_ENABLE_INT) > 0):
      return True
    else:
      return False

  def enable_capture(self, enable):
    """enable_capture

    enable a capture

    Args:
      Nothing

    Returns:
      enable:
        True = Enable interrupt
        False = Disable interrupt

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if enable:
      control = control | CONTROL_ENABLE_LA
    else:
      control = control & ~(CONTROL_ENABLE_LA)
    self.set_control(control)

  def is_capture_enabled(self):
    """is_capture_enabled

    returns True if a capture is currently enabled

    Args:
      Nothing

    Returns:
      True: Capture is enabled
      False: Capture is disabled

    Raises:
      OlympusCommError: Error in communication
    """
    control = self.get_control()
    if ((control & CONTROL_ENABLE_LA) > 0):
      return True
    else:
      return False

  def restart_capture(self):
    """restart_capture

    Restarts the logic capture, this will reset any current or
    finished capture, resets the repeat count for the current
    capture

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      OlympusCommError: Error in communication
 
    """
    control = self.get_control()
    control = control | CONTROL_RESET
    self.set_control(control)

  def is_capture_finished(self):
    """is_capture_finished

    returns true if capture is finished

    Args:
      Nothing

    Returns:
      True: Capture is finished
      False: Capture is not finished

    Raises:
      OlympusCommError: Error in communication
    """
    status  = self.get_status()
    if ((status & STATUS_FINISHED) > 0):
      return True
    else:
      return False

  def set_trigger(self, trigger):
    """set_trigger

    trigger

    when combined with the trigger mask this value will set the required
    pattern that must be matched in order to trigger a capture
    
    when a mask bit is 0 then the trigger bit is don't care, when a mask
    bit is 1 then the incomming data capture must match the associated bit

    Args:
      trigger: 32-bit trigger value

    Return:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    self.o.write_register(self.dev_id, TRIGGER, trigger)

  def get_trigger(self):
    """get_trigger

    read the trigger value

    Args:
      Nothing

    Return:
      32-bit trigger register value

    Raises:
      OlympusCommError: Error in communication
    """
    return self.o.read_register(self.dev_id, TRIGGER)

  def set_trigger_mask(self, trigger_mask):
    """set_trigger_mask

    trigger mask:
    
    1 in a bit value indicates that the associated trigger bit should be
    compared to get a valid capture
    0 in a bit value indicates that the associated trigger bit is a 
    "don't care"

    Args:
      trigger_mask: 32-bit value trigger_mask value

    Return:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    self.o.write_register(self.dev_id, TRIGGER_MASK, trigger_mask)

  def get_trigger_mask(self):
    """get_trigger_mask

    read the trigger mask value

    Args:
      Nothing

    Return:
      32-bit trigger mask register value

    Raises:
      OlympusCommError: Error in communication
    """
    return self.o.read_register(self.dev_id, TRIGGER_MASK)

  def set_trigger_after(self, trigger_after):
    """set_trigger_after

    trigger after:

    Sets the number of clock cycles that are captured before a trigger occurs

    Args:
      trigger_after: 32-bit trigger after value

    Return:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    self.o.write_register(self.dev_id, TRIGGER_AFTER, trigger_after)


  def get_trigger_after(self):
    """get_trigger_after

    read the trigger after value

    Args:
      Nothing

    Return:
      32-bit trigger after register value

    Raises:
      OlympusCommError: Error in communication
    """
    return self.o.read_register(self.dev_id, TRIGGER_AFTER)

  def set_repeat_count(self, repeat_count):
    """set_repeat_count

    repeat count:

    the number of matched triggers that must be captured before the
    Logic Analzyer will start capturing data

    Args:
      repeat_count: 32-bit value

    Return:
      Nothing

    Raises:
      OlympusCommError: Error in communication
    """
    self.o.write_register(self.dev_id, REPEAT_COUNT, repeat_count)

  def get_repeat_count(self):
    """get_repeat_count

    read the repeat count value

    Args:
      Nothing

    Return:
      32-bit repeat count register value

    Raises:
      OlympusCommError: Error in communication
    """
    return self.o.read_register(self.dev_id, REPEAT_COUNT)

  def get_data_count (self):
    """get_data_count

    read the size of logic analyzer buffer

    Args:
      Nothing

    Return:
      32-bit size of the logic analyzer buffer

    Raises:
      OlympusCommError: Error in communication
    """
    return self.o.read_register(self.dev_id, DATA_COUNT)

  def get_capture_data(self):
    """get_capture_data

    returns an array of the captured data

    Args:
      Nothing

    Return:
      Array of 32-bit unsigned values

    Raises:
      OlympusCommError: Error in communication
      LAError: Capture was not finished
    """
    if not self.is_capture_finished():
      raise LAError("Capture is not finished")

    #get the number of 32-bits to read
    count = self.get_data_count()
    
    print "Reading %d Vaues" % count

    data_in = self.o.read(self.dev_id, DATA, count)
    #change this to 32-bit value
    data_out = Array('L')
    for i in range(0, len(data_in), 4):
      data_out.append (data_in[i] << 24 | data_in[i + 1] << 16 | data_in[i + 2] << 8 | data_in[i + 3])

    return data_out


def unit_test(oly, dev_id):
  print "unit test!"
  lax = LogicAnalyzer(oly, dev_id)
  print "Resetting"
  lax.reset()

  print "Is Capture Enable:"
  print "Capture Enable %s" % (lax.is_capture_enabled())

  print "Enable LAX"
  lax.enable_capture(True)

  print "Is Capture Enabled:"
  print "Capture Enable %s" % (lax.is_capture_enabled())

  print "Disable LAX"
  lax.enable_capture(False)

  print "Is Capture Enabled:"
  print "Capture Enable %s" % (lax.is_capture_enabled())


  print "Is Interrupt Enabled:"
  print "Interrupt Enabled: %s" % (lax.is_interrupt_enabled())


  print "Enable interrupt"
  lax.enable_interrupt(True)

  print "Is Interrupt Enabled:"
  print "Interrupt Enabled: %s" % (lax.is_interrupt_enabled())

  print "Disable interrupt"
  lax.enable_interrupt(False)

  print "Is Interrupt Enabled:"
  print "Interrupt Enabled: %s" % (lax.is_interrupt_enabled())

  print "Is capture finished:"
  print "Capture Finished %s" % (lax.is_capture_finished())

  print "Size of capture 0x%08X" % lax.get_data_count()

  print "Set up for a capture..."
  print "Enable Interrupts"
  lax.enable_interrupt(True)

  print "set the trigger"
  lax.set_trigger(0x00300)
  print "set the trigger mask to 0 to trigger on anything"
  lax.set_trigger_mask(0x00100)
  print "set the trigger after"
  lax.set_trigger_after(0x000)
  print "set the repeat count"
  lax.set_repeat_count(10)

  print "Enable the capture"
  lax.enable_capture(True)

  

  data_out  = Array('L')
  print "Wait for interrupts, Press a button!"
  if oly.wait_for_interrupts(wait_time = 5):
    if oly.is_interrupt_for_slave(dev_id):
      print "Found an interrupt for LAX!"
      data_out  = lax.get_capture_data()

  if len(data_out) > 0:
    for i in data_out:
      print "0x%08X" % i



