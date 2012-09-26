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

Controls all the communication with the Logic Analyzer
"""

import sys
import os
import threading
import time

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from userland import olympus
from userland.olympus import OlympusCommError
from userland.dionysus import dionysus
from userland.drivers import logic_analyzer
from userland.drivers.logic_analyzer import LAError
import la_data_parser


class ListenerThread (threading.Thread):

  def __init__ (self, callback):
    threading.Thread.__init__(self)
    self.exit_request = False
    self.callback = callback
    self.running = False
    self.name = "Listener_Thread"
    print "starting listener thread"

  def set_logic_analyzer(self, logic_analyzer):
    self.logic_analyzer = logic_analyzer

  def run(self):
    self.exit_request = False
    self.running = True
    while (1):
      #Longest I will wait is 500 mS
      if self.logic_analyzer.wait_for_capture(.5):
        self.callback()
        self.running = False
        break

      #check if the user has requested an exit
      if self.exit_request:
        self.jrunning = False
        break

  def is_running(self):
    if self.running:
      return self.isAlive()
    return False

  def request_exit(self):
    if self.is_running():
      print "Exiting %s" % self.name
      self.exit_request = True





class LAController:

  def __init__(self, gui):
    #get a handle to the GUI
    self.gui = gui
    self.trigger = 0x00000000
    self.mask = 0x00000000
    self.trigger_after = 0x00000000
    self.repeat_count = 0x00000000
    self.la = None
    self.gui_callback = None
    self.listener = ListenerThread(self.interrupt)

  def __del__ (self):
    if self.listener is not None:
      if self.listener.is_running():
        self.listener.request_exit()
        print "Waiting for the listener thread to join"
        self.lisetner.join()

  def set_gui_callback(self, gui_callback):
    self.gui_callback = gui_callback

  def set_trigger_bit(self, trigger_bit, enable):
    #print "Setting trigger %d to %s" % (trigger_bit, str(enable))
    if enable:
      self.trigger = self.trigger | (1 << trigger_bit)
    else:
      self.trigger = self.trigger & (~(1 << trigger_bit))

  def get_trigger_bit(self, trigger_bit):
    if (self.trigger & (1 << trigger_bit)) > 0:
      return True

    return False

  def set_mask_bit(self, mask_bit, enable):
    #print "Setting mask %d to %s" % (mask_bit, str(enable))
    if enable:
      self.mask = self.mask | (1 << mask_bit)
    else:
      self.mask = self.mask & ~(1 << mask_bit)

  def get_mask_bit(self, mask_bit):
    if (self.mask & (1 << mask_bit)) > 0:
      return True

    return False

  def set_trigger_after(self, trigger_after):
    self.trigger_after = trigger_after

  def set_repeat_count(self, repeat_count):
    self.repeat_count = repeat_count

  def get_trigger_after(self):
    return trigger_after

  def get_repeat_count(self):
    return repeat_count

  def interrupt(self):
    self.gui_callback()

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


  def go(self):
    print "Go"
    if self.la is None:
      return False

    if self.listener.is_running():
      self.listener.request_exit()
      print "Exiting the currently running thread"
      self.listener.join()
      
    self.la.enable_capture(False)
    self.la.reset()
    self.la.enable_interrupt(False)

    self.la.set_trigger(self.trigger)
    self.la.set_trigger_mask(self.mask)
    self.la.set_trigger_after(self.trigger_after)
    self.la.set_repeat_count(self.repeat_count)

    self.la.enable_interrupt(True)
    self.la.enable_capture(True)

    self.listener = ListenerThread(self.interrupt)
    self.listener.set_logic_analyzer(self.la)
    self.listener.start()
    print "Launched listener thread"
    return True


  def process_capture_data(self):
    print "Process capture data"
    data_length = self.la.get_data_count()
    data = self.la.get_capture_data() 
    vcd = la_data_parser.create_vcd_buffer(data)
    print "vcd buffer: "
    print vcd
    f = open("output.vcd", 'w')
    f.write(vcd)
    f.close()


    
