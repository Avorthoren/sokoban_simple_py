# -*- coding: utf-8 -*-
from __future__ import annotations
from enum import Enum, auto
from typing import Union, Sequence


class MoveType(Enum):
	REGULAR = auto()
	PUSH = auto()


class MoveDir(Enum):
	RIGHT = auto()
	UP = auto()
	LEFT = auto()
	DOWN = auto()
	DEFAULT = RIGHT

	@classmethod
	def getNext(cls, dir_: MoveDir) -> Union[MoveDir, None]:
		if dir_ == cls.RIGHT:
			return cls.UP
		elif dir_ == cls.UP:
			return cls.LEFT
		elif dir_ == cls.LEFT:
			return cls.DOWN
		else:
			return None

	@classmethod
	def getOpposite(cls, dir_: MoveDir) -> MoveDir:
		if dir_ == cls.RIGHT:
			return cls.LEFT
		elif dir_ == cls.UP:
			return cls.DOWN
		elif dir_ == cls.LEFT:
			return cls.RIGHT
		else:
			return cls.UP

	def __str__(self):
		return self.name[0]


class Move:
	def __init__(
		self,
		type_: MoveType,
		dir_: MoveDir,
		savedDeadBoxes: Union[None, Sequence[int]] = None
	):
		self.type_ = type_
		self.dir_ = dir_
		self.savedDeadBoxes = savedDeadBoxes

	def __str__(self):
		symbol = str(self.dir_)
		return symbol if self.type_ == MoveType.PUSH else symbol.lower()


class BoxMove:
	def __init__(self, startCellIndex: int, dir_: MoveDir):
		self.startCellIndex = startCellIndex
		self.dir_ = dir_

	def __eq__(self, other):
		return self.startCellIndex == other.startCellIndex and self.dir_ == other.dir_

	def __hash__(self):
		print(len(MoveDir), self.dir_.value, self.startCellIndex)
		return len(MoveDir) * self.dir_.value + self.startCellIndex

	def __str__(self):
		return f"{self.startCellIndex}{self.dir_}"

	__repr__ = __str__


if __name__ == "__main__":
	for moveDir in MoveDir:
		print(int(moveDir.value))
