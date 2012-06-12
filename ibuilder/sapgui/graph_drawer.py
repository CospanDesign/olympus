#!/usr/bin/python

import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo
from gtk import gdk
import math
from types import *
from graph_drawing_area import GraphDrawingArea
from graph_utils import Box
import sap_graph_manager as gm
from sap_graph_manager import NodeType
from sap_graph_manager import SlaveType
import status_text


def enum(*sequential, **named):
  enums = dict(zip(sequential, range(len(sequential))), **named)
  return type('Enum', (), enums)

# Different ways to draw a box
BoxStyle = enum('OUTLINE', 'SOLID')

def motion_notify_event(widget, event):
  '''Handle mouse motion.'''
  state = event.state

  if event.is_hint:
    x, y, state = event.window.get_pointer()
  else:
    x = event.x
    y = event.y
    state = event.state

  widget.set_pointer_value(x, y)

  if state & gtk.gdk.BUTTON1_MASK:
    widget.start_moving()
#    widget.set_moving_state(1)

  return True

def button_press_event(widget, event):
  '''Handles mouse button press.'''
  x, y, state = event.window.get_pointer()
  widget.button_press()
  widget.set_pointer_value(x, y)
  return True

def button_release_event(widget, event):
  '''Handles mouse button release.'''
  x, y, state = event.window.get_pointer()
  widget.set_pointer_value(x, y)
  widget.stop_moving()
  widget.button_release()
  return True

#"""Custom Cairo Drawing surface."""

