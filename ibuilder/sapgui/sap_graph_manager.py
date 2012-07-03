#!/usr/bin/env python
import networkx as nx
import sapfile
from saperror import SlaveError

class NodeError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class PortError(Exception):
  pass

def enum(*sequential, **named):
  enums = dict(zip(sequential, range(len(sequential))), **named)
  return type('Enum', (), enums)

NodeType = enum('HOST_INTERFACE',
                'MASTER',
                'MEMORY_INTERCONNECT',
                'PERIPHERAL_INTERCONNECT',
                'SLAVE')

def isNodeType(nt):
  return nt == NodeType.HOST_INTERFACE or \
         nt == NodeType.MASTER or \
         nt == NodeType.MEMORY_INTERCONNECT or \
         nt == NodeType.PERIPHERAL_INTERCONNECT or \
         nt == NodeType.SLAVE

SlaveType = enum('MEMORY', 'PERIPHERAL')

def isSlaveType(st):
  return st == SlaveType.MEMORY or st == SlaveType.PERIPHERAL

def get_unique_name(name, node_type,
    slave_type = SlaveType.PERIPHERAL, slave_index = 0):
  if node_type == NodeType.SLAVE:
    unique_name = name + "_" + str(slave_type) + "_" + str(slave_index)
  else:
    unique_name = name + "_" + str(node_type)
  return unique_name

class SapNode:
  name = ""
  unique_name = ""
  node_type = NodeType.SLAVE
  slave_type = SlaveType.PERIPHERAL
  slave_index = 0
  parameters={}
  bindings={}

  def __init__(self):
    self.name = ""
    self.unique_name = ""
    self.node_type = NodeType.SLAVE
    self.slave_type = SlaveType.PERIPHERAL
    self.slave_index = 0
    self.parameters={}
    self.bindings={}

  def copy(self):
    nn = SapNode()
    nn.name = self.name
    nn.unique_name = self.unique_name
    nn.node_type = self.node_type
    nn.slave_type = self.slave_type
    nn.slave_index = self.slave_index
    nn.parameters = self.parameters
    nn.bindings = self.bindings.copy()
    return nn


