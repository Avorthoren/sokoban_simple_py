# -*- coding: utf-8 -*-
from itertools import combinations, count
from time import time
from typing import Generator, Set, Tuple, List


def idGenerator(start=1) -> Generator[int, None, None]:
	"""Generate consecutive ids."""
	id_ = start
	while True:
		yield id_
		id_ += 1


def combinationGenerator(n: int, k: int, offset: int = 0) -> Generator[Set[int], None, None]:
	if k == 0:
		yield set()
		return

	for i in range(offset, n - k + 1):
		for subComb in combinationGenerator(n, k - 1, i + 1):
			subComb.add(i)
			yield subComb


def combinationTupleGenerator(n: int, k: int, offset: int = 0) -> Generator[Tuple[int], None, None]:
	if k == 0:
		yield tuple()
		return

	for i in range(offset, n - k + 1):
		for subComb in combinationTupleGenerator(n, k - 1, i + 1):
			yield i, *subComb


def _combinationListGenerator(n: int, k: int, offset: int = 0) -> Generator[List[int], None, None]:
	if k == 0:
		yield []
		return

	for i in reversed(range(k - 1, n - offset)):
		for subComb in _combinationListGenerator(n, k - 1, n - i):
			subComb.append(i)
			yield subComb


def combinationListSubGenerator(n: int, k: int, offset: int = 0) -> Generator[List[int], None, None]:
	if k == 0:
		yield []
		return

	for i in range(offset, n - k + 1):
		for subComb in combinationListSubGenerator(n, k - 1, i + 1):
			subComb.append(i)
			yield subComb


def combinationListGenerator(n: int, k: int) -> Generator[List[int], None, None]:
	for comb in combinationListSubGenerator(n, k):
		comb.reverse()
		yield comb


def _combinations(iterable, r):
	# combinations('ABCD', 2) --> AB AC AD BC BD CD
	# combinations(range(4), 3) --> 012 013 023 123
	pool = tuple(iterable)
	n = len(pool)
	if r > n:
		return
	indices = list(range(r))
	yield tuple(pool[i] for i in indices)
	while True:
		for i in reversed(range(r)):
			if indices[i] != i + n - r:
				break
		else:
			return
		indices[i] += 1
		for j in range(i+1, r):
			indices[j] = indices[j-1] + 1
		yield tuple(pool[i] for i in indices)


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
	t0 = time()
	counter = 0
	for c in _combinationListGenerator(6, 3):
		print(c)
		counter += 1

	print(time() - t0)
	print(counter)

	for el in combinationTupleGenerator(6, 3):
		print(el)
