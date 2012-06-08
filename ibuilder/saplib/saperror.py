
class SlaveError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)


class ModuleNotFound(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class PreProcessorError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)
