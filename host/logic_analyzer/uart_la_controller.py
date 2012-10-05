#Distributed under the MIT licesnse.
#Copyright (c) 2012 Dave McCoy (dave.mccoy@cospandesign.com)

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

""" Logic Analyzer Controller

Controls all the communication with the Logic Analyzer with Dionysus
"""

import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from userland import olympus
from userland.olympus import OlympusCommError
from userland.dionysus import dionysus
from userland.drivers import logic_analyzer
from userland.drivers.logic_analyzer import LAError
import uart_logic_analyzer
from uart_logic_analyzer import UARTLAError
import la_controller



class UARTLAController(la_controller.LAController):
  def __init_(self, gui):
    super (UARTLAController, self).__init__(gui)
    self.size = 0

  def connect(self):
    print "Connect to the LA over UART!"
    self.la = uart_logic_analyzer.LogicAnalyzer()
    try:
      self.la.ping()
      self.la.set_enable_capture(False)
      self.size = self.la.get_data_length()
      return True

    except UARTLAError as err:
      return False
    
  def listener_callback(self):
    try:
      print "Waiting for %d" % (self.size * 8)
      self.data = self.la.capture_data(self.size, timeout = .5)
      self.data_length = len(self.data)
      if self.data_length == 0:
        return False

      self.gui_callback()
      return True
    except UARTLAError:
      return False

  def go(self):
    print "Capture Data"
    if self.connect == False:
      raise LAError("Logic Analyzer not connected!")

    self.kill_thread()

    self.la.set_enable_capture(False)
    self.la.set_trigger(self.trigger)
    self.la.set_mask(self.mask)
    self.la.set_trigger_after(self.trigger_after)
    self.la.set_trigger_edge(self.edge)
    self.la.set_both_edges(self.both)
    self.la.set_repeat_count(self.repeat_count)
    self.la.set_enable_capture(True)

    self.start_thread()
    return True