class GraphDrawer(GraphDrawingArea):
  def __init__(self, sgm):
    GraphDrawingArea.__init__(self)
    self.val = 0
    self.debug = False
    self.dy = 10
    self.sgm = sgm  # Save the reference to the SGM.

    self.dash_size = 30
    self.dash_total_size = 4.0
    self.dash_width = 1.0

    self.box_width_ratio = .75 # Ratio from width of column to box.
    self.box_height_ratio = .5 # Ratio from width to height.

    # The height of the slaves can change when more are added.
    self.pslave_height_ratio = .5
    self.mslave_height_ratio = .5

    # Padding
    self.x_padding = 10
    self.y_padding = 10

    # Boxes
    self.boxes = {}
    self.boxes["host_interface"] = Box()
    self.boxes["master"] = Box()
    self.boxes["pic"] = Box()
    self.boxes["mic"] = Box()
    self.boxes["pslaves"] = []
    self.boxes["mslaves"] = []
    self.boxes["trash"] = Box()
    self.boxes["arbitrator"] = Box()
    self.boxes["back"] = Box()
    self.boxes["remove"] = Box()

    self.temp_box = Box()
    self.status = status_text.StatusText()

    # Initial prev_width, prev_height
    self.prev_width = -1
    self.prev_height = -1
    self.regenerate_boxes = False

    ps_count = self.sgm.get_number_of_slaves(SlaveType.PERIPHERAL)
    ms_count = self.sgm.get_number_of_slaves(SlaveType.MEMORY)

    for i in xrange(ps_count):
      self.boxes["pslaves"].append(Box())

    for i in xrange(ms_count):
      self.boxes["mslaves"].append(Box())


    self.prev_ps_count = ps_count
    self.prev_ms_count = ms_count

    # Add mouse event handling.
    self.p_x = 0
    self.p_y = 0
    self.moving = 0

    self.connect("motion_notify_event", motion_notify_event)
    self.connect("button_press_event", button_press_event)
    self.connect("button_release_event", button_release_event)

    self.set_events(gtk.gdk.EXPOSURE_MASK
                  | gtk.gdk.LEAVE_NOTIFY_MASK
                  | gtk.gdk.BUTTON_PRESS_MASK
                  | gtk.gdk.BUTTON_RELEASE_MASK
                  | gtk.gdk.POINTER_MOTION_MASK
                  | gtk.gdk.POINTER_MOTION_HINT_MASK)

    self.selected_node = None
    self.rel_x = 0
    self.rel_y = 0

    self.mov_x = 0
    self.mov_y = 0
    self.slave_add_callback = None
    self.slave_remove_callback = None
    self.slave_move_callback = None
    self.slave_select_callback = None
    self.slave_arbitrator_select_callback = None
    self.back_selected_callback = None
    self.arbitrator_connected_callback = None
    self.arbitrator_disconnected_callback = None
    self.new_slave = 0

    # Initialize drag receive.
    self.drag_dest_set(gtk.DEST_DEFAULT_ALL, [], gtk.gdk.ACTION_COPY)
    self.drag_dest_add_text_targets()
    self.connect("drag-data-received", self.on_drag_data_received)

    self.en_arb_view = False
    self.selected_master = ""
    self.selected_master_node = None
    self.selected_arb_master = ""
    self.connected_slave = ""

  def on_drag_data_received(self, widget, drag_content, x, y, data, info, my_data):
    """A slave has been dragged to this window and dropped."""
    text = data.get_text()
    if self.debug:
      print "graph drawer received text: %s" % text
    if not self.in_slave_column(x, y):
      return

    if self.debug:
      print "in slave area"

    drop_type = None
    sl = []
    if y < (self.prev_height / 2.0):
      if self.debug:
        print "in peripheral bus"
      drop_type = SlaveType.PERIPHERAL
      sl = self.boxes["pslaves"]
    else:
      drop_type = SlaveType.MEMORY
      sl = self.boxes["mslaves"]

    drop_index = 0
    for slave_box in sl:
      if y < slave_box.y + (slave_box.height / 2.0):
        break
      else:
        drop_index += 1

    if self.debug:
      print "drop location is at %d" % drop_index

    if (self.slave_add_callback is not None):
      self.slave_add_callback(text, drop_type, drop_index)

    f = text.rpartition("/")[2]
    tp = "memory"
    if drop_type == SlaveType.PERIPHERAL:
      tp = "peripheral"
    self.status.print_info(__file__, "droping slave %s in the %s bus at %d" % (f, tp, drop_index))

  def set_slave_arbitrator_select_callback(self, slave_arbitrator_select_callback):
    self.slave_arbitrator_select_callback = slave_arbitrator_select_callback

  def set_slave_select_callback(self, slave_select_callback):
    self.slave_select_callback = slave_select_callback

  def set_slave_add_callback(self, slave_add_callback):
    self.slave_add_callback = slave_add_callback

  def set_slave_remove_callback(self, slave_remove_callback):
    self.slave_remove_callback = slave_remove_callback

  def set_slave_move_callback(self, slave_move_callback):
    self.slave_move_callback = slave_move_callback

  def set_back_selected(self, back_selected):
    self.back_selected_callback = back_selected

  def set_arb_connect(self, arb_connect):
    self.arbitrator_connected_callback = arb_connect

  def set_arb_disconnect(self, arb_disconnect):
    self.arbitrator_disconnected_callback = arb_disconnect

  def can_node_move(self, node):
    # Cannot move when in arbitrator view.
    if self.en_arb_view:
      return False

    if node is None:
      return False

    if node.node_type != NodeType.SLAVE:
      return False

    # Can't move the DRT
    if node.slave_type == SlaveType.PERIPHERAL and node.slave_index == 0:
      return False

    return True

  def start_moving(self):
    if self.moving == 1:
      return

    # The node should have been selected in set_button_state.
    node = self.selected_node
    if self.can_node_move(node):
      # Store the pointer's top-relative position.
      if node.slave_type == SlaveType.PERIPHERAL:
        b = self.boxes["pslaves"][node.slave_index]
      else:
        b = self.boxes["mslaves"][node.slave_index]

      self.rel_x = self.p_x - b.x
      self.rel_y = self.p_y - b.y

      # Tell everyone we are moving.
      self.moving = 1

  def in_slave_column(self, x, y):
    cw = self.get_column_width(self.prev_width)
    sc_left = cw * 3
    sc_right = cw * 4
    sc_top = 0
    sc_bot = self.prev_height

    if x < sc_left:
      return False
    if x > sc_right:
      return False
    if y < sc_top:
      return False
    if y > sc_bot:
      return False
    return True

  def in_trash_can(self):
    cw = self.get_column_width(self.prev_width)
    b = self.boxes["trash"]

    if self.p_x < b.x:
      return False
    if self.p_x > b.x + b.width:
      return False
    if self.p_y < b.y:
      return False
    if self.p_y > b.y + b.height:
      return False
    return True

  def stop_moving (self):
    if self.moving == 0:
      return

    if self.debug:
      print "dropping slave"

    self.moving = 0
    node = self.selected_node

    # Check to see if the slave is within the slave column.
    if node.slave_type == SlaveType.PERIPHERAL:
      b = self.boxes["pslaves"][node.slave_index]
    else:
      b = self.boxes["mslaves"][node.slave_index]

    # Check if were are within the slave area.
    if self.debug:
      print "check to see if we're in slave area"

    if self.in_trash_can():
      if self.debug:
        print "removing slave"
      if self.new_slave:
        print "can't remove a new slave"
        return
      if (self.slave_remove_callback is not None):
        self.slave_remove_callback(node.slave_type, node.slave_index)

    if not self.in_slave_column(self.mov_x, self.mov_y):
      return

    if self.debug:
      print "in slave area"

    mid_x = self.mov_x + (b.width / 2.0)
    mid_y = self.mov_y + (b.height / 2.0)


    if mid_y < (self.prev_height / 2.0):
      if self.debug:
        print "in peripheral bus"
      drop_type = SlaveType.PERIPHERAL
      sl = self.boxes["pslaves"]

    else:
      if self.debug:
        print "in memory bus"
      drop_type = SlaveType.MEMORY
      sl = self.boxes["mslaves"]

    # Now find where in the bus it is dropped.
    drop_index = 0
    for slave_box in sl:
      if mid_y < slave_box.y + (slave_box.height / 2.0):
        break
      else:
        drop_index += 1

    if self.debug:
      print "drop location is at %d" % drop_index

    if self.debug:
      print "moving existing slave"

    result = False
    if (self.slave_move_callback is not None):
      result = self.slave_move_callback(node.slave_type,
                                        node.slave_index,
                                        drop_type,
                                        drop_index)

  def button_press(self):
    node_name = self.get_selected_name(self.p_x, self.p_y)
    if len(node_name) > 0:
      if node_name == "back":
        self.back_selected_callback()
        return

      if node_name == "remove":
        if self.debug:
          print "remove selected"
        self.arbitrator_disconnected_callback( \
                    self.selected_master,
                    self.selected_arb_master)
        return

      if self.en_arb_view:

        column_width = self.get_column_width(self.prev_width)
        # Reject any button hits outside of column 3.
        if self.p_x < (column_width * 3):
          return

        sn = self.selected_node
