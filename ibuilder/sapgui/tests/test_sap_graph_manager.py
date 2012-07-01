import unittest
import os
import sys
import json
import mock

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'saplib'))

import sapfile
import saputils
import sap_graph_manager as gm
from sap_graph_manager import NoSuchNodeError, NodeType, SlaveType, SlaveError, NodeError

class UTest(unittest.TestCase):
  def setUp(self):
    # Data found in saplib/example_project/gpio_example.json
    self.project_tags = {
      "BASE_DIR": "~/projects/sycamore_projects",
      "board": "xilinx-s3esk",
      "PROJECT_NAME": "example_project",
      "TEMPLATE": "wishbone_template.json",
      "INTERFACE": {
        "filename": "uart_io_handler.v",
        "bind": {
          "phy_uart_in": {
            "port": "RX",
            "direction": "input"
          },
          "phy_uart_out": {
            "port": "TX",
            "direction": "output"
          }
        }
      },
      "SLAVES": {
        "gpio1": {
          "filename":"wb_gpio.v",
          "bind": {
            "gpio_out[7:0]": {
              "port":"led[7:0]",
              "direction":"output"
            },
            "gpio_in[3:0]": {
              "port":"switch[3:0]",
              "direction":"input"
            }
          }
        }
      },
      "bind": {},
      "constraint_files": []
    }
    self.sgm = gm.SapGraphManager()
    self.sgm.graph = mock.Mock()

  def test_add_node_master_memory(self):
    arg_n, arg_nt, arg_st = 'name', NodeType.MASTER, SlaveType.MEMORY

    self.sgm.get_number_of_memory_slaves = mock.Mock(return_value=0)
    self.sgm.get_number_of_peripheral_slaves = mock.Mock(
        side_effect=AssertionError('get_number_of_peripheral_slaves called'))
    self.sgm.get_unique_name = mock.Mock(return_value='uname')

    class Helper:
      name = None
    def mock_add_node(x):
      if Helper.name != None:
        self.fail('add_node called 2x')
      Helper.name = x
    self.sgm.graph.add_node = mock_add_node
    self.sgm.graph.node = {}

    # Run & Test
    self.assertEqual('uname', self.sgm.add_node(arg_n, arg_nt, arg_st))
    self.assertIn('uname', self.sgm.graph.node)
    self.assertEqual(self.sgm.graph.node['uname'].name, arg_n)
    self.assertEqual(self.sgm.graph.node['uname'].node_type, arg_nt)
    self.assertEqual(self.sgm.graph.node['uname'].slave_type, arg_st)
    self.assertEqual(self.sgm.graph.node['uname'].slave_index, 0)
    self.assertEqual(self.sgm.graph.node['uname'].unique_name, 'uname')

  def test_add_node_master_peripheral(self):
    arg_n, arg_nt, arg_st = 'name', NodeType.MASTER, SlaveType.PERIPHERAL

    self.sgm.get_number_of_peripheral_slaves = mock.Mock(return_value=0)
    self.sgm.get_number_of_memory_slaves = mock.Mock(
        side_effect=AssertionError('get_number_of_memory_slaves called'))
    self.sgm.get_unique_name = mock.Mock(return_value='uname')

    class Helper:
      name = None
    def mock_add_node(x):
      if Helper.name != None:
        self.fail('add_node called 2x')
      Helper.name = x
    self.sgm.graph.add_node = mock_add_node
    self.sgm.graph.node = {}

    # Run & Test
    self.assertEqual('uname', self.sgm.add_node(arg_n, arg_nt, arg_st))
    self.assertIn('uname', self.sgm.graph.node)
    self.assertEqual(self.sgm.graph.node['uname'].name, arg_n)
    self.assertEqual(self.sgm.graph.node['uname'].node_type, arg_nt)
    self.assertEqual(self.sgm.graph.node['uname'].slave_type, arg_st)
    self.assertEqual(self.sgm.graph.node['uname'].slave_index, 0)
    self.assertEqual(self.sgm.graph.node['uname'].unique_name, 'uname')

  def test_add_node_bad_SlaveType_raises_TypeError(self):
    arg_n, arg_nt, arg_st = 'name', NodeType.MASTER, 'foo'

    self.sgm.get_number_of_peripheral_slaves = mock.Mock(
        side_effect=AssertionError('get_number_of_peripheral_slaves called'))
    self.sgm.get_number_of_memory_slaves = mock.Mock(
        side_effect=AssertionError('get_number_of_memory_slaves called'))
    self.sgm.get_unique_name = mock.Mock(
        side_effect=AssertionError('get_unique_name called'))
    self.sgm.graph.add_node = mock.Mock(
        side_effect=AssertionError('graph.add_node called'))

    self.assertRaises(TypeError, self.sgm.add_node, arg_n, arg_nt, arg_st)

  def test_add_node_bad_NodeType_raises_TypeError(self):
    arg_n, arg_nt, arg_st = 'name', 'flah g-nah nah', SlaveType.MEMORY

    self.sgm.get_number_of_peripheral_slaves = mock.Mock(
        side_effect=AssertionError('get_number_of_peripheral_slaves called'))
    self.sgm.get_number_of_memory_slaves = mock.Mock(
        side_effect=AssertionError('get_number_of_memory_slaves called'))
    self.sgm.get_unique_name = mock.Mock(
        side_effect=AssertionError('get_unique_name called'))
    self.sgm.graph.add_node = mock.Mock(
        side_effect=AssertionError('graph.add_node called'))

    self.assertRaises(TypeError, self.sgm.add_node, arg_n, arg_nt, arg_st)

  def test_bind_port(self):
    arg_n, arg_po, arg_pi = 'name', '1234', 3

    # Build mock node.
    mock_node = mock.Mock()
    mock_node.parameters = {
      'ports' : {
        arg_po : {
          'direction' : 'out'
        }
      }
    }
    mock_node.bindings = {}

    # Set up SGM.
    self.sgm.get_node = mock.Mock(return_value=mock_node)

    # Run & Test
    self.sgm.bind_port(arg_n, arg_po, arg_pi)
    self.assertIn(arg_po, mock_node.bindings)
    self.assertEquals(arg_pi, mock_node.bindings[arg_po]['pin'])
    self.assertEquals('out', mock_node.bindings[arg_po]['direction'])

  def test_bind_port_raises_NoSuchNodeError(self):
    arg_n, arg_po, arg_pi = 'name', '1234', 3

    # Set up SGM.
    self.sgm.get_node = mock.Mock(return_value=None)

    # Run & Test
    self.assertRaises(NoSuchNodeError, self.sgm.bind_port, arg_n, arg_po, arg_pi)

  def test_clear_graph(self):
    pass

  def test_connect_nodes(self):
    pass

  def test_disconnect_nodes(self):
    pass

  def test_fix_slave_indexes(self):
    pass

  def test_get_connected_slaves(self):
    pass

  def test_get_edge_name(self):
    pass

  def test_get_host_interface_node(self):
    pass

  def test_get_node(self):
    pass

  def test_get_node_bindings(self):
    pass

  def test_get_node_names(self):
    pass

  def test_get_nodes_dict(self):
    pass

  def test_get_number_of_connections(self):
    pass

  def test_get_number_of_memory_slaves(self):
    pass

  def test_get_number_of_peripheral_slaves(self):
    pass

  def test_get_number_of_slaves(self):
    pass

  def test_get_parameters(self):
    pass

  def test_get_size(self):
    pass

  def test_get_slave_at(self):
    pass

  def test_get_slave_name_at(self):
    pass

  def test_is_slave_connected_to_slave(self):
    pass

  def test_move_memory_slave(self):
    pass

  def test_move_peripheral_slave(self):
    pass

  def test_move_slave(self):
    pass

  def test_remove_node(self):
    pass

  def test_remove_slave(self):
    pass

  def test_rename_slave(self):
    pass

  def test_set_config_bindings(self):
    pass

  def test_set_edge_name(self):
    pass

  def test_set_parameters(self):
    pass

  def test_unbind_port(self):
    pass



