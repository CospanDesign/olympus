#! /usr/bin/python


import time
import random
import sys
import string
from pyftdi.pyftdi.ftdi import Ftdi
from array import array as Array
import getopt 


class Dionysus (object):
  
  SYNC_FIFO_INTERFACE = 0
  SYNC_FIFO_INDEX = 0

  read_timeout = 3
  drt_string = ""
  drt_lines = []
  interrupts = 0
  interrupt_address = 0


  def __init__(self, idVendor, idProduct, dbg = False):
    self.vendor = idVendor
    self.product = idProduct
    self.dbg = dbg
    if self.dbg:
      print "Debug enabled"
    self.dev = Ftdi()
    self.open_dev()
    self.drt = Array('B')

  def __del__(self):
    self.dev.close()


  def set_read_timeout(self, read_timeout):
    self.read_timeout = read_timeout

  def get_read_timeout(self):
    return self.read_timeout

  def reset(self):
    data = Array('B')
    data.extend([0XCD, 0x03, 0x00, 0x00]);
    print "Sending reset..."
    self.dev.purge_buffers()
    self.dev.write_data(data)
    return True
 

  def ping(self):
    data = Array('B')
    data.extend([0XCD, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]);
    print "Sending ping...",
    self.dev.purge_buffers()
    self.dev.write_data(data)
    rsp = Array('B')
    temp = Array('B')

    timeout = time.time() + self.read_timeout

    while time.time() < timeout:
      response = self.dev.read_data(3)
      print ".",
      rsp = Array('B')
      rsp.fromstring(response)
      temp.extend(rsp)
      if 0xDC in rsp:
        print "Got a response"  
        break

    if not 0xDC in rsp:
      print "Response not found"  
      print "temp: " + str(temp)
      return rsp

    index  = rsp.index(0xDC) + 1

    read_data = Array('B')
    read_data.extend(rsp[index:])

    num = 3 - index
    read_data.fromstring(self.dev.read_data(num))
    return True
      
  def write(self, dev_index, offset, data = Array('B'), mem_device = False):
    length = len(data) / 4

    # ID 01 NN NN NN OO AA AA AA DD DD DD DD
      # ID = ID BYTE (0xCD)
      # 01 = Write Command
      # NN = Size of write (3 bytes)
      # OO = Offset of device
      # AA = Address (4 bytes)
      # DD = Data (4 bytes)

    #create an array with the identification byte (0xCD)
    #and code for write (0x01)

    data_out = Array('B', [0xCD, 0x01]) 
    if mem_device:
      print "memory device"
      data_out = Array ('B', [0xCD, 0x11])
    
    #append the length into the frist 32 bits
    fmt_string = "%06X" % (length) 
    data_out.fromstring(fmt_string.decode('hex'))
    offset_string = "00"
    if not mem_device:
      offset_string = "%02X" % (dev_index + 1)
    data_out.fromstring(offset_string.decode('hex'))
    addr_string = "%06X" % offset
    data_out.fromstring(addr_string.decode('hex'))
    
    data_out.extend(data)

    if (self.dbg):
      print "data write string: " + str(data_out)

    #avoid the akward stale bug
    self.dev.purge_buffers()

    self.dev.write_data(data_out)
    rsp = Array('B')

    timeout = time.time() + self.read_timeout
    while time.time() < timeout:
      response = self.dev.read_data(1)
      if len(response) > 0:
        rsp = Array('B')
        rsp.fromstring(response)
        if rsp[0] == 0xDC:
          print "Got a response"  
          break

    if (len(rsp) > 0):
      if rsp[0] != 0xDC:
        print "Response not found"  
        return False

    else:
      print "No Response"
      return False

    response = self.dev.read_data(8)
    rsp = Array('B')
    rsp.fromstring(response)

