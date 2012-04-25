
class box:
	def __init__(self):
		self.x = 0.0
		self.y = 0.0
		self.width = 0.0
		self.height = 0.0
		self.tag = ""
		self.r = 0.0
		self.g = 0.0
		self.b = 0.0

	def in_bounding_box(self, x, y):
		if 	self.x <= x and x <= (self.x + self.width) and \
			self.y <= y and y <= (self.y + self.height):

			return True

		return False
