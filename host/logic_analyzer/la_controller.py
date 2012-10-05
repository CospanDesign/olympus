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
import time
import threading

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
import la_data_parser


class ListenerThread (threading.Thread):

  def __init__ (self, controller):
    threading.Thread.__init__(self)
    self.controller = controller
    self.exit_request = False
    self.running = False
    self.name = "Listener_Thread"
    print "starting listener thread"

  def set_logic_analyzer(self, logic_analyzer):
    self.logic_analyzer = logic_analyzer

  def run(self):
    self.exit_request = False
    self.running = True
    #spin our wheels until we get a true
    while (not self.controller.listener_callback()):
      #check if the user has requested an exit
      if self.exit_request:
        break
    self.running = False

  def is_running(self):
    if self.running:
      return self.isAlive()
    return False

  def request_exit(self):
    if self.is_running():
      print "Exiting %s" % self.name
      self.exit_request = True


class LAController(object):

  def __init__(self, gui):
    #get a handle to the GUI
    self.listener = ListenerThread(self)
    self.gui = gui
    self.trigger = 0x00000000
    self.mask = 0x00000000
    self.edge = 0x00000000
    self.both = 0x00000000
    self.trigger_after = 0x00000000
    self.repeat_count = 0x00000000
    self.la = None
    self.gui_callback = None
    self.data = None
    self.data_len = 0

  def __del__ (self):
    if self.listener is not None:
      if self.listener.is_running():
        self.listener.request_exit()
        print "Waiting for the listener thread to join"
        self.lisetner.join()

  def quit(self):
    """quit

    User has requested a quit, clean up any threads left running

    Args:
      Nothing

    Returns:
      Nothing

    Raises:
      Nothing
    """
    if self.listener.is_running():
      self.listener.request_exit()
      print "Waiting for the listener thread to join"
      self.listener.join()
      self.listener = None



  def set_gui_callback(self, gui_callback):
    """set_gui_callback

    This callback gets called whenever new data is received, concrete class receives new data

    Args:
      gui_callback: the callback function

    Returns:
      Nothing

    Raises:
      Nothing
    """
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

  def set_edge_bit(self, edge_bit, enable):
    #print "Setting edge %d to %s" % (edge_bit, str(enable))
    if enable:
      self.edge = self.edge | (1 << edge_bit)
    else:
      self.edge = self.edge & ~(1 << edge_bit)

  def get_edge_bit(self, edge_bit):
    if (self.edge & (1 << edge_bit)):
      return True

    return False

  def set_both_bit(self, both_bit, enable):
    #print "Setting both %d to %s" % (both_bit, str(enable))
    if enable:
      self.both = self.both | (1 << both_bit)
    else:
      self.both = self.both & ~(1 << both_bit)

  def get_both_bit(self, both_bit):
    if (self.both & (1 << both_bit)):
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

  def kill_thread(self):
    if self.listener.is_running():
      self.listener.request_exit()
      print "Exiting the currently running thread"
      self.listener.join()

  def start_thread(self):
    self.listener = ListenerThread(self)
    self.listener.set_logic_analyzer(self.listener_callback)
    self.listener.start()
    print "Launched listener thread"

  def process_capture_data(self):
    print "Process capture data"
    vcd = la_data_parser.create_vcd_buffer(self.data)
    f = open("output.vcd", 'w')
    f.write(vcd)
    f.close()

#Functions to implement 

  def listener_callback(self):
    """listener_callback
    
    The listener thread will call this function continuously to test if there is any data in the LA
    the function returns false if there is no more new data and true if there is

    the implementing concrete class must call the gui_callback function with the data
    (in the form of 32bit array) as a parameter

    Args:
      Nothing

    Returns:
      False: no new data
      True: new data

    Raises:
      Nothing
    """
    raise AssertionError("listener_callback is not implemented")

  def connect(self):
    raise AssertionError("connect function is not implemented")
        
  def go(self):
    raise AssertionError("go function is not implemented")