#   if rsp[0] == 0xFE:
    print "Response: " + str(rsp)
    return True

  def read(self, length, device_offset, address, mem_device = False, drt = False):
    read_data = Array('B')

    write_data = Array('B', [0xCD, 0x02]) 
    if mem_device:
      print "memory device"
      write_data = Array ('B', [0xCD, 0x12])
  
    fmt_string = "%06X" % (length) 
    write_data.fromstring(fmt_string.decode('hex'))
    offset_string = "00"
    if drt:
      offset_string = "%02X" % device_offset
    elif not mem_device:
      offset_string = "%02X" % (device_offset + 1)

    write_data.fromstring(offset_string.decode('hex'))

    addr_string = "%06X" % address
    write_data.fromstring(addr_string.decode('hex'))
    if (self.dbg):
      print "data read string: " + str(write_data)

    self.dev.purge_buffers()
    self.dev.write_data(write_data)

    timeout = time.time() + self.read_timeout
    rsp = Array('B')
    while time.time() < timeout:
      response = self.dev.read_data(1)
      if len(response) > 0:
        rsp = Array('B')
        rsp.fromstring(response)
        if rsp[0] == 0xDC:
          print "Got a response"  
          break

    if len(rsp) > 0:
      if rsp[0] != 0xDC:
        print "Response not found"  
        return read_data
    else:
      print "No Response found"
      return None

    #I need to watch out for the modem status bytes
    response = self.dev.read_data(length * 4 + 8 )
    rsp = Array('B')
    rsp.fromstring(response)

    #I need to watch out for hte modem status bytes
    if self.dbg:
      print "response length: " + str(length * 4 + 8)
      print "response: " + str(rsp)
    #read_data.fromstring(read_string.decode('hex'))
    return rsp[8:]
    

  def debug(self):
    #self.dev.set_dtr_rts(True, True)
    #self.dev.set_dtr(False)
    print "CTS: " + str(self.dev.get_cts())
