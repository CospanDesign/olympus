#! /usr/bin/env python

import subprocess
import os
import select
import fcntl


class BuildController(object):
  '''Meant to manage building a project in a sub-process.'''
  def __init__(self):
    '''Inits the build controller.'''
    self.sub = None

  def run(self, command):
    """Generates the project in a separate process."""
#    self.sub = subprocess.Popen(["bash", "/home/cospan/Projects/python/subprocess/demo.sh"],
#    self.sub = subprocess.Popen(["ls", "-l"],
    args = ["bash", command]
    self.sub = subprocess.Popen(args,
                  stdout = subprocess.PIPE,
                  stderr = subprocess.STDOUT)

    flags = fcntl.fcntl(self.sub.stdout, fcntl.F_GETFL)
    fcntl.fcntl(self.sub.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    data = self.read()
    if data is not None:
      print "data is not None"
      print data

  def read(self):
    '''Reads the data from the completed subprocess.'''
    try:
      return self.sub.stdout.readline()
    except:
      return None

  def kill_child(self):
    '''Kills project generation.'''
    print "kill child"
    self.sub.kill()

  def is_running(self):
    '''Determine whether this is currently generating the project files.'''
    if self.sub is None:
      print "sub == None"
      return False
    if os.path.exists("/proc/" + str(self.sub.pid)):
      procfile = open("/proc/%d/stat" % self.sub.pid)
      status = procfile.readline().split(' ')[2]
      procfile.close()
      if status == 'Z':
        print "Zombie!"  # Kill it with FIRE!
        return False
      return True

    print "process file not found"
    return False

if __name__ == "__main__":
  '''Tests this class.'''
  print "starting"
  p = BuildController()
  p.run("tests/demo.sh")
  print "child process created"
  while p.is_running():
#    data = p.sub.stdout.readlines()
    data = p.read()
    if data is None:
      continue
    print data,

  print "finished"