#        print "m, a, s: %s, %s, %s" % (self.selected_master, self.selected_arb_master, node_name)
        self.arbitrator_connected_callback(  self.selected_master,
                          self.selected_arb_master,
                          node_name)



      self.selected_node = self.sgm.get_node(node_name)
      sn = self.selected_node
      name = sn.name
      tags = self.sgm.get_parameters(node_name)
      arb_master = ""

      # Check to see if an arbitrator master was selected.
      if self.is_arbitrator_master_selected(node_name, self.p_x, self.p_y):
        arb_master = self.get_arbitrator_master_selected(node_name,
                                                         self.p_x,
                                                         self.p_y)

#        print "arbitrator master: %s selected"% (arb_master)
        self.selected_master_node = sn

        if sn.slave_type == SlaveType.PERIPHERAL:
          b = self.boxes["pslaves"][sn.slave_index]
        else:
          b = self.boxes["mslaves"][sn.slave_index]
        connected_slave = b.get_connected_slave(arb_master)
        self.slave_arbitrator_select_callback(node_name, arb_master, connected_slave)

      self.slave_select_callback(name, tags)
    else:
      self.slave_select_callback(None, None)

  def button_release(self):
    self.selected_node = None

  def set_pointer_value(self, x, y):
    self.p_x = x
    self.p_y = y

  def force_update(self):
    ps_count = self.sgm.get_number_of_slaves(SlaveType.PERIPHERAL)
    ms_count = self.sgm.get_number_of_slaves(SlaveType.MEMORY)

    self.boxes["pslaves"] = []
    self.boxes["mslaves"] = []

    for i in range (0, ps_count):
      self.boxes["pslaves"].append(Box())

    for i in range (0, ms_count):
      self.boxes["mslaves"].append(Box())

    self.regenerate_boxes = True
