#! /usr/bin/python

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

""" core_analyzer

Analyzes the olympus core in case of a crash

"""
__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

""" Changelog:
  
09/21/2012
  -Initial Commit

"""

import time
import random
import sys
import os
import string
import json
from array import array as Array

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from userland.dionysus.dionysus import Dionysus
from userland.olympus import OlympusCommError
from userland.dionysus.control.dionysus_control import Dionysus_Control

def analyze_crash(pretty_print = True):
  """analyze_crash

  Resets the olympus core and analyzes crash

  NOTE: DO NOT RESET THE OLYMPUS IMAGE MANUALLY OR YOU WILL LOSE THE DUMP
  DATA

  This function will reset the board

  Args:
    pretty_print: if True, prints out the core dump in an easy to read format

  Returns:
    Dictionary of the core data

  Raises:
    OlympusCommError: A failure of communication was detected
  """

  #reset the core
  dc = Dionysus_Control() 
  dc.reset_internal_state_machine()
  time.sleep(.1)

  #now the dump data is ready to be read
  oly = Dionysus()
  core_data = oly.dump_core()
  core_dict = create_core_dump_dict(core_data)
  pretty_print_core_dump(core_dict)
  

def create_core_dump_dict(core_data):
  """create_core_dump_dict

  create an easy to read dictionary from the raw core dump data

  Args:
    core_data: 32-bit array of raw core data

  Returns:
    dictionary of the core data

  Raises:
    Nothing
  """
  #0:   state
  #1:   status
  # bit 0:    mem_bus_selected
  #2:   flags
  # bit 0:    peripheral interupt
  # bit 1:    nack timeout
  #3:   nack count
  #4:   in command
  # top 16 bits: flags
  # bottom 16 bits: user requested command
  #5:   in address
  #6:   internal data count
  #7:   wishbone state
  #8:   wishbone peripheral address
  #9:   wishbone peripheral data in (from slave)
  #10:  wishbone peripheral data out (to slave)
  #11:  wishbone memory address
  #12:  wishbone memory data in (from memory slave)
  #13:  wishbone memory data out (to memory slave)

  print "Length of core read: %d" % len(core_data)

  core_dict = {}
  core_dict["state"]                  = core_data[0]
  core_dict["mem_bus_selected"]       = ((core_data[1] & 0x01) > 0) 
  core_dict["master_ready"]           = ((core_data[1] & 0x02) > 0)
  core_dict["in_ready"]               = ((core_data[1] & 0x04) > 0)
  core_dict["out_en"]                 = ((core_data[1] & 0x08) > 0)
  core_dict["out_ready"]              = ((core_data[1] & 0x10) > 0)
  core_dict["ih_ready"]               = ((core_data[1] & 0x20) > 0)
  core_dict["periph_int"]             = ((core_data[2] & 0x01) > 0)
  core_dict["nack_timeout"]           = core_data[3]
  core_dict["in_command"]             = (core_data[4] & 0x0000FFFF)
  core_dict["in_flags"]               = ((core_data[4] & 0xFFFF0000) >> 16)
  core_dict["in_address"]             = core_data[5]
  core_dict["internal_data_count"]    = core_data[6]
  core_dict["periph_bus"]             = {}
  core_dict["memory_bus"]             = {}
  core_dict["periph_bus"]["cyc"]      = ((core_data[7] & 0x100000) > 0)
  core_dict["periph_bus"]["stb"]      = ((core_data[7] & 0x80000) > 0)
  core_dict["periph_bus"]["we"]       = ((core_data[7] & 0x40000) > 0)
  core_dict["periph_bus"]["ack"]      = ((core_data[7] & 0x20000) > 0)
  core_dict["periph_bus"]["int"]      = ((core_data[7] & 0x10000) > 0)
  core_dict["periph_bus"]["addr"]     = core_data[8] 
  core_dict["periph_bus"]["data_in"]  = core_data[9]
  core_dict["periph_bus"]["data_out"] = core_data[10]
  core_dict["memory_bus"]["cyc"]      = ((core_data[7] & 0x08) > 0)
  core_dict["memory_bus"]["stb"]      = ((core_data[7] & 0x04) > 0)
  core_dict["memory_bus"]["we"]       = ((core_data[7] & 0x02) > 0)
  core_dict["memory_bus"]["ack"]      = ((core_data[7] & 0x01) > 0)
  core_dict["memory_bus"]["addr"]     = core_data[11]
  core_dict["memory_bus"]["data_in"]  = core_data[12]
  core_dict["memory_bus"]["data_out"] = core_data[13]

  #get the state
  state = "Unknown"
  if (core_dict["state"] == 0):
    state = "Idle"
  elif (core_dict["state"] == 1):
    state = "Write"
  elif (core_dict["state"] == 2):
    state = "Read"
  elif (core_dict["state"] == 3):
    state = "Core Dump"
  else:
    state = "Unknown state"
  core_dict["state_string"] = state

  #incomming command
  in_command = "Unknown"
  if (core_dict["in_command"] == 0):
    in_command = "Ping"
  elif (core_dict["in_command"] == 1):
    in_command = "Write"
  elif (core_dict["in_command"] == 2):
    in_command = "Read"
  elif (core_dict["in_command"] == 3):
    in_command = "Comm Reset"
  elif (core_dict["in_command"] == 4):
    in_command = "Master Control"
  elif (core_dict["in_command"] == 15):
    in_command = "Core Dump"
  else:
    in_command = "No Command Sent"

  core_dict["in_command_string"] = in_command
 

  return core_dict


