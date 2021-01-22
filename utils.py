# -*- coding: utf-8 -*-
from typing import Generator


def idGenerator(start=1) -> Generator[int, None, None]:
	"""Generate consecutive ids."""
	id_ = start
	while True:
		yield id_
		id_ += 1


class MaxLenDict(dict):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._maxLen = len(self)

	@property
	def maxLen(self) -> int:
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