#    self.generate_boxes(self.prev_width, self.prev_height)


  def generate_boxes(self, width, height):
    column_width = self.get_column_width(width)

    # Trash can.
    b = self.boxes["trash"]
    b.set_name("Trash")

    box_width = column_width * self.box_width_ratio
    box_height = box_width * self.box_height_ratio
    box_x = column_width + (column_width - box_width) / 2.0
    box_y = height - box_height - ((column_width - box_width) / 2.0)

    b.set_location_and_size(box_x, box_y, box_width, box_height)

    b.set_color(1.0, 0.0, 0.0)

    # Back button.
    b = self.boxes["back"]
    b.set_name("Back")
    box_width = column_width * self.box_width_ratio / 2.0
    box_height = box_width * 2.0 * self.box_height_ratio
    box_x = ((column_width - box_width) / 2.0) + box_width / 2.0
    box_y = height / 2.0 - box_height / 2.0

    b.set_location_and_size(box_x, box_y, box_width, box_height)

    b.set_color(1.0, 1.0, 1.0)

    # Remove button.
    b = self.boxes["remove"]
    b.set_name("Remove")
    box_width = column_width * self.box_width_ratio / 2.0
    box_height = box_width * self.box_height_ratio
    box_x = ((column_width - box_width) / 2.0) + 2 * column_width
    box_y = 0

    b.set_location_and_size(box_x, box_y, box_width, box_height)

    b.set_color(1.0, 0.0, 0.0)

    if self.en_arb_view == False:
      # Host interface.
      b = self.boxes["host_interface"]
      node = self.sgm.get_host_interface_node()
      b.set_name(node.name)
      box_width = column_width * self.box_width_ratio
      box_height = box_width * self.box_height_ratio
      box_x = (column_width - box_width) / 2.0
      box_y = (height / 2.0) - box_height / 2.0

      b.set_location_and_size(box_x, box_y, box_width, box_height)
      b.set_color(0.0, 1.0, 0.0)

      # Master.
      b = self.boxes["master"]
      b.set_name("Master")
      box_width = column_width * self.box_width_ratio
      box_height = height - (column_width - box_width)
      box_x = (column_width - box_width) / 2.0 + column_width
      box_y = (column_width - box_width) / 2.0

      b.set_location_and_size(box_x, box_y, box_width, box_height)
      b.set_color(1.0, 0.5, 0.0)

    # Peripheral interconnect.
    b = self.boxes["pic"]
    b.set_name("Peripherals")
    box_width = column_width * self.box_width_ratio
    box_height = (height / 2.0) - (column_width - box_width)

    if self.en_arb_view:
      box_x = (column_width - box_width) / 2.0
    else:
      box_x = (column_width - box_width) / 2.0 + 2 * column_width
    box_y = ((column_width - box_width) / 2.0)

    b.set_location_and_size(box_x, box_y, box_width, box_height)
    b.set_color(1.0, 1.0, 0.0)

    # Memory interconnect.
    b = self.boxes["mic"]
    b.set_name("Memories")
    box_width = column_width * self.box_width_ratio
    box_height = (height / 2.0) - (column_width - box_width)

    if self.en_arb_view:
      box_x = (column_width - box_width) / 2.0
    else:
      box_x = (column_width - box_width) / 2.0 + (2 * column_width)
    box_y = (column_width - box_width) / 2.0 + height / 2.0

    b.set_location_and_size(box_x, box_y, box_width, box_height)
    b.set_color(1.0, 1.0, 0.0)

    # Peripheral slaves.
    for i in range (0, len(self.boxes["pslaves"])):
      b = self.boxes["pslaves"][i]
      node = self.sgm.get_slave_at(i, SlaveType.PERIPHERAL)
      b.set_name(node.name)
      box_width = column_width * self.box_width_ratio
      box_height = box_width * self.pslave_height_ratio
      box_x = (column_width - box_width) / 2.0 + (column_width * 3)
      box_y = (column_width - box_width) / 2.0 + \
          i * ((column_width - box_width) + box_height)

      b.set_location_and_size(box_x, box_y, box_width, box_height)
      b.set_color(0.0, 0.0, 1.0)

      # Setup the arbitrator masters.
      arbs = node.parameters["arbitrator_masters"]
      arb_res = self.sgm.get_connected_slaves(node.unique_name)
#      if self.debug:
#        print "arbitrator masters: " + str(arbs)
      s_name = ""

      if len(arb_res.keys()) > 0:
        # We're not a master, but some slave is attached to us.
        b.arb_slave = True

      # The DRT should never be an arbitrator slave.
      if self.en_arb_view and i == 0:
        box_x = (column_width - box_width) / 2.0 + (column_width * 1)
        b.set_location_and_size(box_x, box_y, box_width, box_height)

      for j in xrange(len(arbs)):
        arb = arbs[j]
        is_connected = False
#        if self.debug:
#          print "arb: " + arb
        b.arb_slave = False
        for key in arb_res.keys():
          if arb == key:
            is_connected = True
            s_name = arb_res[key]
          if key not in arbs:
            b.arb_slave = True
            continue

        if self.en_arb_view:
          if self.selected_master_node == node or \
              s_name == self.connected_slave or i == 0:
            box_x = (column_width - box_width) / 2.0 + (column_width * 1)
            b.set_location_and_size(box_x, box_y, box_width, box_height)

        if self.debug:
          print "add arbitrator master"
        b.add_arbitrator_master(arb, is_connected, s_name)

      # Generate an arbitrator box if this is the selected slave.
      if self.en_arb_view and self.connected_slave == node.unique_name:
        if self.debug:
          print "generting arbitrator box"
        b = self.boxes["arbitrator"]
        b.name = "arbitrator"

        box_x = (column_width - box_width) / 2.0 + (column_width * 2)
        b.set_color(1.0, 1.0, 1.0)
        b.set_location_and_size(box_x, box_y, box_width, box_height)

    # Memory slaves.
    for i in xrange(len(self.boxes["mslaves"])):
      b = self.boxes["mslaves"][i]
      node = self.sgm.get_slave_at(i, SlaveType.MEMORY)
      b.set_name(node.name)
      box_width = column_width * self.box_width_ratio
      box_height = box_width * self.mslave_height_ratio
      box_x = (column_width - box_width) / 2.0 + (column_width * 3)
      box_y = (column_width - box_width) / 2.0 + \
          i * ((column_width - box_width) + box_height) + height / 2

      b.set_location_and_size(box_x, box_y, box_width, box_height)
      b.set_color(1.0, 0.0, 1.0)

      # Setup the arbitrator masters.
      arbs = node.parameters["arbitrator_masters"]
      arb_res = self.sgm.get_connected_slaves(node.unique_name)
#      if self.debug:
#        print "arbitrator masters: " + str(arbs)
      s_name = ""

      if len(arb_res.keys()) > 0:
        # We're not a master, but some slave is attached to us
        b.arb_slave = True

      for i in range(0, len(arbs)):
        arb = arbs[i]
        is_connected = False
