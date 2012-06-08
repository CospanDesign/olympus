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


"""Resolves defines from verilog files much like a pre-processor for c

Defines in verilog can be dependent on verilog include file. The ibuilder
script will sometimes need the evaluated values to generate all the files
"""

__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

"""Changes:
  06/07/2012
    -Added Documentation and licsense
"""

import os
import sys
import string
import saperror

def generate_define_table(filestring="", debug = False):
  """Reads in a module as a buffer and returns a dictionary of defines

  Main work horse of the preprocessor this will find all the defines in a 
  given module. If all the defines cannot be evaluated directly by the
  current module then this will search all the included modules to determine
  evaluate 

  Args:
    filestring: A buffer from the module's file

  Returns:
    A dictionary of defines

  Raises:
    PreProcessorError 
  """
  import saputils
  define_dict = {}
  #from a file string find all the defines and generate an entry into a dictionary
  filestring = saputils.remove_comments(filestring)
  str_list = filestring.splitlines()

  for item in str_list:
    item = item.strip()
    #look for include files
    if item.startswith("`include"):
      if debug:
        print "found an include: " + item
      #read int the include file, strip away the comments
      #then append everything to the end
      item = item.partition("`include")[2]
      item = item.strip()
      item = item.strip("\"")
      inc_file = saputils.find_rtl_file_location(item)
      if debug:
        print "include file location: " + inc_file

      #try and open the include file
      try:
        ifile = open(inc_file)
        fs = ifile.read()
        ifile.close()
      except:
        if item != "project_defines.v":
          raise PreProcessor("Error while attempting to the include file: %s" % inc_file)

      try:
        if debug:
          print "got the new file string"
        include_defines = generate_define_table(fs)
        if debug:
          print "after include_define"
          print "length of include defines: " + str(len(include_defines.keys()))
        for key in include_defines.keys():
          #append the values found in the include back in the local dictionary
          if debug:
            print "working on: " + key
          if (not define_dict.has_key(key)):
            define_dict[key] = include_defines[key]


        if debug:
          print "added new items onto the list"
#      except TypeError as terr:
#        print "Type Error: " + str(terr)
      except:
        if item != "project_defines.v":
          raise PreProcessorError("Error while processing: %s: %s" %(item, sys.exc_info()[0]))
          #print "error while processing : ", item, ": ",  sys.exc_info()[0]
      continue

    if item.startswith("`define"):
      #if the string starts with `define split the name and value into the dictionary
#      if debug:
#        print "found a define: " + item
      item = item.partition("`define")[2]
      item = item.strip()
      if (len(item.partition(" ")[2]) > 0):
        name = item.partition(" ")[0].strip()
        value = item.partition(" ")[2].strip()
        if debug:
          print "added " + name + "\n\tWith value: " + value
        define_dict[name] = value
        continue
      if (len(item.partition("\t")[2]) > 0):
        name = item.partition("\t")[0].strip()
        value = item.partition("\t")[2].strip()
        if debug:
          print "added " + name + "\n\tWith value: " + value
        define_dict[name] = value
        continue
      if debug:
        print "found a define without a value: " + item

  return define_dict


def resolve_defines(work_string="", define_dict={}, debug = False):
  """given a string with a define change it into what it is supposed to be defining"""
  #loop through the string until all the defines are resolved
  #there could be nested defines so the string might go through the same loop
  #a few times
  if debug:
    print "starting string: " + work_string
  work_string = work_string.strip()
  #while there is still a tick mark in the string
  while (work_string.__contains__("`")):
    if debug:
      print "found debug marker"
    #look through the filedict
    #only need to look after the ` portion
    def_string = work_string.partition("`")[2]
    #if there are any white spaces in the line we only want the first one
    def_string = def_string.split()[0]
  #  if (len(def_string.split()) > 0)
  #    def_string = def_string.split()[0]

    if debug:
      print "found the first occurance of a define: " + def_string
    #now I'm working with only the definition and any characters afterwards
    #attempt to match up this entire string to one wihtin the keys
    def_len = len(def_string)
    while ( (def_len > 0) and (not define_dict.keys().__contains__(def_string[0: def_len]))):
      if debug:
        print "def_string: " + def_string[0:def_len]
      #didn't find the string yet
      def_len = def_len - 1
    #check to see if the item found is unique
    #actually the solution must be unique because dictionaries cannot multiple keys with the same name
    if (def_len > 0):
      key = def_string[0:def_len]
      value = str(define_dict[key])
      if debug:
        print "found define! " + key
        print "replacement value: " + value
      work_string = work_string.replace("`" + key, value, 1)
      if debug:
        print "final string: " + work_string

    else:
      if debug:
        print "Error in resolve_define(): didn't find define status in " + work_string
      return ""


  return work_string


def evaluate_range(in_string = "", define_dict = {}, debug = False):
  """resolve an entire string, use this for the first item in the pre-processor, and for paranthesis"""

  #resolve all the defines
  #work_string = resolve_defines(in_string, define_dict)
  if ("[" in in_string):
    pre = str(eval(in_string[in_string.index("[") + 1: in_string.index(":")]))
    if debug:
      print "pre: " + pre
    post = str(eval(in_string[in_string.index(":") + 1: in_string.index("]")]))
    if debug:
      print "post: " + post
    in_string = in_string[:in_string.index("[") + 1] + pre + ":" + post + in_string[in_string.index("]")]

  if debug:
    print in_string
  return in_string

#  work_string = eval(in_string)
#  print work_string
#  return str(work_string)


#  #get rid of all paranthsis
#  while ("(" in work_string):
#    #recursively call this function to get rid of all paranthesis
#    start = work_string.index("(")
#    end = work_string.index(")")
#    if debug:
#      print "first parenthesis: " + work_string[start + 1: end]
#    np_string = resolve_string(work_string[start + 1:end], define_dict)
#    if debug:
#      print "np string: " + np_string
#    work_string = work_string[0:start] + " " + np_string + " " + work_string[end + 1:-1]
#    if debug:
#      print "final string: " + work_string
#
#  #get rid of any white spaces
#  work_string = work_string.strip()
#  #look for * and \
#  while ("*" in work_string):
#    if debug:
#      print "found *"
#    op_index = work_string.index("*")
#    if debug:
#      print "index of *: " + str(op_index)
#    #there is a multiplication
#    pre = work_string.partition("*")[0]
#    post = work_string.partition("*")[2]
#    if debug:
#      print "pre: " + pre
#      print "post: " + post
#
#    pre = pre.strip()
#    pre_index = len(pre) - 1
#    post = post.strip()
#    post_index = 0
#    #find the beginning of the the operand
#    while (pre_index > 0):
#      #find the non point where there is no more number
#      if (not pre[pre_index].isnumber()):
#        break
#      pre_index = pre_index - 1
#      pre = pre[pre_index:].strip()
#
#
#    while (post_index < len(post) - 1):
#      #find the point where the post is not a number
#      if (not post[post_index].isnumber()):
#        break
#      post_index = post_index + 1
#      post = post[:post_index].strip()
#
#    if debug:
#      print "pre operand: (" + pre + ")"
#      print "post operand: (" + post + ")"
#
#    pre_val = string.atoi(pre)
#    post_val = string.atoi(post)
#
#    val = pre_val * post_val
#
#
#  #look for + and -
#
#  return work_string


def calulate_operator(pre, operator, post):

  work_string = ""


  return work_string

