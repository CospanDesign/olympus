#! /usr/bin/python
import sys
import os
import json
import string

#sys.path.append(os.path.join(os.path.dirname(__file__)))

class DRTError(Exception):
  """DRTError

  Errors associated with Devcie ROM Table:
    invalid JSON file.
  """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)


def get_device_list():
  """get a list of devices"""
  drt_tags = {}
  dev_tags = {}
  dev_list = []
  index = 0
  length = 0
  try: 
    f = open(os.path.join(os.path.dirname(__file__), "drt.json"), "r")
    drt_tags = json.load(f)
  except TypeError as err:
    print "JSON Error: %s" % str(err)
    raise DRTError("DRT Error: %s", str(err)) 

  dev_tags = drt_tags["devices"]

  length = len(dev_tags) 

  for i in range(0, length):
    for key in dev_tags.keys():
      #change the hex number into a integer
      in_str = dev_tags[key]["ID"]
      index = int(dev_tags[key]["ID"][2:], 16)
      if index == i:
        dev_tags[key]["name"] = key
        dev_list.insert(index, dev_tags[key])
  return dev_list


def get_device_index(name):
  """get the index of the device speicified by name"""
  dev_list = get_device_list()
    
  for i in range(0, len(dev_list)):
    if name == dev_list[i]["name"]:
      return i 

  raise DRTError("Name: %s is not a known type of devices" % name) 

def get_device_type(index):
  """Given a index return the name of the Device"""
  dev_list = get_device_list()
  return dev_list[i]["name"]

def get_flag_tags():
  """Returns a listing of the Flags"""
  drt_tags = {}
  flag_tags = {}

  try: 
    f = open(os.path.join(os.path.dirname(__file__), "drt.json"), "r")
    drt_tags = json.load(f)
  except TypeError as err:
    print "JSON Error: %s" % str(err)
    raise DRTError("DRT Error: %s", str(err)) 

  flag_tags = drt_tags["flags"]
  return flag_tags

def get_device_flag_names(flags_string):
  """Reads in a flag string and returns the flags that are set
  in a human readible view"""

  flag_tags = get_flag_tags()
  flags = int(flags_string, 16)
  flag_names = []

  for key in flag_tags.keys():
    test_value = 2 ** flag_tags[key]["bit"]
    if (test_value & flags) > 0:
      flag_names.append("0x%8X: %s" % (test_value, key))
  return flag_names
  

def pretty_print_drt(drt):
  """takes in a DRT string and prints it in a pretty way"""
  drt_lines = drt.splitlines()
  num = int(drt_lines[1], 16)

  #the first line is the version of the DRT and the ID
  white = '\033[0m'
  gray = '\033[90m'
  red   = '\033[91m'
  green = '\033[92m'
  yellow = '\033[93m'
  blue = '\033[94m'
  purple = '\033[95m'
  cyan = '\033[96m'

  test = '\033[97m'

  print red,
  print "DRT:"
  print ""
  print "%s%s:%sVersion: %s ID Word: %s" % (blue, drt_lines[0], green, drt_lines[0][0:4], drt_lines[0][4:8])
  print "%s%s:%sNumber of Devices: %d" % (blue, drt_lines[1], green, int(drt_lines[1], 16))
  print "%s%s:%sString Table Offset (0x0000 == No Table)" % (blue, drt_lines[2], green)
  print "%s%s:%sReserverd for future use" % (blue, drt_lines[3], green)
  print "%s%s:%sReserverd for future use" % (blue, drt_lines[4], green)
  print "%s%s:%sReserverd for future use" % (blue, drt_lines[5], green)
  print "%s%s:%sReserverd for future use" % (blue, drt_lines[6], green)
  print "%s%s:%sReserverd for future use" % (blue, drt_lines[7], green)

  print red,
  print "Devices:"
  for i in range (0, num_of_devices):
    memory_device = False 
    f = int (drt_lines[((i + 1) * 8 + 1)], 16) 
    if ((f & 0x00010000) > 0):
      memory_device = True
    print ""
    print red,
    print "Device %d" % i
    type_value = int(drt_lines[(i + 1) * 8], 16)
    type_name = get_device_type(type_value)
    print "%s%s:%sDevice Type: %s" % (blue, drt_lines[(i + 1) * 8], green, type_name) 
    print "%s%s:%sDevice Flags:" % (blue, drt_lines[((i + 1) * 8) + 1], green)
    flags = get_device_flags(i)
    for j in flags:
      print "\t%s%s" % (purple, j)

    if memory_device:
      print "%s%s:%sOffset of Memory Device:      0x%08X" % (blue, drt_lines[((i + 1) * 8) + 2], green, int(drt_lines[((i + 1) * 8) + 2], 16))
      print "%s%s:%sSize of Memory device:        0x%08X" % (blue, drt_lines[((i + 1) * 8) + 3], green, int (drt_lines[((i + 1) * 8) + 3], 16))


    else:
      print "%s%s:%sOffset of Peripheral Device:  0x%08X" % (blue, drt_lines[((i + 1) * 8) + 2], green, int(drt_lines[((i + 1) * 8) + 2], 16))
      print "%s%s:%sNumber of Registers :         0x%08X" % (blue, drt_lines[((i + 1) * 8) + 3], green, int(drt_lines[((i + 1) * 8) + 3], 16))

    print "%s%s:%sReserved for future use" % (blue, drt_lines[((i + 1) * 8) + 4], green)
    print "%s%s:%sReserved for future use" % (blue, drt_lines[((i + 1) * 8) + 5], green)
    print "%s%s:%sReserved for future use" % (blue, drt_lines[((i + 1) * 8) + 6], green)
    print "%s%s:%sReserved for future use" % (blue, drt_lines[((i + 1) * 8) + 7], green)


  print white,

 

if __name__ == "__main__":
  """test all functions"""
  dev_list = get_device_list()
  print "Devices:"
  for i in range(0, len(dev_list)):
    print "\t%s" % dev_list[i]["name"]
    print "\t\tID: 0x%04X" % i 
    print "\t\tDescription: %s" % dev_list[i]["description"]

  print "\n\n"
  print "GPIO index: %d" % get_device_index("GPIO")
  #get_device_index ("bob")