#        if self.debug:
#          print "arb: " + arb

        b.arb_slave = False
        for key in arb_res.keys():
          if arb == key:
            is_connected = True
            s_name = arb_res[key]

          if key not in arbs:
            b.arb_slave = True
            continue

          if self.en_arb_view:
            if   self.selected_master_node == node or \
              s_name == self.connected_slave:
              box_x = (column_width - box_width) / 2.0 + (column_width * 1)
              b.set_location_and_size(box_x, box_y, box_width, box_height)

          b.add_arbitrator_master(arb, is_connected, s_name)

      # Generate an arbitrator box if this is the selected slave.
      if self.en_arb_view and self.connected_slave == node.unique_name:
        if self.debug:
          print "generting (mem)arbitrator box"
        b = self.boxes["arbitrator"]
        b.name = "arbitrator"

        box_x = (column_width - box_width) / 2.0 + (column_width * 2)
        b.set_color(1.0, 1.0, 1.0)
        b.set_location_and_size(box_x, box_y, box_width, box_height)


  def set_debug_mode(self, debug):
    self.debug = debug

  def draw(self, width, height):
    # Compare the current width and height with the previous.  If there is a
    # difference, calculate the size of all the boxes.
    ps_count = self.sgm.get_number_of_slaves(SlaveType.PERIPHERAL)
    ms_count = self.sgm.get_number_of_slaves(SlaveType.MEMORY)

    if width != self.prev_width or \
        height != self.prev_height or \
        self.prev_ps_count != ps_count or \
        self.prev_ms_count != ms_count  or \
        self.regenerate_boxes:

      if self.debug:
        print "calculate"
      self.regenerate_boxes = False
      self.generate_boxes(width, height)

    # Save the previous values.
    self.prev_width = width
    self.prev_height = height

    self.prev_ps_count = ps_count
    self.prev_ms_count = ms_count

    # If debug flag enabled write the debug in the top left.
    if self.debug:
      self.display_debug(width, height)

#    self.draw_wb_lines(width, height)
    if self.en_arb_view:
      self.draw_arbitrator_view(width, height)
    else:
      self.draw_bus_view(width, height)

  def set_arbitrator_view(self, node_name, arb_master, connected_slave, enable):
    """Enables or disables arbitrator view.  The calling function must specify
    the selected node and the connected slave (or empty string if not
    connected)."""
    self.selected_master = node_name
    self.selected_arb_master = arb_master
    self.connected_slave = connected_slave
    self.en_arb_view = enable

  def draw_arbitrator_view(self, width, height):
    self.draw_mem_interconnect()
    self.draw_periph_interconnect()
    self.draw_periph_slaves()
    self.draw_mem_slaves()
    if len(self.connected_slave) != 0:
      self.draw_arbitrator()
      self.draw_remove()

    self.draw_back()
    self.draw_connections(width, height)

    return

  def draw_bus_view(self, width, height):
    self.draw_host_interface()
    self.draw_master()
    self.draw_mem_interconnect()
    self.draw_periph_interconnect()
    self.draw_periph_slaves()
    self.draw_mem_slaves()
    self.draw_connections(width, height)
    self.draw_moving()
    return

  def draw_arbitrator(self):
    b = self.boxes["arbitrator"]
    self.draw_box(b, b.x, b.y, style = BoxStyle.OUTLINE)

  def draw_remove(self):
    b = self.boxes["remove"]
    sm = self.selected_master_node
    if sm.slave_type == SlaveType.PERIPHERAL:
      bm = self.boxes["pslaves"][sm.slave_index]
    else:
      bm = self.boxes["mslaves"][sm.slave_index]
    b.y = bm.y
    self.draw_box(b, b.x, b.y, style = BoxStyle.OUTLINE)

  def draw_back(self):
    b = self.boxes["back"]
    self.draw_box(b, b.x, b.y, style = BoxStyle.OUTLINE)
    # Draw the arrow
    cr = self.cr
    cr.set_line_cap(cairo.LINE_CAP_ROUND)

    cr.set_line_width(5.0)
    cr.set_source_rgb(0.0, 0.0, 0.0)
    cr.move_to (b.x, b.y + b.height / 2.0)
    cr.line_to (b.x - b.width, b.y + b.height / 2.0)
    cr.line_to (b.x - b.width / 2.0, b.y)
    cr.move_to (b.x - b.width,b.y +  b.height / 2.0)
    cr.line_to (b.x - b.width / 2.0, b.y + b.height)
    cr.set_line_cap(cairo.LINE_CAP_BUTT)
    cr.set_line_width(2.0)
    cr.stroke

  def draw_host_interface(self):
    cr = self.cr
    b = self.boxes["host_interface"]

    self.draw_box(b, b.x, b.y, style = BoxStyle.OUTLINE)

  def draw_master(self):
    cr = self.cr
    b = self.boxes["master"]
    self.draw_box(b, b.x, b.y, style = BoxStyle.OUTLINE)


  def draw_mem_interconnect(self):
    cr = self.cr
    b = self.boxes["mic"]
    self.draw_box(b, b.x, b.y, style = BoxStyle.OUTLINE)

  def draw_periph_interconnect(self):
    cr = self.cr
    b = self.boxes["pic"]
    self.draw_box(b, b.x, b.y, style = BoxStyle.OUTLINE)


  def draw_periph_slaves(self):
    for i in xrange(len(self.boxes["pslaves"])):
      # If there is a box moving don't draw it here.
      if self.moving and not (self.selected_node is None):
        if self.selected_node.slave_type == SlaveType.PERIPHERAL\
          and self.selected_node.slave_index == i:
          continue

      name = self.sgm.get_slave_name_at(i, SlaveType.PERIPHERAL)
      p = self.sgm.get_node(name)
      b = self.boxes["pslaves"][i]
      self.draw_box(b, b.x, b.y, style = BoxStyle.OUTLINE)


  def draw_mem_slaves(self):
    for i in range (0, len(self.boxes["mslaves"])):
      # If there is a box moving don't draw it here.
      if self.moving and not (self.selected_node is None):
        if self.selected_node.slave_type == SlaveType.MEMORY \
          and self.selected_node.slave_index == i:
          continue
      name = self.sgm.get_slave_name_at(i, SlaveType.MEMORY)
      p = self.sgm.get_node(name)
      b = self.boxes["mslaves"][i]

      self.draw_box(b, b.x, b.y, style = BoxStyle.OUTLINE)

  def draw_moving(self):
    if self.moving == 0:
      return

    node = None
    b = None

    # Draw trash can.
    b = self.boxes["trash"]

    self.draw_box(b, b.x, b.y, style = BoxStyle.OUTLINE)

    # Draw node.
    node = self.selected_node
    if node.slave_type == SlaveType.PERIPHERAL:
      b = self.boxes["pslaves"][node.slave_index]
    else:
      b = self.boxes["mslaves"][node.slave_index]

    self.mov_x = self.p_x - self.rel_x
    self.mov_y = self.p_y - self.rel_y

    self.draw_box(b, self.mov_x, self.mov_y, style = BoxStyle.OUTLINE)

  def draw_box(self, box, x, y, style = BoxStyle.OUTLINE):
