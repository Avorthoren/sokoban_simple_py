# -*- coding: utf-8 -*-
from __future__ import annotations
from enum import Enum, auto
from typing import Optional, Self


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
	def getNext(cls, dir_: MoveDir | None) -> Self:
		if dir_ is None:
			return cls.RIGHT
		elif dir_ == cls.RIGHT:
			return cls.UP
		elif dir_ == cls.UP:
			return cls.LEFT
		elif dir_ == cls.LEFT:
			return cls.DOWN
		else:
			return None

	@classmethod
	def getOpposite(cls, dir_: MoveDir) -> Self:
		if dir_ == cls.RIGHT:
			return cls.LEFT
		elif dir_ == cls.UP:
			return cls.DOWN
		elif dir_ == cls.LEFT:
			return cls.RIGHT
		else:
			return cls.UP

	def __str__(self) -> str:
		return self.name[0]

	@classmethod
	def fromChar(cls, c: str) -> Self:
		c = c.upper()
		for member in cls:
			if member.name[0] == c:
				return member

		raise KeyError(f"No member of {cls.__name__} starts with '{c}'")


class Move:
	__slots__ = 'type_', 'dir_', 'savedDeadBoxes'

	def __init__(
		self,
		type_: MoveType,
		dir_: MoveDir,
		# Set of permanently blocked boxes BEFORE this move.
		savedDeadBoxes: Optional[set[int]] = None
	):
		self.type_ = type_
		self.dir_ = dir_
		self.savedDeadBoxes = savedDeadBoxes

	def __str__(self) -> str:
		return str(self.dir_) if self.type_ == MoveType.PUSH else str(self.dir_).lower()

	@classmethod
	def fromChar(cls, c: str) -> Self:
		dir_ = MoveDir.fromChar(c)
		type_ = MoveType.REGULAR if c.islower() else MoveType.PUSH
		return cls(type_, dir_)
