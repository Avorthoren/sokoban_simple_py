# -*- coding: utf-8 -*-

from enum import Enum, auto
from typing import Self


class CellType(Enum):
	WALL = auto()
	REGULAR = auto()
	GOAL = auto()


class CellState(Enum):
	EMPTY = auto()
	RUNNER = auto()
	BOX = auto()


class Cell:
	"""Sokoban board cell class."""
	__slots__ = 'type_', 'state'

	def __init__(self, type_: CellType, state: CellState):
		if type_ == CellType.WALL and state != CellState.EMPTY:
			raise ValueError(f"{CellType.WALL.name} must be {CellState.EMPTY.name}")

		self.type_ = type_
		self.state = state

	def getFingerprint(self) -> int:
		"""Kinda like hash of the cell."""
		if self.type_ == CellType.WALL:
			return 1
		elif self.state == CellState.EMPTY:
			return 3 if self.type_ == CellType.GOAL else 2
		elif self.state == CellState.BOX:
			return 5 if self.type_ == CellType.GOAL else 4
		elif self.state == CellState.RUNNER:
			return 7 if self.type_ == CellType.GOAL else 6
		else:
			# Should never happen.
			return 0

	def isPassable(self) -> bool:
		return self.type_ != CellType.WALL and self.state != CellState.BOX

	@classmethod
	def empty(cls) -> Self:
		return cls(CellType.REGULAR, CellState.EMPTY)

	@classmethod
	def wall(cls) -> Self:
		return cls(CellType.WALL, CellState.EMPTY)

	@classmethod
	def goal(cls) -> Self:
		return cls(CellType.GOAL, CellState.EMPTY)

	@classmethod
	def box(cls) -> Self:
		return cls(CellType.REGULAR, CellState.BOX)

	@classmethod
	def runner(cls) -> Self:
		return cls(CellType.REGULAR, CellState.RUNNER)

	@classmethod
	def boxOnGoal(cls) -> Self:
		return cls(CellType.GOAL, CellState.BOX)

	@classmethod
	def runnerOnGoal(cls) -> Self:
		return cls(CellType.GOAL, CellState.RUNNER)

	def __str__(self) -> str:
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