#    x,y = box.x,box.y
    width,height = box.width,box.height
    text = box.name
    r,g,b = box.r,box.g,box.b

    cr = self.cr
    cr.set_source_rgb(r, g, b)
    cr.rectangle(x, y, width, height)
    cr.fill()
    if style == BoxStyle.OUTLINE:
      # How do I draw a box with an outline?
      cr.set_line_width(2.0)
      cr.rectangle(x, y, width, height)
      cr.set_source_rgb(0.0, 0.0, 0.0)
      cr.stroke()

    if len(text) > 0:
      cr.set_source_rgb(0.0, 0.0, 0.0)
#      cr.select_font_face("Georgia", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
      cr.set_font_size(10)
      x_bearing, y_bearing, twidth, theight = cr.text_extents(text)[:4]
      text_x = 0.5 - twidth / 2 - x_bearing
      text_y = 0.5 - theight / 2 - y_bearing

      pos_x = x + (width / 2.0) + text_x
      pos_y = y + (height / 2.0) + text_y

#      print "text x: " + str(text_x)
#      print "text y: " + str(text_y)

      cr.move_to(pos_x, pos_y)
      cr.show_text(text)

      if self.moving:
        return

    # If there are any icons draw them.
    if box.arb_slave:
      # Create a white box.
#      print "draw an the arbitrator slave"
      cr.set_source_rgb(1.0, 1.0, 1.0)
      cr.rectangle(x, y, box.arb_slave_width, height)
      cr.fill()
      cr.set_line_width(2.0)
      cr.set_source_rgb(0.0, 0.0, 0.0)
      cr.rectangle(x, y, box.arb_slave_width, height)
      cr.stroke()
      cr.set_source_rgb(0.0, 0.0, 0.0)
      cr.set_font_size(10)
      x_bearing, y_bearing, twidth, theight = cr.text_extents("AS")[:4]
      text_x = 0.5 - twidth / 2 - x_bearing
      text_y = 0.5 - theight / 2 - y_bearing

      pos_x = x + (box.arb_slave_width / 2.0) + text_x
      pos_y = y + (height / 2.0) + text_y
      cr.move_to(pos_x, pos_y)
      cr.show_text("AS")

    for arb in box.arb_master.keys():
