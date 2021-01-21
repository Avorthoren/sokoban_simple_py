# -*- coding: utf-8 -*-

from enum import Enum, auto


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
	def getNext(cls, dir_):
		if dir_ == cls.RIGHT:
			return cls.UP
		elif dir_ == cls.UP:
			return cls.LEFT
		elif dir_ == cls.LEFT:
			return cls.DOWN
		else:
			return None

	@classmethod
	def getOpposite(cls, dir_):
		if dir_ == cls.RIGHT:
			return cls.LEFT
		elif dir_ == cls.UP:
			return cls.DOWN
		elif dir_ == cls.LEFT:
			return cls.RIGHT
		else:
			return cls.UP


class Move:
	def __init__(self, type_, dir_, savedDeadBoxes=None):
		self.type_ = type_
		self.dir_ = dir_
		self.savedDeadBoxes = savedDeadBoxes

	def __str__(self):
		return self.dir_.name[0] if self.type_ == MoveType.PUSH else self.dir_.name[0].lower()


class BoxMove:
	def __init__(self, startCellIndex, dir_):
		self.startCellIndex = startCellIndex
		self.dir_ = dir_
