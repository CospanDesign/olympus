#! /usr/bin/python

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

""" Logic Analyzer GUI Controller

Manages the GUI
"""


__author__ = "dave.mccoy@cospandesign.com (Dave McCoy)"

import gtk
import gobject
import sys
import os

import la_controller

NUMBER_OF_SIGNALS = 32

class LAGUI:


  def __init__ (self, filename = "./gui/logic_analyzer.glade"):

    #Load the Glade File
    builder = gtk.Builder()
    builder.add_from_file(filename)

    #Connect to specific components
    self.window = builder.get_object("window_main")
    self.ctable = builder.get_object("table_control")
    self.sb_trigger_after = builder.get_object("spinbutton_trigger_after")
    self.sb_repeat_count = builder.get_object("spinbutton_repeat_count")
    self.b_connect = builder.get_object("toolbutton_connect")
    self.b_go = builder.get_object("toolbutton_go")
    self.l_status = builder.get_object("label_status")
    self.tv_status = builder.get_object("textview_status")
    self.buf_status = self.tv_status.get_buffer()

    self.buf_status.set_text("Logic Analyzer Started\n")


    #Connect Callbacks
    builder.connect_signals(self)
    self.window.connect("destroy", gtk.main_quit)
    self.sb_trigger_after.connect("value-changed", self.ta_changed)
    self.sb_repeat_count.connect("value-changed", self.rc_changed)
    self.b_connect.connect("clicked", self.connect_clicked)
    self.b_go.connect("clicked", self.go_clicked)


    self.output_list = []

    #instantiate the controller
    self.lac = la_controller.LAController(self)
    self.lac.set_gui_callback(self.logic_analyzer_interrupt)

    #adde the checkboxes
    self.add_check_boxes()

    #Show Window
    self.window.show()

#  def update_counts(self):
#    trigger_after = self.lac.get_trigger_after()
#    repeat_count = self.lac.get_repeat_count()
#    self.sb_trigger_after.set_text(str(trigger_after))
#    self.sb_repeat_count.set_text(str(repeat_count))

  def logic_analyzer_interrupt(self):
    self.buf_status.insert_at_cursor("Capture!\n")
    self.buf_status.insert_at_cursor("Processing Capture Data\n")
    self.lac.process_capture_data()

  def connect_clicked(self, widget, data=None):
    result = self.lac.connect()
    print "Result: %s" % result
    if result:
      self.l_status.set_text("Found Olympus LAX")
      self.buf_status.insert_at_cursor("Found Olympus LAX\n")
    else:
      self.l_status.set_text("Failed to find Device")
      self.buf_status.insert_at_cursor("Failed to find Device\n")

  def go_clicked(self, widget, data=None):
    result = self.lac.go()
    if result:
      self.l_status.set_text("Sent LA signal control down")
      self.buf_status.insert_at_cursor("Sent LA signal control data\n")
    else:
      self.l_status.set_text("Device not connected")
      self.buf_status.insert_at_cursor("Device not connected\n")

  def ta_changed(self, widget, data=None):
    value = self.sb_trigger_after.get_value_as_int()
    self.lac.set_trigger_after(value)

  def rc_changed(self, widget, data=None):
    value = self.sb_repeat_count.get_value_as_int()
    self.lac.set_repeat_count(value)

  def checkbox_callback(self, widget, data=None):
    #print "%s is %s" % (data, ("OFF", "ON") [widget.get_active()])
    #parse the name
    name = data.partition(" ")[0]
    index = int(data.partition(" ")[2])
    if name == "trigger":
      self.lac.set_trigger_bit(index, widget.get_active())

    if name == "mask":
      self.lac.set_mask_bit(index, widget.get_active())
    #need to update the output with this setting
    self.update_output_bit(index)


  def add_check_boxes(self):
    #go through each of the tables and add a checkboxes for trigger
    self.output_list = []
    for i in range (0, NUMBER_OF_SIGNALS):
      cb =  gtk.CheckButton()
      name = "trigger %d" % i
      cb.connect("toggled", self.checkbox_callback, name)
      self.ctable.attach(cb, 1, 2, i + 1, i + 2, xoptions=gtk.EXPAND, yoptions=gtk.EXPAND | gtk.FILL)
      cb.show()

    #add the checkboxes for mask
    for i in range (0, NUMBER_OF_SIGNALS):
      cb =  gtk.CheckButton()
      name = "mask %d" % i
      cb.connect("toggled", self.checkbox_callback, name)
      self.ctable.attach(cb, 2, 3, i + 1, i + 2, xoptions=gtk.EXPAND, yoptions=gtk.EXPAND | gtk.FILL)
      cb.show()

    #add the checkboxes for mask
    for i in range (0, NUMBER_OF_SIGNALS):
      out_text = gtk.Label()
      #out_text.set_text("X")
      #out_text.set_max_length(1)
      self.ctable.attach(out_text, 3, 4, i + 1, i + 2, xoptions=gtk.EXPAND, yoptions=gtk.EXPAND | gtk.FILL)
      self.output_list.append(out_text)
      out_text.show()
      self.update_output_bit(i)

  def update_output_bit(self, index):
    #print "updating output"
    trigger_bit = self.lac.get_trigger_bit(index)
    mask_bit = self.lac.get_mask_bit(index)
    #print "trigger: %s" % str(trigger_bit)
    #print "mask: %s" % str(mask_bit)
    if not mask_bit:
      self.output_list[index].set_label("X")
    else:
      if trigger_bit:
        self.output_list[index].set_label("1")
      else:
        self.output_list[index].set_text("0")





if __name__ == "__main__":
  la = LAGUI()
  gtk.main()