#      print "drawing: " + arb
      icon = box.arb_master[arb]
      if icon.connected:
        cr.set_source_rgb(1.0, 1.0, 1.0)
      else:
        cr.set_source_rgb(0.0, 0.0, 0.0)

      cr.rectangle(icon.x, icon.y, icon.width, icon.height)
      cr.fill()

      if icon.connected:
        cr.set_source_rgb(0.0, 0.0, 0.0)
      else:
        cr.set_source_rgb(1.0, 1.0, 1.0)

      cr.set_font_size(10)
      x_bearing, y_bearing, twidth, theight = cr.text_extents(arb)[:4]
      text_x = 0.5 - twidth / 2 - x_bearing
      text_y = 0.5 - theight / 2 - y_bearing

      pos_x = icon.x + (icon.width / 2.0) + text_x
      pos_y = icon.y + (icon.height / 2.0) + text_y
      cr.move_to(pos_x, pos_y)
      cr.show_text(arb)

    cr.set_source_rgb(0.0, 0.0, 0.0)

    # TODO Check if the box is an arbitrator slave
#      print "text pos (x, y) = %d, %d" % (x + text_x, y + text_y)

  def draw_wb_lines(self, width, height):
    '''Draws the column lines.'''
    cr = self.cr
    column_width = self.get_column_width(width)
    cr.set_line_width(2)
    cr.set_line_cap(cairo.LINE_CAP_SQUARE)
    cr.set_dash([self.dash_size/self.dash_total_size, self.dash_size/self.dash_width], 0)

    for i in xrange(1, 4):
      cr.move_to(column_width * i, 0)
      cr.line_to(column_width * i, height)
    cr.move_to(column_width * 3, height/2)
    cr.line_to(width, height/2)

    # Draw the graph.
    cr.stroke()
    cr.set_dash([], 0)

  def debug_line(self, debug_string):
    cr = self.cr
    cr.set_source_rgb(0, 0, 0)
    cr.move_to(5, self.dy)
    cr.show_text(debug_string)
    self.dy += 10

  def display_debug(self, width, height):
    self.dy = 10
    column_width = self.get_column_width(width)
    self.debug_line("debug")
    self.debug_line("width, height: %d, %d" % (width, height))
    self.debug_line("width, height: %d, %d" % (width, height))
    self.debug_line("column width: " + str(column_width))

    self.debug_line("peripheral slaves: " + str(self.prev_ps_count))
    self.debug_line("memory slaves: " + str(self.prev_ms_count))
    self.debug_line("pointer x: %6d" % self.p_x)
    self.debug_line("pointer y: %6d" % self.p_y)
    self.debug_line("moving: %6d" % self.moving)

    node_name = "None"
    if not (self.selected_node is None):
      node_name = self.selected_node.name

    self.debug_line("selected node: %s" % node_name )
    self.debug_line("new slave: %6d" % self.new_slave)


  def get_column_width(self, screen_width=0.0):
    # Sanity check ...
    if screen_width <= 1:
      return screen_width
    return screen_width / 4.0

  def draw_connections(self, width, height):
    cr = self.cr
    column_width = self.get_column_width(width)

    cr.set_line_width(2)
    cr.set_line_cap(cairo.LINE_CAP_SQUARE)
    cr.set_dash([], 0)

    hi_b = self.boxes["host_interface"]
    m_b = self.boxes["master"]
    pic_b = self.boxes["pic"]
    mic_b = self.boxes["mic"]
    ab = self.boxes["arbitrator"]

    if self.en_arb_view == False:
      # Generate host to master connection.
      cr.move_to (hi_b.x + hi_b.width, hi_b.y + hi_b.height / 2.0)
      cr.line_to (m_b.x, m_b.y + m_b.height/2.0)

      # Master to peripheral interconnect.
      cr.move_to (m_b.x + m_b.width, pic_b.y + pic_b.height / 2.0)
      cr.line_to (pic_b.x, pic_b.y + pic_b.height / 2.0)

      # master to memory interconnect.
      cr.move_to (m_b.x + m_b.width, mic_b.y + mic_b.height / 2.0)
      cr.line_to (mic_b.x, mic_b.y + mic_b.height / 2.0)

    # Peripheral interconnect to peripheral slaves.
    for i in range (0, len(self.boxes["pslaves"])):
      node = self.sgm.get_slave_at(i, SlaveType.PERIPHERAL)
      if self.moving and not (self.selected_node is None):
        if self.selected_node.slave_type == SlaveType.PERIPHERAL\
          and self.selected_node.slave_index == i:
          continue

      b = self.boxes["pslaves"][i]

      if self.en_arb_view:
        arbs = b.get_arb_master_names()
        for arb in arbs:
          if b.is_arb_master_connected(arb):
            s_name = b.get_name_of_connected_slave(arb)
            if self.connected_slave == s_name:
              #make a connection to the arbitrator
              cr.move_to(b.x + b.width, b.y + b.height / 2.0)
              cr.line_to(ab.x + ab.width / 2.0, b.y + b.height / 2.0)
              if (b.y < ab.y):
                cr.line_to(ab.x + ab.width / 2.0, ab.y)
              else:
                cr.line_to(ab.x + ab.width / 2.0, ab.y + b.height)

      cr.move_to(pic_b.x + pic_b.width, \
            (column_width - b.width) / 2.0 + \
            i * ((column_width - b.width) + b.height) + \
            b.height / 2.0)

      # Check if this is a slave for the arbitrator.
      if self.en_arb_view and node.unique_name == self.connected_slave:
        cr.line_to (ab.x, ab.y + ab.height / 2.0)
        cr.move_to (ab.x + ab.width, ab.y + ab.height / 2.0)
        cr.line_to (b.x, b.y + b.height / 2.0)
      else:
        cr.line_to (b.x, b.y + b.height / 2.0)

    # Memory interconnect to memory slaves.
    for i in range (0, len(self.boxes["mslaves"])):
      node = self.sgm.get_slave_at(i, SlaveType.MEMORY)
      if self.moving and not (self.selected_node is None):
        if self.selected_node.slave_type == SlaveType.MEMORY \
          and self.selected_node.slave_index == i:
          continue
      b = self.boxes["mslaves"][i]
      cr.move_to (mic_b.x + mic_b.width, \
            (column_width - b.width) / 2.0 + \
            i * ((column_width - b.width) + b.height) + \
            b.height / 2.0 +\
            height / 2.0)

      # Check if this is a slave for the arbitrator.
      if self.en_arb_view and node.unique_name == self.connected_slave:
        cr.line_to (ab.x, ab.y + ab.height / 2.0)
        cr.move_to (ab.x + ab.width, ab.y + ab.height / 2.0)
        cr.line_to (b.x, b.y + b.height / 2.0)
      else:
        cr.line_to (b.x, b.y + b.height / 2.0)

    cr.stroke()

  def get_selected_name(self, x, y):
    name = ""

    if self.en_arb_view:
      b = self.boxes["back"]
      if b.in_bounding_box(x, y):
        name = "back"

      b = self.boxes["remove"]
      if b.in_bounding_box(x, y):
        name = "remove"
    else:
      # Check host interface.
      b = self.boxes["host_interface"]
      if b.in_bounding_box(x, y):
        # Return the name.
        name = gm.get_unique_name("Host Interface", NodeType.HOST_INTERFACE)

      # Check master.
      b = self.boxes["master"]
      if b.in_bounding_box(x, y):
        name = gm.get_unique_name("Master", NodeType.MASTER)

    # Check memory interconnect.
    b = self.boxes["mic"]
    if b.in_bounding_box(x, y):
      name = gm.get_unique_name("Memory", NodeType.MEMORY_INTERCONNECT)

    # Check peripheral interconnect.
    b = self.boxes["pic"]
    if b.in_bounding_box(x, y):
      name = gm.get_unique_name("Peripherals", NodeType.PERIPHERAL_INTERCONNECT)

    # Check the peripheral slaves.
    for i in range (0, len(self.boxes["pslaves"])):
      pname = self.sgm.get_slave_name_at(i, SlaveType.PERIPHERAL)
      b = self.boxes["pslaves"][i]
      if b.in_bounding_box(x, y):
        name = pname

    # Check the memory slaves.
    for i in range (0, len(self.boxes["mslaves"])):
      mname = self.sgm.get_slave_name_at(i, SlaveType.MEMORY)
      b = self.boxes["mslaves"][i]
      if b.in_bounding_box(x, y):
        name = mname

    return name

  def is_arbitrator_master_selected(self, node_name, x, y):
    # This could be done with just the x and y, but this way reduces a lot of
    # overhead of searching through each node.
    node = self.sgm.get_node(node_name)
    slave_type = node.slave_type
    slave_index = node.slave_index
    if slave_type == SlaveType.PERIPHERAL:
      b = self.boxes["pslaves"][slave_index]
    else:
      b = self.boxes["mslaves"][slave_index]

    if b.in_arb_master_icon(x, y):
      return True

    return False

  def get_arbitrator_master_selected(self, node_name, x, y):
    # This could be done with just the x and y, but this way reduces a lot of
    # overhead of searching through each node.
    node = self.sgm.get_node(node_name)
    slave_type = node.slave_type
    slave_index = node.slave_index
    if slave_type == SlaveType.PERIPHERAL:
      b = self.boxes["pslaves"][slave_index]
    else:
      b = self.boxes["mslaves"][slave_index]

    return b.get_arb_master_name(x, y)


def run(Widget):
  print "in run"
  window = gtk.Window()
  window.set_default_size(640, 430)
  window.connect ("delete-event", gtk.main_quit)
  window.set_size_request(400, 400)
  widget = Widget()
  widget.show()
  window.add(widget)
  window.present()
  gtk.main()


if __name__ == "__main__":
  print "in main"
  run(GraphDrawer)

