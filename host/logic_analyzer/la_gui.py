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
import glib
import argparse

import dionysus_la_controller
import uart_la_controller

NUMBER_OF_SIGNALS = 32


DESCRIPTION = "\n" \
"GUI Interface to the Logic Analyzer core\n" + \
"\n" + \
"Can be used in one of two ways:\n" + \
"\tAn Olympus Peripheral: \t\tAccessed in the same way as other slaves\n" + \
"\tStand alone UART device:\tThis is useful to debug internal signals\n"

EPILOG = "\n" + \
"Examples:\n" + \
"\n" + \
"Attach to an Olympus core\n" + \
"\tla_gui.py\n" + \
"\n" + \
"Attached to the specified UART\n" + \
"\tla_gui.py -u /dev/ttyUSB0"


class LAGUI:


  def __init__ (self, controller_name="dionysus", device="/dev/ttyUSB0"):

    filename = "./gui/logic_analyzer.glade" 

    #enable threading
    gobject.threads_init()

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
    self.tb_main = builder.get_object("toolbar_main")
    self.buf_status = self.tv_status.get_buffer()

    self.buf_status.set_text("Logic Analyzer Started\n")


    #Connect Callbacks
    builder.connect_signals(self)
    self.window.connect("destroy", self.la_gui_quit)
    self.sb_trigger_after.connect("value-changed", self.ta_changed)
    self.sb_repeat_count.connect("value-changed", self.rc_changed)
    self.b_connect.connect("clicked", self.connect_clicked)
    self.b_go.connect("clicked", self.go_clicked)


    self.output_list = []

    #adde the checkboxes


    #instantiate the controller
    color = gtk.gdk.Color(red=0xFFFF, green=0xF000, blue=0xF000)

    if (controller_name == "dionysus"):
      self.lac = dionysus_la_controller.DionysusLAController(self)
    elif (controller_name == "UART"):
      color = gtk.gdk.Color(red=0x00FF, green=0xFFFF, blue=0xFFFF)
      self.lac = uart_la_controller.UARTLAController(self)

    self.lac.set_gui_callback(self.logic_analyzer_interrupt)

    #Set the background color to indicate that this is for the Wishbone LA
    #color = gtk.gdk.color_parse('#84AB3E')
    #self.tb_main.modify_bg(gtk.STATE_NORMAL, color)
    #self.tb_main.show()
    #Show Window
    self.window.modify_bg(gtk.STATE_NORMAL, color)
    self.add_check_boxes()
    self.window.show()

    #gobject.timeout_add(50, self.tick)
    #self.thread_status = None

#  def update_counts(self):
#    trigger_after = self.lac.get_trigger_after()
#    repeat_count = self.lac.get_repeat_count()
#    self.sb_trigger_after.set_text(str(trigger_after))
#    self.sb_repeat_count.set_text(str(repeat_count))

  def la_gui_quit(self, value):
    self.lac.quit()
    gtk.main_quit()

  def tick(self):
    if self.thread_status is not None:
      self.buf_status.insert_at_cursor(self.thread_status + "\n")

    self.thread_status = None
    return True
    
  def logic_analyzer_interrupt(self):
    self.lac.process_capture_data()
    glib.idle_add(self.logic_analyzer_done, "Captured!")
    #self.thread_status  = "Captured"

  def logic_analyzer_done(self, output_status):
    self.buf_status.insert_at_cursor(output_status + "\n")

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

    if name == "edge":
      self.lac.set_edge_bit(index, widget.get_active())

    if name == "both":
      self.lac.set_both_bit(index, widget.get_active())

    #need to update the output with this setting
    self.update_output_bit(index)


  def add_check_boxes(self):
    #go through each of the tables and add a checkboxes for trigger
    self.output_list = []
    for i in range (0, NUMBER_OF_SIGNALS):
      cb =  gtk.CheckButton()
      name = "trigger %d" % i
      cb.connect("toggled", self.checkbox_callback, name)
      self.ctable.attach(cb, 1, 2, i + 1, i + 2, xoptions=gtk.EXPAND, yoptions=gtk.EXPAND)
      cb.show()

    #add the checkboxes for mask
    for i in range (0, NUMBER_OF_SIGNALS):
      cb =  gtk.CheckButton()
      name = "mask %d" % i
      cb.connect("toggled", self.checkbox_callback, name)
      self.ctable.attach(cb, 2, 3, i + 1, i + 2, xoptions=gtk.EXPAND, yoptions=gtk.EXPAND)
      cb.show()

    #add the checkboxes for edges
    for i in range (0, NUMBER_OF_SIGNALS):
      cb =  gtk.CheckButton()
      name = "edge %d" % i
      cb.connect("toggled", self.checkbox_callback, name)
      self.ctable.attach(cb, 3, 4, i + 1, i + 2, xoptions=gtk.EXPAND, yoptions=gtk.EXPAND)
      cb.show()

    #add the checkboxes for both edges
    for i in range (0, NUMBER_OF_SIGNALS):
      cb =  gtk.CheckButton()
      name = "both %d" % i
      cb.connect("toggled", self.checkbox_callback, name)
      self.ctable.attach(cb, 4, 5, i + 1, i + 2, xoptions=gtk.EXPAND, yoptions=gtk.EXPAND)
      cb.show()

    #add the labels for the output
    for i in range (0, NUMBER_OF_SIGNALS):
      out_text = gtk.Label()
      #out_text.set_text("X")
      #out_text.set_max_length(1)
      self.ctable.attach(out_text, 5, 6, i + 1, i + 2, xoptions=gtk.EXPAND, yoptions=gtk.EXPAND)
      self.output_list.append(out_text)
      out_text.show()
      self.update_output_bit(i)

  def update_output_bit(self, index):
    #print "updating output"
    trigger_bit = self.lac.get_trigger_bit(index)
    mask_bit = self.lac.get_mask_bit(index)
    edge_bit = self.lac.get_edge_bit(index)
    both_bit = self.lac.get_both_bit(index)
    #print "trigger: %s" % str(trigger_bit)
    #print "mask: %s" % str(mask_bit)
    if not mask_bit:
      self.output_list[index].set_label("?")
    else:
      if edge_bit:
        if both_bit:
          self.output_list[index].set_label("X")
        else:
          if trigger_bit:
            self.output_list[index].set_label("/")
          else:
            self.output_list[index].set_label("\\")
      else:
        if trigger_bit:
          self.output_list[index].set_label("1")
        else:
          self.output_list[index].set_text("0")





if __name__ == "__main__":
  parser = argparse.ArgumentParser(
  formatter_class=argparse.RawDescriptionHelpFormatter,
    description=DESCRIPTION,
    epilog=EPILOG
    )

  #parser.add_argument("echo")
  parser.add_argument("-u", "--uart", type=str, help="Uses the UART logic analyzer interface specified")
  parser.parse_args()
  args = parser.parse_args()

  la = None
  if args.uart:
    print "uart set"
    la = LAGUI(controller_name = "UART", device = args.uart)


  else:
    print "Olympus Slave"
    la = LAGUI()
 
  gtk.main()
