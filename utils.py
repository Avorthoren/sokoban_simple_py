# -*- coding: utf-8 -*-

def idGenerator(start=1):
	"""Generate consecutive ids.

	Generator function. Generates consecutive ints starting from `start`
	Usage example:
	>>> id_ = idGenerator()
	>>> next(id_)
	1
	>>> next(id_)
	2

	Args:
	start - int, starting id

	Return:
	generator which yields int
	"""
	id_ = start
	while True:
		yield id_
		id_ += 1


class MaxLenDict(dict):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._maxLen = len(self)

	@property
	def maxLen(self):
		return self._maxLen

	def __setitem__(self, *args, **kwargs):
		super().__setitem__(*args, **kwargs)
		self._maxLen = len(self)

	def update(self, *args, **kwargs):
		super().update(*args, **kwargs)
		self._maxLen = len(self)


if __name__ == "__main__":
	d = MaxLenDict()
	print(d.maxLen)
	d.update({1: 1, 2: 2})
	print(d.maxLen)
	d[3] = 3
	print(d.maxLen)
	del d[1]
	print(d.maxLen)
