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
import la_controller




class DionysusLAController(la_controller.LAController):

  def __init__(self, gui):
    super(DionysusLAController, self).__init__(gui)

  def connect(self):
    print "Connect"
    self.la = None
    try:
      dyn = dionysus.Dionysus()
      dyn.ping()
      dyn.read_drt()
      num_devices = dyn.get_number_of_devices()
      for dev_index in range (0, num_devices):
        memory_device = dyn.is_memory_device(dev_index)
        dev_offset = dyn.get_device_address(dev_index)
        dev_size = dyn.get_device_size(dev_index)
        device_id = dyn.get_device_id(dev_index)
        if (device_id == 0x0C):
          print "testing Logic Analyzer @ %d" % dev_offset
          self.la = logic_analyzer.LogicAnalyzer(dyn, dev_offset)
          return True
    except:
      print "Found exception"
      return False
    return False

  def listener_callback(self):
    if self.la.is_capture_finished():
      self.data_length = self.la.get_data_count()
      self.data = self.la.get_capture_data()
      self.gui_callback()
      return True

    else: 
      #Longest I will wait is 500 mS
      try:
        if self.logic_analyzer.wait_for_capture(.5):
          self.data_length = self.la.get_data_count()
          self.data = self.la.get_capture_data()
          self.gui_callback()
          return True
      except IndexError as err:
        print "Error in Dionysus read interrupt"
    #no data yet
    return False

  def go(self):
    print "Go"
    if self.la is None:
      return False

    self.kill_thread()
      
    self.la.enable_capture(False)
    self.la.reset()
    self.la.enable_interrupt(False)

    self.la.set_trigger(self.trigger)
    self.la.set_trigger_mask(self.mask)
    self.la.set_trigger_after(self.trigger_after)
    self.la.set_repeat_count(self.repeat_count)
    self.la.set_trigger_edge(self.edge)
    self.la.set_both_edges(self.both)

    self.la.enable_interrupt(True)
    self.la.enable_capture(True)

    self.start_thread()
    return True


   
