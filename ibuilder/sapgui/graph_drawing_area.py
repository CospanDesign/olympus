import gtk, gobject, cairo
from gtk import gdk
import math
from types import *

class GraphDrawingArea(gtk.DrawingArea):
  """Custom Drawing Area"""
  def __init__(self):
    '''Inits the graph drawing area by connecting the expose event correctly.'''
    super(GraphDrawingArea, self).__init__()

    self.connect("expose_event", self.do_expose_event)
    gobject.timeout_add(50, self.tick)

  def tick(self):
    if self.window is None:
      return True

    alloc = self.get_allocation()
    if alloc.width < 0 or alloc.height < 0:
      return True

    rect = gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
    self.window.invalidate_rect(rect, True)

    return True # Causes timeout to tick again


  def do_expose_event(self, widget, event):
    '''Draws the graph area?'''
#    print "expose event"
    self.cr = self.window.cairo_create()
    self.draw(*self.window.get_size())

if __name__ == '__main__':
  # TODO some test of some sort
  print 'No test yet written!'