class SapGraphManager:
  def __init__(self):
    """Initialize the controller."""
    self.graph = nx.Graph()

    # Additions for DI.
    self.get_unique_name = get_unique_name

  def clear_graph(self):
    """Resets the graph."""
    self.graph = nx.Graph()

  def add_node(self, name, node_type, slave_type=SlaveType.PERIPHERAL,
      debug=False):
    '''Adds a node to this graph.'''

    # Check node_type validity
    if not isNodeType(node_type):
      raise TypeError('Expected node_type to be NodeType, got' + node_type)

    # Set index to last in peripheral/memory and check SlaveType validity.
    if slave_type == SlaveType.PERIPHERAL:
      s_count = self.get_number_of_peripheral_slaves()
    elif slave_type == SlaveType.MEMORY:
      s_count = self.get_number_of_memory_slaves()
    else:
      raise TypeError("Expected SlaveType.{MEMORY|PERIPHERAL}, got " +
          slave_type)

    # Create & populate node.
    node = SapNode()
    node.name = name
    node.node_type = node_type
    node.slave_type = slave_type
    node.slave_index = s_count
    node.unique_name = self.get_unique_name(
        name, node_type, slave_type, node.slave_index)

    if debug:
      print "unique_name: " + node.unique_name

    # Add node to graph.
    self.graph.add_node(str(node.unique_name))
    self.graph.node[node.unique_name] = node

    return node.unique_name

  def remove_slave(self, slave_index, slave_type):
    # Can't remove the DRT so if the index is 0 then don't try.
    if slave_type == SlaveType.PERIPHERAL and slave_index == 0:
      raise SlaveError ("DRT cannot be removed")

    count = self.get_number_of_slaves(slave_type)
    if slave_index >= count:
      if slave_type == SlaveType.PERIPHERAL:
        raise SlaveError("Slave index %d on peripheral bus is out of range" % \
            (slave_index))
      else:
        raise SlaveError("Slave index %d on memory bus is out of range" % \
            (slave_index))

    # Move the slave to the end so I can remove it.
    if slave_index < count:
      for index in range (slave_index, count - 1):
        self.move_slave(index, index + 1, slave_type)

    slave_name = self.get_slave_name_at(count - 1, slave_type)
    self.graph.remove_node(slave_name)

  def rename_slave(self, slave_type, slave_index, new_name):
    current_name = self.get_slave_name_at(slave_index, slave_type)
    node = self.get_node(current_name)

    unique_name = self.get_unique_name(
        new_name, NodeType.SLAVE, slave_type, slave_index)

    node.name = new_name
    node.unique_name = unique_name
    self.graph = nx.relabel_nodes(self.graph, {current_name : unique_name})

  def get_host_interface_node(self):
    '''Gets the unique host interface.  Raises severe Exception if none is in
    the underlying graph.'''
    for node in self.graph:
      if node.node_type == NodeType.HOST_INTERFACE:
        return node
    raise Exception("SEVERE: No host interface defined!")

  def fix_slave_indexes(self):
    '''Loops through all the slaves (peripheral and memory) and assigns
    their index ... to ... their index?  This function may need to be
    deprecated as I (jam) don't think it does anything.'''
    pcount = self.get_number_of_slaves(SlaveType.PERIPHERAL)
    mcount = self.get_number_of_slaves(SlaveType.MEMORY)

    for i in xrange(pcount):
      name = self.get_slave_name_at(i, SlaveType.PERIPHERAL)
      node = self.get_node(name)
      node.slave_index = i

    for i in xrange(mcount):
      name = self.get_slave_name_at(i, SlaveType.MEMORY)
      node = self.get_node(name)
      node.slave_index = i

  def get_slave_at(self, index, slave_type, debug = False):
    name = self.get_slave_name_at(index, slave_type, debug)
    return self.get_node(name)

  def get_slave_name_at(self, index, slave_type, debug=False):
    if slave_type is None:
      raise SlaveError("Peripheral or Memory must be specified")

    graph_dict = self.get_nodes_dict()

    for key in graph_dict.keys():
      node = graph_dict[key]
      if node.node_type != NodeType.SLAVE or node.slave_type != slave_type:
        continue

      if debug:
        print "node: " + node.name
        print "node.slave_index: " + str(node.slave_index)
        print "index: " + str(index)

      if node.slave_index == index:
        if debug:
          print "success"
        return key

    raise SlaveError("Unable to locate slave %d on %s bus" %
        (index, slave_type == SlaveType.PERIPHERAL and 'peripheral' or 'memory'))

  def move_slave(self, from_index, to_index, slave_type, debug=False):
    if from_index == to_index:
      return

    if slave_type is None:
      raise SlaveError ("Slave Type must be specified")

    if slave_type == SlaveType.PERIPHERAL:
      self.move_peripheral_slave(from_index, to_index, debug)
    else:
      self.move_memory_slave(from_index, to_index, debug)

    # TODO Test me.
    self.fix_slave_indexes()

  def move_peripheral_slave(self, from_index, to_index, debug=False):
    """Move the slaves from the from_index to the to index."""
    s_count = self.get_number_of_peripheral_slaves()
    if to_index >= s_count:
      to_index = s_count - 1

    if from_index == to_index:
      return

    if from_index == 0:
      raise SlaveError ("Cannot move DRT")
    if to_index == 0:
      raise SlaveError ("DRT is the only peripheral slave at index 0")

    graph_dict = self.get_nodes_dict()

    # Find the slave at the from_index.
    from_node = None
    for key in graph_dict.keys():
      if debug:
        print "Checking: %s" % (graph_dict[key].name)
      if graph_dict[key].node_type != NodeType.SLAVE or \
          graph_dict[key].slave_type != SlaveType.PERIPHERAL:
        continue

      if debug:
        print "\tChecking index: %d" % (graph_dict[key].slave_index)

      if graph_dict[key].slave_index != from_index:
        continue

      from_node = graph_dict[key]
      break

    if from_node is None:
      raise SlaveError("Slave with from index %d not found" % (from_index))

    # Find the slave at the to_index.
    to_node = None
    for key in graph_dict.keys():
      if graph_dict[key].node_type != NodeType.SLAVE or \
          graph_dict[key].slave_type != SlaveType.PERIPHERAL or \
          graph_dict[key].slave_index != to_index:
        continue
      to_node = graph_dict[key]
      break

    if to_node is None:
      raise SlaveError("Slave with to index %d not found" % (to_index))

    if debug:
      print "before move:"
      print "\tslave %s at position %d with name: %s" % \
          (from_node.name, from_node.slave_index, from_node.unique_name)
      print "\tslave %s at position %d with name: %s" % \
          (to_node.name, to_node.slave_index, to_node.unique_name)

    from_node.slave_index = to_index
    from_unique = self.get_unique_name(from_node.name,
                                       from_node.node_type,
                                       from_node.slave_type,
                                       from_node.slave_index)

    mapping = {from_node.unique_name : from_unique}

    if debug:
      print "from.unique_name: " + from_node.unique_name
      print "from_unique: " + from_unique

      print "keys"
      for name in graph_dict.keys():
        print "key: " + name

    self.graph = nx.relabel_nodes(self.graph,
                                  {from_node.unique_name : from_unique})
    from_node = self.get_node(from_unique)
    from_node.slave_index = to_index
    from_node.unique_name = from_unique

    to_node.slave_index = from_index
    to_unique = self.get_unique_name(to_node.name,
                                     to_node.node_type,
                                     to_node.slave_type,
                                     to_node.slave_index)
    self.graph = nx.relabel_nodes (self.graph, {to_node.unique_name:to_unique})
    to_node = self.get_node(to_unique)

    to_node.slave_index = from_index
    to_node.unique_name = to_unique

    if debug:
      print "after move:"
      print "\tslave %s at position %d with name: %s" % \
          (from_node.name, from_node.slave_index, from_node.unique_name)
      print "\tslave %s at position %d with name: %s" % \
          (to_node.name, to_node.slave_index, to_node.unique_name)

      graph_dict = self.get_nodes_dict()
      print "keys"
      for name in graph_dict.keys():
        print "key: " + name

  def move_memory_slave(self, from_index, to_index, debug=False):
    """Move the slave from the from_index to the to_index."""
    s_count = self.get_number_of_memory_slaves()
    if to_index >= s_count:
      to_index = s_count - 1

    if from_index == to_index:
      return

    graph_dict = self.get_nodes_dict()

    # Find the slave at the from_index.
    from_node = None
    for key in graph_dict.keys():
      if graph_dict[key].node_type != NodeType.SLAVE or \
          graph_dict[key].slave_type != SlaveType.MEMORY or \
          graph_dict[key].slave_index != from_index:
        continue
      from_node = graph_dict[key]
      break

    if from_node is None:
      raise SlaveError("Slave with from index %d not found" % (from_index))

    # Find the slave at the to_index.
    to_node = None
    for key in graph_dict.keys():
      if graph_dict[key].node_type != NodeType.SLAVE or \
          graph_dict[key].slave_type != SlaveType.MEMORY or \
          graph_dict[key].slave_index != to_index:
        continue
      to_node = graph_dict[key]
      break

    if to_node is None:
      raise SlaveError("Slave with to index %d not found" % (to_index))

    if debug:
      print "before move:"
      print "\tslave %s at position %d with name: %s" % \
          (from_node.name, from_node.slave_index, from_node.unique_name)
      print "\tslave %s at position %d with name: %s" % \
          (to_node.name, to_node.slave_index, to_node.unique_name)

    from_node.slave_index = to_index
    from_unique = self.get_unique_name(from_node.name,
                                       from_node.node_type,
                                       from_node.slave_type,
                                       from_node.slave_index)

    mapping = {from_node.unique_name : from_unique}

    if debug:
      print "from.unique_name: " + from_node.unique_name
      print "from_unique: " + from_unique

      print "keys"
      for name in graph_dict.keys():
        print "key: " + name

    self.graph = nx.relabel_nodes(self.graph,
                                  {from_node.unique_name : from_unique})
    from_node = self.get_node(from_unique)
    from_node.slave_index = to_index
    from_node.unique_name = from_unique

    to_node.slave_index = from_index
    to_unique = self.get_unique_name(to_node.name,
                                     to_node.node_type,
                                     to_node.slave_type,
                                     to_node.slave_index)
    self.graph = nx.relabel_nodes(self.graph, {to_node.unique_name:to_unique})

    to_node = self.get_node(to_unique)
    to_node.slave_index = from_index
    to_node.unique_name = to_unique

    if debug:
      print "after move:"
      print "\tslave %s at position %d with name: %s" % \
          (from_node.name, from_node.slave_index, from_node.unique_name)
      print "\tslave %s at position %d with name: %s" % (\
          to_node.name, to_node.slave_index, to_node.unique_name)

      graph_dict = self.get_nodes_dict()
      print "keys"
      for name in graph_dict.keys():
        print "key: " + name

  def remove_node(self, name):
    """Removes a node using the unique name to find it."""

    # Since the master and slave are always constant, the only nodes that can be
    # removed are the slaves.

    # Procedure:
    # - Search for the connections between the interconnect and the slave.
    # - Sever the connection.
    # - If the slave has a master for arbitration purposes, sever that
    #   connection.

    self.graph.remove_node(name)

  def get_size(self):
    '''Returns the number of nodes in the graph.'''
    return len(self.graph)

  def get_node_names(self):
    """Get all names usually for the purpose of iterating through the
    graph."""
    return self.graph.nodes(False)

  def get_nodes_dict(self):
    '''Builds a dictionary from the nodes in the graph, where the key is the
    name of the node, and the value is the node itself.'''
    return dict(self.graph.nodes(True))

  def get_node(self, name):
    """Gets a node by the unique name."""
    g = self.get_nodes_dict()
    if name not in g:
      raise NodeError("Node with unique name: %s does not exists" % name)
    return g[name]

  def connect_nodes(self, node1, node2):
    """Connects two nodes together.  Creates them if they don't exist."""
    self.graph.add_edge(node1, node2, name='')

  def set_edge_name(self, node1_name, node2_name, edge_name):
    """Find the edge connected to the two given nodes."""
    self.graph[node1_name][node2_name]["name"]=edge_name

  def get_edge_name(self, node1_name, node2_name):
    try:
      return self.graph[node1_name][node2_name]["name"]
    except KeyError as ke:
      if node1_name not in self.graph:
        raise NodeError('No such node: %s' % node1_name)
      elif node2_name not in self.graph[node1_name]:
        raise NodeError('No edge between %s and %s' % (node1_name, node2_name))
      else:
        raise Exception('SEVERE: edge has no "name" attribute.')

  def is_slave_connected_to_slave(self, slave):
    for nb_name in self.graph.neighbors(slave):
      nb = self.get_node(nb_name)
      if nb.node_type == NodeType.SLAVE:
        return True
    return False

  def get_connected_slaves(self, slave_master_name):
    slaves = {}
    try:
      for nb_name in self.graph.neighbors(slave_master_name):
        nb = self.get_node(nb_name)
        if nb.node_type == NodeType.SLAVE:
          edge_name = self.get_edge_name(slave_master_name, nb_name)
          slaves[edge_name] = nb.unique_name
    except nx.exception.NetworkXError:
      raise NodeError("No such node: %s" % slave_master_name)
    return slaves

  def disconnect_nodes(self, n1, n2):
    """If the two nodes are connected disconnect them."""
    try:
      self.graph.remove_edge(n1, n2)
    except nx.exception.NetworkXError:
      raise NodeError('''"%s" and "%s" aren't connected''' % (n1, n2))

  def get_number_of_connections(self):
    return self.graph.number_of_edges()

  def get_number_of_slaves(self, slave_type):
    '''Gets the number of slaves.  Raises a SaveError if there is no slave type
    or the slave type is SlaveType.PERIPHERAl.'''
    if slave_type is None:
      raise SaveError("Slave type must be specified")

    if slave_type == SlaveType.PERIPHERAL:
      return self.get_number_of_peripheral_slaves()

    return self.get_number_of_memory_slaves()

  def get_number_of_peripheral_slaves(self):
    '''Counts and returns the number of peripheral slaves.'''
    return sum([1 for node in self.graph if node.node_type == NodeType.SLAVE and
        node.slave_type == SlaveType.PERIPHERAL])

  def get_number_of_memory_slaves(self):
    '''Counts and returns the number of memory slaves.'''
    return sum([1 for node in self.graph if node.node_type == NodeType.SLAVE and
        node.slave_type == SlaveType.MEMORY])



  ##############################################################################
  #                              Control Stuff                                 #
  ##############################################################################

  def set_parameters(self, name, parameters, debug = False):
    """Sets all the parameters from the core."""
    g = self.get_nodes_dict()
    g[name].parameters = parameters

    # TODO Re-organize the way that ports are put into the parameters.
    pdict = parameters["ports"]
    pdict_out = dict()
    direction_names = ["input", "output", "inout"]

    if debug:
      print "parameters: " + str(pdict)
    for d in direction_names:
      for n in pdict[d].keys():
        pdict_out[n] = {}
        pdict_out[n]["direction"] = d
        if "size" in pdict[d][n]:
          pdict_out[n]["size"] = pdict[d][n]["size"]
        if "max_val" in pdict[d][n]:
          pdict_out[n]["max_val"] = pdict[d][n]["max_val"]
        if "min_val" in pdict[d][n]:
          pdict_out[n]["min_val"] = pdict[d][n]["min_val"]

    g[name].parameters["ports"] = {}
    g[name].parameters["ports"] = pdict_out

  def get_parameters(self, name):
    g = self.get_nodes_dict()
    return g[name].parameters

  def set_config_bindings(self, name, bindings):
    node = self.get_node(name)
    node.bindings.clear()
    for p in bindings.keys():
      node.bindings[p] = {}
      node.bindings[p]["pin"] = bindings[p]["port"]
      node.bindings[p]["direction"] = bindings[p]["direction"]

  def bind_port(self, name, port, pin, debug=False):
    if type(port) is not str:
      raise TypeError('port must be str')
    node = self.get_node(name)
    if port not in node.parameters['ports']:
      raise PortError('Could not find port ' + port)
    direction = node.parameters["ports"][port]["direction"]
    node.bindings[port] = {}
    node.bindings[port]["pin"] = pin
    node.bindings[port]["direction"] = direction

  def unbind_port(self, name, port):
    node = self.get_node(name)
    if port not in node.bindings.keys():
      raise SlaveError("port %s is not in the binding dictionary for node %s" \
          % (port, name))
    del(node.bindings[port])

  def get_node_bindings(self, name):
    '''Gets the bindings of the node with the given name.  Raises NodeError
    if there is no node with that name.'''
    return self.get_node(name).bindings

#  def bind_pin_to_port(self, name, port, pin, debug = False):
#    """
#    binds the specific port to a pin
#    """
#    g = self.get_nodes_dict()
#    if debug:
#      print "Dictionary: " + str(g[name].parameters["ports"][port])
#    node = self.get_node(name)
#    g[name].parameters["ports"][port]["port"] = pin