class IntTest(unittest.TestCase):
  """Unit test for gen_drt.py"""

  def setUp(self):
    self.dbg = False
    self.vbs = False
    if "SAPLIB_VERBOSE" in os.environ:
      if (os.environ["SAPLIB_VERBOSE"] == "True"):
        self.vbs = True

    if "SAPLIB_DEBUG" in os.environ:
      if (os.environ["SAPLIB_DEBUG"] == "True"):
        self.dbg = True

    # Open up the specified JSON project config file and copy it into a buffer.
    file_name = os.getenv("SAPLIB_BASE") + "/example_project/gpio_example.json"
    filein = open(file_name)
    json_string = filein.read()
    filein.close()

    self.project_tags = json.loads(json_string)

    if self.dbg:
      print "loaded JSON file"

    # Generate graph.
    self.sgm = gm.SapGraphManager()

    return

  def test_graph_add_node(self):
    if self.dbg:
      print "generating host interface node"

    self.sgm.add_node("uart", gm.NodeType.HOST_INTERFACE)

    # Get the size of the graph
    size = self.sgm.get_size()
    if self.dbg:
      print "number of nodes: " + str(size)

    self.assertEqual(size, 1)


  def test_rename_slave(self):
    if self.dbg:
      print "renaming slave"
    self.sgm.add_node ("name1", gm.NodeType.SLAVE, gm.SlaveType.PERIPHERAL, 0)
    self.sgm.rename_slave(gm.SlaveType.PERIPHERAL, 0, "name2")
    name = self.sgm.get_slave_name_at(0, gm.SlaveType.PERIPHERAL)
    node = self.sgm.get_node(name)
    name = node.name
    self.assertEqual(name, "name2")

  def test_get_number_of_peripheral_slaves(self):
    self.sgm.add_node("slave_1",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_2",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    count = self.sgm.get_number_of_slaves(gm.SlaveType.PERIPHERAL)
    self.assertEqual(count, 2)

  def test_get_number_of_memory_slaves(self):
    self.sgm.add_node("slave_1",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.MEMORY,
                      debug = self.dbg)
    self.sgm.add_node("slave_2",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.MEMORY,
                      debug = self.dbg)
    count = self.sgm.get_number_of_slaves(gm.SlaveType.MEMORY)

    self.assertEqual(True, True)

  def test_slave_index(self):
    self.sgm.add_node("slave_1",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_2",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_3",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_4",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_5",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)

    # Scramble things up.
    self.sgm.move_slave(3, 1, gm.SlaveType.PERIPHERAL)
    self.sgm.move_slave(2, 4, gm.SlaveType.PERIPHERAL)
    self.sgm.move_slave(2, 3, gm.SlaveType.PERIPHERAL)
    self.sgm.move_slave(1, 4, gm.SlaveType.PERIPHERAL)
    self.sgm.move_slave(4, 2, gm.SlaveType.PERIPHERAL)

    self.sgm.remove_slave(1, gm.SlaveType.PERIPHERAL)

    count = self.sgm.get_number_of_slaves(gm.SlaveType.PERIPHERAL)

    for i in xrange(count):
      slave_name = self.sgm.get_slave_name_at(i, gm.SlaveType.PERIPHERAL)
      node = self.sgm.get_node(slave_name)
      self.assertEqual(i, node.slave_index)

    # Test memory locations.
    self.sgm.add_node("mem_1",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.MEMORY,
                      debug = self.dbg)
    self.sgm.add_node("mem_2",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.MEMORY,
                      debug = self.dbg)
    self.sgm.add_node("mem_3",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.MEMORY,
                      debug = self.dbg)
    self.sgm.add_node("mem_4",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.MEMORY,
                      debug = self.dbg)

    # Scramble things up.
    self.sgm.move_slave(0, 1, gm.SlaveType.MEMORY)
    self.sgm.move_slave(3, 1, gm.SlaveType.MEMORY)
    self.sgm.move_slave(2, 0, gm.SlaveType.MEMORY)
    self.sgm.move_slave(0, 3, gm.SlaveType.MEMORY)

    self.sgm.remove_slave(2, gm.SlaveType.MEMORY)

    count = self.sgm.get_number_of_slaves(gm.SlaveType.MEMORY)

    for i in range (0, count):
      slave_name = self.sgm.get_slave_name_at(i, gm.SlaveType.MEMORY)
      node = self.sgm.get_node(slave_name)
      self.assertEqual(i, node.slave_index)

  def test_clear_graph(self):
    if self.dbg:
      print "generating host interface node"

    self.sgm.add_node("uart", gm.NodeType.host_interface)
    # Get the size of the graph.
    size = self.sgm.get_size()
    if self.dbg:
      print "number of nodes: " + str(size)

    self.sgm.clear_graph()

    size = self.sgm.get_size()
    self.assertEqual(size, 0)

  def test_graph_add_slave_node(self):
    if self.dbg:
      print "generating host interface node"

    self.sgm.add_node("gpio",
                      gm.NodeType.SLAVE,
                      gm.SlaveType.PERIPHERAL,
                      debug=self.dbg)

    gpio_name = gm.get_unique_name("gpio",
                                   gm.NodeType.SLAVE,
                                   gm.SlaveType.PERIPHERAL,
                                   slave_index = 1)

    if self.dbg:
      print "unique name: " + gpio_name

    # Get the size of the graph.
    size = self.sgm.get_size()
    if self.dbg:
      print "number of nodes: " + str(size)

    self.assertEqual(size, 1)

  def test_graph_remove_node(self):
    if self.dbg:
      print "adding two nodes"
    self.sgm.add_node("uart", gm.NodeType.host_interface)
    self.sgm.add_node("master", gm.NodeType.master)

    size = self.sgm.get_size()
    if self.dbg:
      print "number of nodes: " + str(size)

    self.assertEqual(size, 2)

    # Remove the uart node.
    unique_name = gm.get_unique_name("uart", gm.NodeType.host_interface)

    self.sgm.remove_node(unique_name)

    size = self.sgm.get_size()
    if self.dbg:
      print "number of nodes: " + str(size)

    self.assertEqual(size, 1)

  def test_get_node_names(self):
    if self.dbg:
      print "adding two nodes"

    self.sgm.add_node("uart", gm.NodeType.HOST_INTERFACE)
    self.sgm.add_node("master", gm.NodeType.MASTER)

    names = self.sgm.get_node_names()


    uart_name = gm.get_unique_name("uart", gm.NodeType.HOST_INTERFACE)
    master_name = gm.get_unique_name("master", gm.NodeType.MASTER)

    self.assertIn(uart_name, names)
    self.assertIn(master_name, names)

  def test_get_nodes(self):
    if self.dbg:
      print "adding two nodes"

    self.sgm.add_node("uart", gm.NodeType.HOST_INTERFACE)
    self.sgm.add_node("master", gm.NodeType.MASTER)

    graph_dict = self.sgm.get_nodes_dict()


    uart_name = gm.get_unique_name("uart", gm.NodeType.HOST_INTERFACE)
    master_name = gm.get_unique_name("master", gm.NodeType.MASTER)

    if self.dbg:
      print "dictionary: " + str(graph_dict)

    self.assertIn(uart_name, graph_dict)
    self.assertIn(master_name, graph_dict)


  def test_get_host_interface(self):
    self.sgm.add_node("uart", gm.NodeType.HOST_INTERFACE)
    self.sgm.add_node("master", gm.NodeType.MASTER)
    node = self.sgm.get_host_interface_node()
    self.assertEqual(node.name, "uart")


  def test_connect_nodes(self):
    if self.dbg:
      print "adding two nodes"

    self.sgm.add_node("uart", gm.NodeType.HOST_INTERFACE)
    self.sgm.add_node("master", gm.NodeType.MASTER)



    uart_name = gm.get_unique_name("uart", gm.NodeType.HOST_INTERFACE)
    master_name = gm.get_unique_name("master", gm.NodeType.MASTER)

    # Get the number of connections before adding a connection.
    num_of_connections = self.sgm.get_number_of_connections()
    self.assertEqual(num_of_connections, 0)

    self.sgm.connect_nodes(uart_name, master_name)
    # Get the number of connections after adding a connection.
    num_of_connections = self.sgm.get_number_of_connections()

    self.assertEqual(num_of_connections, 1)

  def test_disconnect_nodes(self):
    if self.dbg:
      print "adding two nodes"

    self.sgm.add_node("uart", gm.NodeType.HOST_INTERFACE)
    self.sgm.add_node("master", gm.NodeType.MASTER)

    uart_name = gm.get_unique_name("uart", gm.NodeType.HOST_INTERFACE)
    master_name = gm.get_unique_name("master", gm.NodeType.MASTER)

    # Get the number of connections before adding a connection.
    num_of_connections = self.sgm.get_number_of_connections()
    self.assertEqual(num_of_connections, 0)
    self.sgm.connect_nodes(uart_name, master_name)

    # Get the number of connections after adding a connection.
    num_of_connections = self.sgm.get_number_of_connections()

    self.assertEqual(num_of_connections, 1)

    self.sgm.disconnect_nodes(uart_name, master_name)
    num_of_connections = self.sgm.get_number_of_connections()
    self.assertEqual(num_of_connections, 0)

  def test_edge_name(self):
    if self.dbg:
      print "adding two nodes, connecting them, setting the name and then \
      reading it"

    self.sgm.add_node("uart", gm.NodeType.HOST_INTERFACE)
    self.sgm.add_node("master", gm.NodeType.MASTER)

    uart_name = gm.get_unique_name("uart", gm.NodeType.HOST_INTERFACE)
    master_name = gm.get_unique_name("master", gm.NodeType.MASTER)

    self.sgm.connect_nodes(uart_name, master_name)

    self.sgm.set_edge_name(uart_name, master_name, "connection")

    result = self.sgm.get_edge_name(uart_name, master_name)
    self.assertEqual(result, "connection")

  def test_edge_dict(self):
    if self.dbg:
      print "adding two nodes, connecting them, setting the name and then \
      reading it"

    uart_name = self.sgm.add_node("uart",
                                  gm.NodeType.SLAVE,
                                  gm.SlaveType.PERIPHERAL)
    master_name = self.sgm.add_node("master",
                                    gm.NodeType.SLAVE,
                                    gm.SlaveType.PERIPHERAL)

    self.sgm.connect_nodes(uart_name, master_name)

    self.sgm.set_edge_name(uart_name, master_name, "connection")

    result = self.sgm.is_slave_connected_to_slave(uart_name)
    self.assertEqual(result, True)

    arb_dict = self.sgm.get_connected_slaves(uart_name)
    self.assertEqual(arb_dict["connection"], master_name)

  def test_get_node_data(self):
    if self.dbg:
      print "adding a nodes"

    self.sgm.add_node("uart", gm.NodeType.HOST_INTERFACE)
    uart_name = gm.get_unique_name("uart", gm.NodeType.HOST_INTERFACE)

    node = self.sgm.get_node(uart_name)
    self.assertEqual(node.name, "uart")

  def test_set_parameters(self):
    """Set all the parameters aquired from a module."""
    self.sgm.add_node("uart", gm.NodeType.HOST_INTERFACE)
    uart_name = gm.get_unique_name("uart", gm.NodeType.HOST_INTERFACE)

    file_name = os.getenv("SAPLIB_BASE") + "/hdl/rtl/wishbone/host_interface/uart/uart_io_handler.v"
    parameters = saputils.get_module_tags(filename = file_name, bus="wishbone")

    self.sgm.set_parameters(uart_name, parameters)
    parameters = None
    if self.dbg:
      print "parameters: " + str(parameters)

    parameters = self.sgm.get_parameters(uart_name)

    if self.dbg:
      print "parameters: " + str(parameters)

    self.assertEqual(parameters["module"], "uart_io_handler")

#  def test_bind_pin_to_port(self):
#    self.sgm.add_node("uart", gm.NodeType.host_interface)
#    uart_name = gm.get_unique_name("uart", gm.NodeType.host_interface)
#
#    file_name = os.getenv("SAPLIB_BASE") +
#                "/hdl/rtl/wishbone/host_interface/uart/uart_io_handler.v"
#    parameters = saputils.get_module_tags(filename = file_name, bus="wishbone")
#
#    self.sgm.set_parameters(uart_name, parameters)
#
#    self.sgm.bind_pin_to_port(uart_name, "phy_uart_in", "RX")
#
#    parameters = None
#    parameters = self.sgm.get_parameters(uart_name)
#
#    #print "Dictionary: " + str(parameters["ports"]["phy_uart_in"])
#    self.assertEqual(parameters["ports"]["phy_uart_in"]["port"], "RX")

  def test_move_peripheral_slave(self):
    self.sgm.add_node("slave_1",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_2",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_3",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)

    if self.dbg:
      count = self.sgm.get_number_of_peripheral_slaves()
      print "Number of slaves: %d" % (count)
    self.sgm.move_slave(2, 1, gm.SlaveType.PERIPHERAL)

    s3_name = gm.get_unique_name("slave_3",
                                 gm.NodeType.slave,
                                 gm.SlaveType.PERIPHERAL,
                                 slave_index = 1)

    result = True
    try:
      node = self.sgm.get_node(s3_name)
    except NodeError as ex:
      print "Error while trying to get Node: " + str(ex)
      result = False

    self.assertEqual(result, True)

  def test_move_memory_slave(self):
    self.sgm.add_node("slave_1",
                      gm.NodeType.slave,
                      gm.SlaveType.memory,
                      debug = self.dbg)
    self.sgm.add_node("slave_2",
                      gm.NodeType.slave,
                      gm.SlaveType.memory,
                      debug = self.dbg)
    self.sgm.add_node("slave_3",
                      gm.NodeType.slave,
                      gm.SlaveType.memory,
                      debug = self.dbg)

    if self.dbg:
      count = self.sgm.get_number_of_memory_slaves()
      print "Number of slaves: %d" % (count)

    result = self.sgm.move_slave(2, 1, gm.SlaveType.memory)

    s3_name = gm.get_unique_name("slave_3",
                                 gm.NodeType.slave,
                                 gm.SlaveType.memory,
                                 slave_index = 1)

    node = self.sgm.get_node(s3_name)

  def test_get_slave_at(self):
    self.sgm.add_node("slave_1",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_2",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_3",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)

    test_name = gm.get_unique_name("slave_2",
                                   gm.NodeType.slave,
                                   gm.SlaveType.PERIPHERAL,
                                   slave_index = 1)
    found_name = self.sgm.get_slave_name_at(1, gm.SlaveType.PERIPHERAL)
    node = self.sgm.get_slave_at(1, gm.SlaveType.PERIPHERAL)

    self.assertEqual(test_name, node.unique_name)

  def test_get_slave_name_at(self):
    self.sgm.add_node("slave_1",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_2",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_3",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)

    test_name = gm.get_unique_name("slave_2",
                                   gm.NodeType.slave,
                                   gm.SlaveType.PERIPHERAL,
                                   slave_index = 1)
    found_name = self.sgm.get_slave_name_at(1, gm.SlaveType.PERIPHERAL)


    self.assertEqual(test_name, found_name)

  def test_remove_slave(self):
    self.sgm.add_node("slave_1",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_2",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)
    self.sgm.add_node("slave_3",
                      gm.NodeType.slave,
                      gm.SlaveType.PERIPHERAL,
                      debug = self.dbg)

    self.sgm.remove_slave(1, gm.SlaveType.PERIPHERAL)

    count = self.sgm.get_number_of_slaves(gm.SlaveType.PERIPHERAL)
    self.assertEqual(count, 2)

if __name__ == "__main__":
  unittest.main()

