import unittest
import os
import sys
import json
import mock
from networkx.exception import NetworkXError

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'saplib'))

import sapfile
import saputils
import sap_graph_manager as gm
from sap_graph_manager import NodeType, SlaveType, SlaveError, NodeError, PortError

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

  def test_bind_port_raises_NodeError(self):
    arg_n, arg_po, arg_pi = 'name', '1234', 3
    self.sgm.get_node = mock.Mock(side_effect=NodeError('No such node!'))
    self.assertRaises(NodeError, self.sgm.bind_port, arg_n, arg_po, arg_pi)

  def test_bind_port_raises_TypeError(self):
    self.assertRaises(TypeError, self.sgm.bind_port, 'name', None, 4)

  def test_bind_port_raises_PortError(self):
    mock_node = mock.Mock()
    mock_node.parameters = {
      'ports' : {
        '1235' : { 'direction' : 'out' },
        '1233' : { 'direction' : 'in' }
      }
    }
    self.sgm.get_node = mock.Mock(return_value=mock_node)
    self.assertRaises(PortError, self.sgm.bind_port, 'name', '1234', 4)

  def test_clear_graph(self):
    # TODO ... really test?  how?
    pass

  def test_connect_nodes(self):
    arg1, arg2 = 'name1', 'name2'
    self.sgm.graph.add_edge = mock.Mock()
    self.sgm.connect_nodes(arg1, arg2)
    self.sgm.graph.add_edge.assert_called_once_with(arg1, arg2, name='')

  def test_disconnect_nodes(self):
    self.sgm.graph.remove_edge = mock.Mock()
    self.sgm.disconnect_nodes('n1', 'n2')
    self.sgm.graph.remove_edge.assert_called_once_with('n1', 'n2')

  def test_disconnect_nodes_dne_raises_NodeError(self):
    self.sgm.graph.remove_edge = mock.Mock(
        side_effect=NetworkXError('Should convert me!'))
    self.assertRaises(NodeError, self.sgm.disconnect_nodes, 'n1', 'n2')
    self.sgm.graph.remove_edge.assert_called_once_with('n1', 'n2')

  def test_fix_slave_indexes_leaves_well_enough_alone(self):
    pcount, mcount = 6, 3

    # Make fake slaves to re-order.
    mock_slaves = {}
    mock_pslaves = []
    mock_mslaves = []
    for i in xrange(pcount):
      mock_pslaves.append(mock.Mock())
      mock_pslaves[-1].name = 'p%d' % i
      mock_pslaves[-1].slave_index = i
      mock_slaves[mock_pslaves[-1].name] = mock_pslaves[-1]
    for i in xrange(mcount):
      mock_mslaves.append(mock.Mock())
      mock_mslaves[-1].name = 'm%d' % i
      mock_mslaves[-1].slave_index = i
      mock_slaves[mock_mslaves[-1].name] = mock_mslaves[-1]

    # Overwrite functions.
    self.sgm.get_number_of_slaves = (lambda x:
        (x == SlaveType.PERIPHERAL and pcount) or
        (x == SlaveType.MEMORY and mcount) or
        self.fail('Unexpected arg: %s' % str(x)))
    self.sgm.get_slave_name_at = (lambda i,x:
        (x == SlaveType.PERIPHERAL and mock_pslaves[i].name) or
        (x == SlaveType.MEMORY and mock_mslaves[i].name) or
        self.fail("Unexpected args: %d,%s" % (i,x)))
    self.sgm.get_node = lambda n: mock_slaves[n]

    # Test
    self.sgm.fix_slave_indexes()
    for i in xrange(pcount):
      self.assertEqual(mock_pslaves[i].slave_index, i)
    for i in xrange(mcount):
      self.assertEqual(mock_mslaves[i].slave_index, i)

  def test_fix_slave_indexes_reorders_correctly(self):
    pcount, mcount = 3, 2

    # Make fake slaves to re-order.
    mock_slaves = {}
    mock_pslaves = []
    mock_mslaves = []
    for i in xrange(pcount):
      mock_pslaves.append(mock.Mock())
      mock_pslaves[-1].name = 'p%d' % i
      mock_pslaves[-1].slave_index = pcount - 1 - i
      mock_slaves[mock_pslaves[-1].name] = mock_pslaves[-1]
    for i in xrange(mcount):
      mock_mslaves.append(mock.Mock())
      mock_mslaves[-1].name = 'm%d' % i
      mock_mslaves[-1].slave_index = mcount - 1 - i
      mock_slaves[mock_mslaves[-1].name] = mock_mslaves[-1]

    # Overwrite functions.
    self.sgm.get_number_of_slaves = (lambda x:
        (x == SlaveType.PERIPHERAL and pcount) or
        (x == SlaveType.MEMORY and mcount) or
        self.fail('Unexpected arg: %s' % str(x)))
    self.sgm.get_slave_name_at = (lambda i,x:
        (x == SlaveType.PERIPHERAL and mock_pslaves[i].name) or
        (x == SlaveType.MEMORY and mock_mslaves[i].name) or
        self.fail("Unexpected args: %d,%s" % (i,x)))
    self.sgm.get_node = lambda n: mock_slaves[n]

    # Test
    self.sgm.fix_slave_indexes()
    for i in xrange(pcount):
      self.assertEqual(mock_pslaves[i].slave_index, i)
    for i in xrange(mcount):
      self.assertEqual(mock_mslaves[i].slave_index, i)

  def test_get_connected_slaves(self):
    # Make mock data.
    mock_node_names = []
    mock_nodes = {}
    mock_slaves = {}
    mock_edge_names = {}

    def add_node(name, nt):
      mock_node_names.append(name)
      mock_nodes[name] = mock.Mock()
      mock_nodes[name].unique_name = name
      mock_nodes[name].node_type = nt
      if nt == NodeType.SLAVE:
        edge_name = 'edge-%s' % name
        mock_edge_names[name] = edge_name
        mock_slaves[edge_name] = mock_nodes[name].unique_name
    add_node('n1', NodeType.SLAVE)
    add_node('n2', NodeType.HOST_INTERFACE)
    add_node('n3', NodeType.SLAVE)
    add_node('n4', NodeType.MEMORY_INTERCONNECT)
    add_node('n5', NodeType.SLAVE)
    add_node('n6', NodeType.PERIPHERAL_INTERCONNECT)
    add_node('n7', NodeType.SLAVE)

    # Set up functions.
    self.sgm.graph.neighbors = mock.Mock(return_value=mock_node_names)
    self.sgm.get_node = (lambda x:
        (x in mock_nodes and mock_nodes[x]) or
        self.fail('Unexpected param: %s' % x))
    self.sgm.get_edge_name = (lambda x,y:
      (x == 'mname' and mock_edge_names[y]) or
      self.fail("Unexpected params: %s,%s" % (x,y)))

    # Test
    self.assertEqual(mock_slaves, self.sgm.get_connected_slaves('mname'))
    self.sgm.graph.neighbors.assert_called_once_with('mname')

  def test_get_connected_slaves_dne_raises_NodeError(self):
    self.sgm.graph.neighbors = mock.Mock(
        side_effect=NetworkXError('Should convert me!'))
    self.assertRaises(NodeError, self.sgm.get_connected_slaves, 'name')
    self.sgm.graph.neighbors.assert_called_once_with('name')

  def test_get_edge_name(self):
    self.sgm.graph = { 'n1' : { 'n2' : { 'name' : 'edge_name' } } }
    self.assertEqual('edge_name', self.sgm.get_edge_name('n1', 'n2'))

  def test_get_edge_name_malformat_raises_Exception(self):
    self.sgm.graph = { 'n1' : { 'n2' : {} } }
    self.assertRaises(Exception, self.sgm.get_edge_name, 'n1', 'n2')

  def test_get_edge_name_edge_dne_raises_NodeError(self):
    self.sgm.graph = { 'n1' : {} }
    self.assertRaises(NodeError, self.sgm.get_edge_name, 'n1', 'n2')

  def test_get_edge_name_node_dne_raises_NodeError(self):
    self.sgm.graph = {}
    self.assertRaises(NodeError, self.sgm.get_edge_name, 'n1', 'n2')

  def test_get_host_interface_node(self):
    mock_nodes = []
    def make_mock(nt):
      mock_nodes.append(mock.Mock())
      mock_nodes[-1].node_type = nt
    make_mock(NodeType.HOST_INTERFACE)

    self.sgm.graph = mock_nodes
    self.assertEqual(mock_nodes[0], self.sgm.get_host_interface_node())

  def test_get_host_interface_node_populous(self):
    mock_nodes = []
    def make_mock(nt):
      mock_nodes.append(mock.Mock())
      mock_nodes[-1].node_type = nt
    make_mock(NodeType.SLAVE)
    make_mock(NodeType.SLAVE)
    make_mock(NodeType.SLAVE)
    make_mock(NodeType.MASTER)
    make_mock(NodeType.HOST_INTERFACE)
    make_mock(NodeType.PERIPHERAL_INTERCONNECT)
    make_mock(NodeType.PERIPHERAL_INTERCONNECT)

    self.sgm.graph = mock_nodes
    self.assertEqual(mock_nodes[4], self.sgm.get_host_interface_node())

  def test_get_host_interface_node_populous_dne_raises_Exception(self):
    mock_nodes = []
    def make_mock(nt):
      mock_nodes.append(mock.Mock())
      mock_nodes[-1].node_type = nt
    make_mock(NodeType.SLAVE)
    make_mock(NodeType.SLAVE)
    make_mock(NodeType.SLAVE)
    make_mock(NodeType.MASTER)
    make_mock(NodeType.PERIPHERAL_INTERCONNECT)
    make_mock(NodeType.PERIPHERAL_INTERCONNECT)

    self.sgm.graph = mock_nodes
    self.assertRaises(Exception, self.sgm.get_host_interface_node)

  def test_get_host_interface_node_dne_raises_Exception(self):
    mock_nodes = []
    def make_mock(nt):
      mock_nodes.append(mock.Mock())
      mock_nodes[-1].node_type = nt
    make_mock(NodeType.SLAVE)
    make_mock(NodeType.MASTER)

    self.sgm.graph = mock_nodes
    self.assertRaises(Exception, self.sgm.get_host_interface_node)

  def test_get_host_interface_node_empty_raises_Exception(self):
    mock_iter = mock.Mock()
    mock_iter.next = mock.Mock(side_effect=StopIteration("empty!"))
    self.sgm.graph.__iter__ = mock.Mock(return_value=mock_iter)
    self.assertRaises(Exception, self.sgm.get_host_interface_node)

  def test_get_node(self):
    mock_node = mock.Mock()
    self.sgm.get_nodes_dict = mock.Mock(return_value={'name': mock_node})
    self.assertEqual(mock_node, self.sgm.get_node('name'))
    self.sgm.get_nodes_dict.assert_called_once_with()

  def test_get_node_dne_raises_NodeError(self):
    self.sgm.get_nodes_dict = mock.Mock(return_value={})
    self.assertRaises(NodeError, self.sgm.get_node, 'name')
    self.sgm.get_nodes_dict.assert_called_once_with()

  def test_get_node_bindings(self):
    bindings = { 'foo': 1, 'bar': 2, 'baz': 3}
    mock_node = mock.Mock()
    mock_node.bindings = bindings
    self.sgm.get_node = mock.Mock(return_value=mock_node)
    self.assertEqual(bindings, self.sgm.get_node_bindings('name'))
    self.sgm.get_node.assert_called_once_with('name')

  def test_get_node_bindings_dne_raises_NodeError(self):
    self.sgm.get_node = mock.Mock(side_effect=NodeError('msg'))
    self.assertRaises(NodeError, self.sgm.get_node_bindings, 'name')

  def test_get_node_names(self):
    self.sgm.graph.nodes = mock.Mock(return_value=['foo', 'bar', 'baz'])
    self.assertEqual(['foo', 'bar', 'baz'], self.sgm.get_node_names())
    self.sgm.graph.nodes.assert_called_once_with(False)

  def test_get_node_names_0(self):
    self.sgm.graph.nodes = mock.Mock(return_value=[])
    self.assertEqual([], self.sgm.get_node_names())
    self.sgm.graph.nodes.assert_called_once_with(False)

  def test_get_nodes_dict(self):
    mock_nodes = []
    for i in xrange(10):
      mock_node = mock.Mock()
      mock_node.name = 'n%d' % i
      mock_nodes.append((mock_node.name, mock_node))
    self.sgm.graph.nodes = mock.Mock(return_value=mock_nodes)

    # Run & Test
    nd = self.sgm.get_nodes_dict()
    for mock_node in mock_nodes:
      self.assertIn(mock_node[0], nd)
      self.assertEqual(mock_node[1], nd[mock_node[0]])

  def test_get_nodes_dict_empty(self):
    self.sgm.graph.nodes = mock.Mock(return_value=[])
    self.assertEqual({}, self.sgm.get_nodes_dict())

  def test_get_number_of_connections_0(self):
    self.sgm.graph.number_of_edges = mock.Mock(return_value=0)
    self.assertEquals(0, self.sgm.get_number_of_connections())

  def test_get_number_of_connections_6(self):
    self.sgm.graph.number_of_edges = mock.Mock(return_value=6)
    self.assertEquals(6, self.sgm.get_number_of_connections())

  def test_get_number_of_memory_slaves(self):
    self.sgm.graph = []
    def add(nt,st):
      self.sgm.graph.append(mock.Mock())
      self.sgm.graph[-1].node_type = nt
      self.sgm.graph[-1].slave_type = st
    add(NodeType.SLAVE, SlaveType.MEMORY)
    add(NodeType.SLAVE, SlaveType.MEMORY)
    add(NodeType.SLAVE, SlaveType.PERIPHERAL)
    add(NodeType.SLAVE, SlaveType.MEMORY)
    add(NodeType.SLAVE, SlaveType.PERIPHERAL)
    add(NodeType.MEMORY_INTERCONNECT, None)
    add(NodeType.HOST_INTERFACE, None)
    add(NodeType.PERIPHERAL_INTERCONNECT, None)
    add(NodeType.MEMORY_INTERCONNECT, None)
    self.assertEquals(3, self.sgm.get_number_of_memory_slaves())

  def test_get_number_of_peripheral_slaves(self):
    self.sgm.graph = []
    def add(nt,st):
      self.sgm.graph.append(mock.Mock())
      self.sgm.graph[-1].node_type = nt
      self.sgm.graph[-1].slave_type = st
    add(NodeType.SLAVE, SlaveType.MEMORY)
    add(NodeType.SLAVE, SlaveType.MEMORY)
    add(NodeType.SLAVE, SlaveType.PERIPHERAL)
    add(NodeType.SLAVE, SlaveType.MEMORY)
    add(NodeType.SLAVE, SlaveType.PERIPHERAL)
    add(NodeType.MEMORY_INTERCONNECT, None)
    add(NodeType.HOST_INTERFACE, None)
    add(NodeType.PERIPHERAL_INTERCONNECT, None)
    add(NodeType.MEMORY_INTERCONNECT, None)
    self.assertEquals(2, self.sgm.get_number_of_peripheral_slaves())

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

