# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Union, Sequence


def f(
	a: int,
	b: Union[None, Sequence[int]] = None
) -> None:
	print(a)
	print(b)


class Test:
	def __init__(self):
		self.a = 1

	def rawCopy(self):
		cls = self.__class__
		copy_ = cls.__new__(cls)

		return copy_


if __name__ == "__main__":
	t = Test()
	print(t.a)
	tc = t.rawCopy()
	tc.a = 2
	print(tc.a)