#    print "DSR: " + str(self.dev.get_dsr())
    s1 = self.dev.modem_status()
    print "S1: " + str(s1)


    print "sending ping...", 
    data = Array('B')
    data.extend([0XCD, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
  # self.dev.set_dtr(True)
    self.dev.purge_buffers()
    self.dev.write_data(data)
    #time.sleep(.01)
#   response = self.dev.read_data(7)
    rsp = Array('B')
#   rsp.fromstring(response)
#   print "rsp: " + str(rsp) 
    temp = Array ('B')

    timeout = time.time() + self.read_timeout

    while time.time() < timeout:

#     if not self.dev.get_dsr():
#       print "DSR low"
      response = self.dev.read_data(3)
      rsp = Array('B')
      rsp.fromstring(response)
      temp.extend(rsp)
      if 0xDC in rsp:
        print "Got a response"  
        break

    if not 0xDC in rsp:
      print "Response not found"  
      print "temp: " + str(temp)
      return rsp

    index  = rsp.index(0xDC) + 1

    read_data = Array('B')
    read_data.extend(rsp[index:])

    num = 3 - index
    read_data.fromstring(self.dev.read_data(num))

    print "read data: " + str(read_data)
    
#
#   data = Array('B')
#   data.extend([0XCD, 0x02, 0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00])
#   print "to device: " + str(data)
#
#   self.dev.write_data(data)
#
#

#   print "reading"


#   time.sleep(.2)
#   response = self.dev.read_data(64)

#   rsp = Array('B')
#   rsp.fromstring(response)
#   print "rsp: " + str(rsp) 
#   for a in rsp:
#     print "Data: %02X" % (a)
#   s1 = self.dev.modem_status()
#   print "S1: " + str(s1)




#   data = Array('B')
#   data.extend([0XCD, 0x01, 0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF])
#
#   self.dev.write_data(data)
#   response = self.dev.read_data(32)
#
#   data = Array('B')
#   data.extend([0XCD, 0x02, 0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF])
#   print "to device: " + str(data)
#
#   self.dev.write_data(data)
#
#
#   self.dev.set_dtr_rts(True, True)
#   s1 = self.dev.modem_status()
#   print "S1: " + str(s1)


#   print "reading"


#   response = self.dev.read_data(4)

#   rsp = Array('B')
#   rsp.fromstring(response)
#   print "rsp: " + str(rsp)
#   for a in rsp:
#     print "Data: %02X" % (a)
#     print "Data: %02X" % (a)
#   time.sleep(.1)
#   response = self.dev.read_data(16)


#   rsp = Array('B')
#   rsp.fromstring(response)
#   print "rsp: " + str(rsp) 
#   for a in rsp:
#     print "Data: %02X" % (a)
#   s1 = self.dev.modem_status()
#   print "S1: " + str(s1)

  def wait_for_interrupts(self, wait_time = 1):
    timeout = time.time() + wait_time

    temp = Array ('B')
    while time.time() < timeout:

      response = self.dev.read_data(3)
      rsp = Array('B')
      rsp.fromstring(response)
      temp.extend(rsp)
      if 0xDC in rsp:
        print "Got a response"  
        break

    if not 0xDC in rsp:
      print "Response not found"  
      return False

    index  = rsp.index(0xDC) + 1

    read_data = Array('B')
    read_data.extend(rsp[index:])

    num = 3 - index
    read_data.fromstring(self.dev.read_data(num))
    if (len (read_data) >= 4):
      self.interrupts = read_data[0] << 24 | read_data[1] << 16 | read_data[2] << 8 | read_data[3]
    
    if (self.dbg):
      print "interrupts: " + str(self.interrupts)
    return True
    
  def is_device_attached (self, device_id ):
    for dev_index in range (0, self.num_of_devices):
      dev_id = string.atoi(self.drt_lines[((dev_index + 1) * 8)], 16)
      if (self.dbg):
        print "dev_id: " + str(dev_id)
      if (dev_id == device_id):
        return True
    return False
  
  def get_device_index(self, device_id):
    for dev_index in range(0, self.num_of_devices):
      dev_id = string.atoi(self.drt_lines[((dev_index + 1) * 8)], 16)
      address_offset = string.atoi(self.drt_lines[((dev_index + 1) * 8) + 2], 16)
      if (device_id == device_id):
        return dev_index
    return -1

  def is_interrupt_for_slave(self, device_id = 0):
    device_id += 1
    if (2**device_id & self.interrupts):
      return True
    return False

  def get_address_from_dev_index(self, dev_index):  
    return string.atoi(self.drt_lines[((dev_index + 1) * 8) + 2], 16)
    
  def read_drt(self):
    data = Array('B')
    data = self.read(8, 0, 0, drt = True)
    self.drt.extend(data)
    self.drt_string = ""
    self.drt_lines = []
#    print "drt: " + str(self.drt)
    self.num_of_devices = (self.drt[4] << 24 | self.drt[5] << 16 | self.drt[6] << 8 | self.drt[7])
    #print "number of devices: " + str(num_of_devices)
    len_to_read = self.num_of_devices * 8
    self.drt.extend(self.read(len_to_read, 0, 8, drt = True))
#    print "drt: " + str(self.drt)
    display_len = 8 + self.num_of_devices * 8

    for i in range (0, display_len):
      self.drt_string += "%02X%02X%02X%02X\n"% (self.drt[i * 4], self.drt[(i * 4) + 1], self.drt[i * 4 + 2], self.drt[i * 4 + 3])

    print self.drt_string
    self.drt_lines = self.drt_string.splitlines()


  def open_dev(self):
    frequency = 30.0E6
    latency = 2
    self.dev.open(self.vendor, self.product, 0)
    # Drain input buffer
    self.dev.purge_buffers()

    # Reset

    # Enable MPSSE mode
    self.dev.set_bitmode(0x00, Ftdi.BITMODE_SYNCFF)
    # Configure clock

    frequency = self.dev._set_frequency(frequency)
    # Set latency timer
    self.dev.set_latency_timer(latency)
    # Set chunk size
    self.dev.write_data_set_chunksize(0x10000)
    self.dev.read_data_set_chunksize(0x10000)

    self.dev.set_flowctrl('hw')
    self.dev.purge_buffers()
  

def test_leds(syc, dev_index):
  print "Found GPIO"
  print "Enable all Output GPIOs"
  syc.write(dev_index, 1, Array('B', [0xFF, 0xFF, 0xFF, 0xFF]))
  print "flash all LED's once"
  #clear
  syc.write(dev_index, 0, Array('B', [0x00, 0x00, 0x00, 0x00]))
  syc.write(dev_index, 0, Array('B', [0xFF, 0xFF, 0xFF, 0xFF]))
  time.sleep(1)
  syc.write(dev_index, 0, Array('B', [0x00, 0x00, 0x00, 0x00]))
  time.sleep(.1)
  

def test_buttons(syc, dev_index):
   print "read buttons in 1 second..."
   time.sleep(1)
   grd = syc.read(1, dev_index, 0)
   if len(grd) > 0:
     gpio_read = grd[0] << 24 | grd[1] << 16 | grd[2] << 8 | grd[3] 
     print "gpio read: " + hex(gpio_read)

   print "testing interrupts, setting interrupts up for postivie edge detect"
   #positive edge detect
   syc.write(dev_index, 4, Array('B', [0xFF, 0xFF, 0xFF, 0xFF]))
   #enable all interrupts
   syc.write(dev_index, 3, Array('B', [0xFF, 0xFF, 0xFF, 0xFF]))

   print "testing interrupts, waiting for 5 seconds..."
     
   if (syc.wait_for_interrupts(wait_time = 5)):
     #print "detected interrupts!"
     #print "interrupts: " + str(syc.interrupts)
     #print "device index: " + str(dev_index)
     #print "blah: " + str(2**(dev_index + 1))
     if (syc.is_interrupt_for_slave(dev_index)):
       print "interrupt for GPIO!"
       grd = syc.read(1, dev_index, 0)
       gpio_read = grd[0] << 24 | grd[1] << 16 | grd[2] << 8 | grd[3] 
       print "gpio read: " + hex(gpio_read)


def test_all_memory (syc = None):
 for dev_index in range (0, syc.num_of_devices):
    device_id = string.atoi(syc.drt_lines[((dev_index + 1) * 8)], 16)
    flags = string.atoi(syc.drt_lines[((dev_index + 1) * 8) + 1], 16)
    address_offset = string.atoi(syc.drt_lines[((dev_index + 1) * 8) + 2], 16)
    num_of_registers = string.atoi(syc.drt_lines[((dev_index + 1) * 8) + 3], 16)
    data_list = list()

    if (device_id == 5):
      print "found Memory device"
      mem_bus = False
      if ((flags & 0x00010000) > 0):
        print "Memory slave is on Memory bus"
        mem_bus = True 
      else:
        print "Memory slave is on peripheral bus"

      print "Writing to all memory locations"
      n1 = 0x00
      n2 = 0x00
      n3 = 0x00
      n4 = 0x00
      
      rand = int(random.random() * 256.0)
      
      #Create 1024 * 2 array
      data_out = Array('B')
      num = 0
      try:
        for i in range (0, 4 * 110):
          num = (i + rand) % 255
          if (i / 256) % 2 == 1:
            data_out.append( 255 - (num))
          else:
            data_out.append(num)

 
      except OverflowError as err:
        print "Overflow Error: %d >= 256" % num
        sys.exit(1)
 

      print "Generated a continuous stream of data with a random start"
#      print "Data: "
#      for i in range (0, len(data_out)):
#        print "\t%X" % data_out[i]

#      bank_count = 4
#      row_count = 12
#      column_count = 10
#      data_out = Array('B', [n1, n2, n3, n4])
      print "Writing %d DWORDS of data" % (len(data_out))
      result = syc.write(dev_index, 0, data_out, mem_bus)
      if result:
        print "Write Successful!"
      else:
        print "Write Failed!"

      #time.sleep(1)

      print "Reading %d DWORDS of data" % (len(data_out))
      data_in = Array('B')
      data_in = syc.read(len(data_out) / 4, dev_index, 0,  mem_bus)

      print "Comparing values"
      fail = False
      fail_count = 0
      if len(data_out) != len(data_in):
        print "data_in length not equal to data_out length:"
        print "\tdata_in: %d, data_out: %d" % (len(data_in), len(data_out))
        fail = True

      else:
        for i in range (0, len(data_out)):
          if data_in[i] != data_out[i]:
            fail = True
            print "Mismatch at %d: READ DATA 0x%X != WRITE DATA 0x%X" % (i, data_in[i], data_out[i])
            fail_count += 1
 
      if not fail:
        print "Memory test passed!"
      elif (fail_count == 0):
        print "Data length of data_in and data_out do not match"
      else:
        print "Failed: %d mismatches" % fail_count


      data_in = Array('B')
      data_in = syc.read(len(data_out) / 4, dev_index, 0,  mem_bus)

      print "Comparing values"
      fail = False
      fail_count = 0
      if len(data_out) != len(data_in):
        print "data_in length not equal to data_out length:"
        print "\tdata_in: %d, data_out: %d" % (len(data_in), len(data_out))
        fail = True

      else:
        for i in range (0, len(data_out)):
          if data_in[i] != data_out[i]:
            fail = True
            print "Mismatch at %d: READ DATA 0x%X != WRITE DATA 0x%X" % (i, data_in[i], data_out[i])
            fail_count += 1
 
      if not fail:
        print "Memory test passed!"
      elif (fail_count == 0):
        print "Data length of data_in and data_out do not match"
      else:
        print "Failed: %d mismatches" % fail_count



#      for b in range (0, bank_count):
#        for r in range (0, row_count):
#          syc.write(dev_index, b * (2 ** 22) + r * (2 ** 10), data_out, mem_bus)
#          print "Wrote To Column at: Bank: 0x%X Row: 0x%X" % (b, r) 
#             
#      print "Reading from all memory locations"
#      data_in = Array('B')
#      for b in range (0, bank_count):
#        for r in range (0, row_count):
#          data_in = syc.read(2048, dev_index,  b * (2 ** 22) + r * (2 ** 10), data_out, mem_bus)
#          for i in data_in:
#            if data_in[i] != (i % 256):
#              print "Error: %X != %X" % (data_in[i], i % 256)
# 
#          print "Read from Column at: Bank: 0x%X Row: 0x%X" % (b, r) 
       
    

  

def test_memory(syc = None):
  for dev_index in range (0, syc.num_of_devices):
    device_id = string.atoi(syc.drt_lines[((dev_index + 1) * 8)], 16)
    flags = string.atoi(syc.drt_lines[((dev_index + 1) * 8) + 1], 16)
    address_offset = string.atoi(syc.drt_lines[((dev_index + 1) * 8) + 2], 16)
    num_of_registers = string.atoi(syc.drt_lines[((dev_index + 1) * 8) + 3], 16)
    data_list = list()

    if (device_id == 5):
      print "found Memory device"
      mem_bus = False
      if ((flags & 0x00010000) > 0):
        print "Memory slave is on Memory bus"
        mem_bus = True 
      else:
        print "Memory slave is on peripheral bus"

      data_out  = Array('B', [0xAA, 0xBB, 0xCC, 0xDD, 0x55, 0x66, 0x77, 0x88])
      #data_out  = Array('B', [0x11, 0x22, 0x33, 0x44])
      result = syc.write(dev_index, 0, data_out, mem_bus)
      if result:
        print "Write Successful!"
      else:
        print "Write Failed!"

      print "Read:"
      #time.sleep(1)

      mem_data = syc.read(1, dev_index, 0, mem_bus)
      print "mem data: " + str(mem_data);
      print "hex: "
      for i in range (0, len(mem_data)):
        print str(hex(mem_data[i])) + ", ",

      print " "
      #time.sleep(1)

      #mem_data = syc.read(1, dev_index, 0, mem_bus)
      mem_data = syc.read(2, dev_index, 0, mem_bus)
      print "mem data: " + str(mem_data);
      print "hex: "
      for i in range (0, len(mem_data)):
        print str(hex(mem_data[i])) + ", ",

      print " "
      #time.sleep(1)

      #mem_data = syc.read(1, dev_index, 0, mem_bus)
      mem_data = syc.read(1, dev_index, 8, mem_bus)
      print "mem data: " + str(mem_data);
      print "hex: "
      for i in range (0, len(mem_data)):
        print str(hex(mem_data[i])) + ", ",

      print " "
      #time.sleep(1)

      mem_data = syc.read(1, dev_index, 0, mem_bus)
      print "mem data: " + str(mem_data);
      print "hex: "
      for i in range (0, len(mem_data)):
        print str(hex(mem_data[i])) + ", ",

      print " "



def dionysus_unit_test(syc = None):
  print "unit test"
  print "Found " + str(syc.num_of_devices) + " slave(s)"
  print "Searching for standard devices..."
  for dev_index in range (0, (syc.num_of_devices)):
    device_id = string.atoi(syc.drt_lines[((dev_index + 1) * 8)], 16)

    print "dev id: " + str(device_id)
    flags = string.atoi(syc.drt_lines[((dev_index + 1) * 8) + 1], 16)
    address_offset = string.atoi(syc.drt_lines[((dev_index + 1) * 8) + 2], 16)
    num_of_registers = string.atoi(syc.drt_lines[((dev_index + 1) * 8) + 3], 16)
    data_list = list()
    if (device_id == 5):
      test_memory(syc)
  
    if (device_id == 1):
      test_leds(syc, dev_index)
      test_buttons(syc, dev_index)
  
 
def usage():
  """prints out a helpful message to the user"""
  print ""
  print "usage: dionysus.py [options]"
  print ""
  print "-h\t--help\t\t\t: displays this help"
  print "-d\t--debug\t\t\t: runs the debug analysis"
  print "-m\t--memory\t\t\t: test only memory"
  print "-l\t--long\t\t\t\t: long memory test"
  print ""
  

if __name__ == '__main__':
  print "starting..."
  argv = sys.argv[1:]
  mem_only = False
  long_mem_test = False

  try:
    syc = Dionysus(0x0403, 0x8530)
    if (len(argv) > 0):
      opts = None
      opts, args = getopt.getopt(argv, "hdml", ["help", "debug", "memory", "long"])
      for opt, arg in opts:
        if opt in ("-h", "--help"):
          usage()
          sys.exit()
        elif opt in ("-d", "--debug"):
          print "Debug mode"
          syc = Dionysus(0x0403, 0x8530, dbg=True)
          syc.debug()
        elif opt in ("-m", "--memory"):
          mem_only = True

        elif opt in ("-l", "--long"):
          long_mem_test = True


    syc.reset()

    if (syc.ping()):
      print "Ping responded successfully"
      print "Retrieving DRT"
      syc.read_drt()
      if (syc.dbg):
        print "testing if device is attached..." + str(syc.is_device_attached(1))
        print "testing get_device_index..." + str(syc.get_device_index(1) == 0)
        print "testing get_address_from_index..." + str(syc.get_address_from_dev_index(0) == 0x01000000)

      if long_mem_test:
        test_all_memory(syc) 

      elif mem_only:
        test_memory(syc)

      else:
        dionysus_unit_test(syc)

      


  except IOError, ex:
    print "PyFtdi IOError: " + str(ex)
  except AttributeError, ex:
    print "PyFtdi AttributeError: " + str(ex)
  except getopt.GetoptError, err:
    print (err)
    usage()
"""
  except ex:
    print "PyFtdi Unknown Error: " + str(ex)

"""

