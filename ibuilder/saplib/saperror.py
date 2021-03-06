
class SlaveError(Exception):
  """SlaveError

  Errors associated with slaves in particular:
    setting incorrect parameters.
    setting incorrect bindings
  """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class ModuleNotFound(Exception):
  """ModuleNotFound

  Errors associated with searching for a module file location
  usually occurs when the module is not found in the local directory
  or in the rtl files in ibuilder
  """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class ModuleFactoryError(Exception):
  """ModuleFactoryError

  Errors associated with creating and generating modules
    Modules may not be found
    Modules generation script may not be found
    Unable to execute a gen script
  """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class PreProcessorError(Exception):
  """PreProcessorError
    
  Errors associated with preprocessing a file
  Errors include:
    Defines that could not be evaluated
    Referenced modules not located
  """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class ArbitratorError(Exception):
  """ArbitratorError

  Errors associated with generatign arbitrators
    User didn't specify the number of masters required
  """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