def pretty_print_core_dump(core_dict):
  """pretty_print_core_dump

  display the core dump in an easy to read format

  Args:
    core_dict: dictionary of the core data

  Returns:
    Nothing

  Raises:
    Nothing
  """
  CSI = "\x1B["

  white = '\033[0m'
  gray = '\033[90m'
  red   = '\033[91m'
  green = '\033[92m'
  yellow = '\033[93m'
  blue = '\033[94m'
  purple = '\033[95m'
  cyan = '\033[96m'

  erase = CSI + "2J"
  set_pos_to_top = CSI + "H"
  reset = CSI + "m"

 
  print erase
  print set_pos_to_top

  print purple
  print "Core Dump Analysis"
  print ""
  print "Last Command Sent"
  print ""
  print blue
  print "Incomming Command:\t%s%s%s" % (cyan, core_dict["in_command_string"], blue)
  print "Incomming Flags:\t%s0x%08X%s" % (cyan, core_dict["in_flags"], blue)
  print "Incomming Address:\t%s0x%08X%s" % (cyan, core_dict["in_address"], blue)
  print "Internal Data Count:\t%s0x%08X%s" % (cyan, core_dict["internal_data_count"], blue)
  print ""
  print purple
  print "Master Internal Registers"
  print ""
  print blue
  print "State: %s%s%s" % (red, core_dict["state_string"], blue)
  print "Flags:"
  print ""
  print "\tMaster Ready for Data:\t\t%s%s%s" % (cyan, core_dict["master_ready"], blue)
  print "\tInput Handler has Data:\t\t%s%s%s" % (cyan, core_dict["in_ready"], blue)
  print "\tOutput Handler ready for Data:\t%s%s%s" % (cyan, core_dict["out_ready"], blue)
  print "\tMaster Send new data:\t\t%s%s%s" % (cyan, core_dict["out_en"], blue)
  print "\tPeripheral Interrupt:\t\t%s%s%s" % (cyan, core_dict["periph_int"], blue)
  print "\tNack Timeout Count:\t\t%s%s%s" % (cyan, core_dict["nack_timeout"], blue)
  print ""
  print purple
  print "Wishbone Bus State"
  if (core_dict["mem_bus_selected"]):
    print "%sMEMORY BUS SELECTED%s" % (yellow, blue)
  else:
    print "%sPERIPHERAL BUS SELECTED%s" % (green, blue)
  
  print green
  print "Peripheral Bus:"
  print "\tcyc:\t\t%s%s%s" % (cyan, str(core_dict["periph_bus"]["cyc"]), green)
  print "\tstb:\t\t%s%s%s" % (cyan, str(core_dict["periph_bus"]["stb"]), green)
  print "\twe:\t\t%s%s%s" % (cyan, str(core_dict["periph_bus"]["we"]), green)
  print "\tack:\t\t%s%s%s" % (cyan, str(core_dict["periph_bus"]["ack"]), green)
  print "\tint:\t\t%s%s%s" % (cyan, str(core_dict["periph_bus"]["int"]), green)
  print "\taddr:\t\t%s0x%08X%s" % (cyan, core_dict["periph_bus"]["addr"], green)
  print "\tdata_in:\t%s0x%08X%s" % (cyan, core_dict["periph_bus"]["data_in"], green)
  print "\tdata_out:\t%s0x%08X%s" % (cyan, core_dict["periph_bus"]["data_out"], green)
  print ""

  print yellow
  print "Memory Bus:"
  print "\tcyc:\t\t%s%s%s" % (cyan, str(core_dict["memory_bus"]["cyc"]), yellow)
  print "\tstb:\t\t%s%s%s" % (cyan, str(core_dict["memory_bus"]["stb"]), yellow)
  print "\twe:\t\t%s%s%s" % (cyan, str(core_dict["memory_bus"]["we"]), yellow)
  print "\tack:\t\t%s%s%s" % (cyan, str(core_dict["memory_bus"]["ack"]), yellow)
  print "\taddr:\t\t%s0x%08X%s" % (cyan, core_dict["memory_bus"]["addr"], yellow)
  print "\tdata_in:\t%s0x%08X%s" % (cyan, core_dict["memory_bus"]["data_in"], yellow)
  print "\tdata_out:\t%s0x%08X%s" % (cyan, core_dict["memory_bus"]["data_out"], yellow)
  print ""
  
  print reset


if __name__ == "__main__":
  analyze_crash()
