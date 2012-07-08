#! /usr/bin/python
import json

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
    f = open("drt.json", "r")
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



if __name__ == "__main__":
  """test all functions"""
  dev_list = get_device_list()
  print "Devices:"
  for i in range(0, len(dev_list)):
    print "\t%s" % dev_list[i]["name"]
    print "\t\tID: 0x%04X" % i 
    print "\t\tDescription: %s" % dev_list[i]["description"]



