# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Union, Sequence


def f(
	a: int,
	b: Union[None, Sequence[int]] = None
) -> None:
	print(a)
	print(b)


if __name__ == "__main__":
	f(1)
	f(2, ["temp", 2])
