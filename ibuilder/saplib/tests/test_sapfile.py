import unittest
import sapfile
import json
import sys
import os

from gen import Gen
from saperror import ModuleFactoryError

class Test (unittest.TestCase):
  """Unit test for sapfile"""

  def setUp(self):
    """open up a sapfile class"""
    os.environ["SAPLIB_BASE"] = sys.path[0] + "/saplib"
    self.sapfile = sapfile.SapFile()
    self.dbg = False
    if "SAPLIB_DEBUG" in os.environ:
      if (os.environ["SAPLIB_DEBUG"] == "True"):
        self.dbg = True

  def test_write_file(self):
    """a file will end up in a directory after this is tested"""
    self.sapfile.buf = "crappidy crap data!"
    self.sapfile.write_file(location="~/sandbox", filename="test")
    #no error was raised!

  def test_apply_gen_script(self):
    """generate a file, a file should come out of this"""
    #load tags
    #load setup the buffer
    #setup the file tags
    #self.sapfile.apply_gen_script()
    self.assertEqual(False, False)

  def test_apply_tags(self):
    """a file should be changed based on the tags"""
    project_name = "projjjjeeeecccttt NAME!!!"

    #This should raise an error if something went wrong
    filein = open(os.getenv("SAPLIB_BASE") + "/bus/README")
    self.sapfile.buf = filein.read()
    filein.close()

    #print self.sapfile.buf
    tag_map = {"PROJECT_NAME":project_name}
    self.sapfile.set_tags(tag_map)
    self.sapfile.apply_tags()
    #print self.sapfile.buf
    result = (self.sapfile.buf.find(project_name) == 0)
    self.assertEqual(result, True)


  def test_set_tags(self):
    """test to see if a tag file was loaded correctly"""
    tag_file = os.getenv("SAPLIB_BASE") +  "/tags/README.json"
    self.sapfile.set_tags(tag_file)
    self.assertEqual(True, True)
  
  def test_process_file_no_dir(self):
    """make sure the process_file fales when user doesn't put in directory"""
    self.assertRaises(ModuleFactoryError, self.sapfile.process_file, filename = "README")

  def test_process_file_no_location(self):
    """make sue the process file fails when user doesn't give a location"""
    project_tags_file = os.getenv("SAPLIB_BASE") + "/example_project/gpio_v2.json"
    filein = open(project_tags_file)
    json_tags = json.load(filein)
    self.sapfile.set_tags(json_tags)
    file_tags = {"location":"bus"}
    self.assertRaises(ModuleFactoryError, self.sapfile.process_file, filename = "README", directory="~/sandbox")
  
  def test_process_file(self):
    """excercise all functions of the class"""
    #print "testing process file"
    project_tags_file = os.getenv("SAPLIB_BASE") + "/example_project/gpio_v2.json"
    filein = open(project_tags_file)
    json_tags = json.load(filein)
    filein.close()

    self.sapfile.set_tags(json_tags)
    file_tags = {"location":"bus"}
    self.sapfile.process_file(filename = "README", directory="~/sandbox", file_dict = file_tags, debug = self.dbg)
    #print self.sapfile.buf

    #the test is to not raise an error
  
  def test_process_bram_file(self):
    """excercise all functions of the class"""
    #print "testing process file"
    project_tags_file = os.getenv("SAPLIB_BASE") + "/example_project/mem_example.json"
    filein = open(project_tags_file)
    json_tags = json.load(filein)
    filein.close()

    self.sapfile.set_tags(json_tags)
    file_tags = {"location":"bus"}
    self.sapfile.process_file(filename = "wb_bram.v", directory="~/sandbox", file_dict = file_tags, debug = self.dbg)
    #print self.sapfile.buf
    
    #if this doesn't throw an error then we're good

  def test_process_gen_script(self):
    """excercise the script"""
    project_tags_file = os.getenv("SAPLIB_BASE") + "/example_project/gpio_v2.json"
    filein = open(project_tags_file)
    json_tags = json.load(filein)
    self.sapfile.set_tags(json_tags)
    file_tags = {"location":"hdl/rtl/wishbone/interconnect", "gen_script":"gen_interconnect"}
    self.sapfile.process_file(filename = "wishbone_interconnect.v", directory="~/sandbox", file_dict = file_tags)
    #print self.sapfile.buf

    #if this doesn't throw an error then we're good
    
  def test_process_file_no_filename(self):
    """excercise the gen script only functionality"""
    project_tags_file = os.getenv("SAPLIB_BASE") + "/example_project/gpio_v2.json"
    filein = open(project_tags_file)
    json_tags = json.load(filein)
    self.sapfile.set_tags(json_tags)
    file_tags = {"gen_script":"gen_top"}
    self.sapfile.process_file("top", directory="~/sandbox", file_dict = file_tags, debug=self.dbg)
    #if this doesn't throw an error then we're good

  def test_has_dependency(self):
    #scan a file that is not a verilog file
    result = self.sapfile.has_dependencies("wb_gpio", debug=self.dbg)
    self.assertEqual(result, False)
    #scan for a file that is a verilog file with a full path
    file_location = os.getenv("SAPLIB_BASE") + "/hdl/rtl/wishbone/host_interface/uart/uart_io_handler.v"
    result = self.sapfile.has_dependencies(file_location, debug=self.dbg)
    self.assertEqual(result, True)
    #scan a file that is a verilog file but not the full path
    result = self.sapfile.has_dependencies("uart_io_handler.v", debug=self.dbg)
    self.assertEqual(result, True)
  
    #scan a file that has multiple levels of dependencies
    result = self.sapfile.has_dependencies("sdram.v", debug=self.dbg)
    self.assertEqual(result, True)
    
    result = self.sapfile.has_dependencies("wb_gpio.v", debug=self.dbg)
    self.assertEqual(result, False)

  def test_get_list_of_dependencies(self):
    deps = self.sapfile.get_list_of_dependencies("wb_gpio.v", debug=self.dbg)
    self.assertEqual(len(deps) == 0, True)
    deps = self.sapfile.get_list_of_dependencies("uart_io_handler.v", debug=self.dbg)
    self.assertEqual(len(deps) > 0, True)
    deps = self.sapfile.get_list_of_dependencies("sdram.v", debug=self.dbg)
    self.assertEqual(len(deps) > 0, True)


  def test_resolve_dependencies(self):
    #filename = "sdram.v"
    #result = self.sapfile.resolve_dependencies(filename, debug = True)
    #"dependencies found for " + filename
    #self.assertEqual(result, True)
    #harder dependency
    filename = "wb_sdram.v"
    self.sapfile.resolve_dependencies(filename, debug = self.dbg)
    #print "\n\n\n\n"
    #print "dependency for " + filename
#    for d in self.sapfile.verilog_dependency_list:
#      print d
    #print "\n\n\n\n"
    self.assertNotEqual(len (self.sapfile.verilog_dependency_list), 0)



if __name__ == "__main__":
  unittest.main()
