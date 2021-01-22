# -*- coding: utf-8 -*-
from __future__ import annotations
from enum import Enum, auto


class CellType(Enum):
	WALL = auto()
	REGULAR = auto()
	GOAL = auto()


class CellState(Enum):
	EMPTY = auto()
	RUNNER = auto()
	BOX = auto()


class Cell:
	def __init__(self, type_: CellType, state: CellState):
		if type_ == CellType.WALL and state != CellState.EMPTY:
			raise ValueError(f"{CellType.WALL.name} must be {CellState.EMPTY.name}")

		self.type_ = type_
		self.state = state

	def __hash__(self):
		if self.type_ == CellType.WALL:
			return 1
		elif self.state == CellState.EMPTY:
			return 3 if self.type_ == CellType.GOAL else 2
		elif self.state == CellState.BOX:
			return 5 if self.type_ == CellType.GOAL else 4
		elif self.state == CellState.RUNNER:
			return 7 if self.type_ == CellType.GOAL else 6
		else:
			return 0

	def __copy__(self):
		cls = self.__class__
		copy_ = cls.__new__(cls)

		copy_.type_ = self.type_
		copy_.state = self.state

		return copy_

	def copy(self) -> Cell:
		return self.__copy__()

	def isGoal(self) -> bool:
		return self.type_ == CellType.GOAL

	def isRegular(self) -> bool:
		return self.type_ == CellType.REGULAR

	def isWall(self) -> bool:
		return self.type_ == CellType.WALL

	def hasBox(self) -> bool:
		return self.state == CellState.BOX

	def hasRunner(self) -> bool:
		return self.state == CellState.RUNNER

	def isPassable(self) -> bool:
		return not (self.isWall() or self.hasBox())

	@classmethod
	def empty(cls) -> Cell:
		return cls(CellType.REGULAR, CellState.EMPTY)

	@classmethod
	def wall(cls) -> Cell:
		return cls(CellType.WALL, CellState.EMPTY)

	@classmethod
	def goal(cls) -> Cell:
		return cls(CellType.GOAL, CellState.EMPTY)

	@classmethod
	def box(cls) -> Cell:
		return cls(CellType.REGULAR, CellState.BOX)

	@classmethod
	def runner(cls) -> Cell:
		return cls(CellType.REGULAR, CellState.RUNNER)

	@classmethod
	def boxOnGoal(cls) -> Cell:
		return cls(CellType.GOAL, CellState.BOX)

	@classmethod
	def runnerOnGoal(cls) -> Cell:
		return cls(CellType.GOAL, CellState.RUNNER)

	def __str__(self):
		if self.type_ == CellType.WALL:
			return "x"
		elif self.state == CellState.EMPTY:
			return "!" if self.type_ == CellType.GOAL else " "
		elif self.state == CellState.BOX:
			return "O" if self.type_ == CellType.GOAL else "o"
		elif self.state == CellState.RUNNER:
			return "R" if self.type_ == CellType.GOAL else "r"
		else:
			return "?"


if __name__ == "__main__":
	c1 = Cell(CellType.GOAL, CellState.EMPTY)
	c2 = c1.copy()
	c1.state = CellState.BOX
	print(c1, c2)

