# -*- coding: utf-8 -*-

import os
import time
from typing import Iterable, Optional, Sequence, Callable

from cell import CellType, CellState, Cell
from move import MoveType, MoveDir, Move


class Field:

	_BORDER_SYMBOL = "x"

	__slots__ = (
		# SOURCE INPUT VALUES

		# : tuple[Cell]
		# All field cells.
		'_cells',
		# : int
		# Number of field columns.
		'_n',

		# CALCULATED INPUT VALUES

		# : int
		# Number of field rows.
		'_m',
		# : int
		# Total number of cells which have to be covered with boxes.
		'_totalGoals',
		# : int
		# Total number of boxes on the field.
		'_totalBoxes',

		# CALCULATED VALUES

		# : tuple[MoveDir] | None
		# Sequence of moves that solve the puzzle found in the last call of the
		# `self._solve`.
		'_winMoves',
		# : bool | None
		# Is None before `self._solve` was called.
		'_solvable',
		# : int
		# Position of the runner in `self._cells`.
		# Mutated by `self._solve`, but restores its value in the end.
		'_runnerPos',
		# : int
		# Number of cells that have to be covered with boxes but aren't ATM.
		# Mutated by `self._solve`, but restores its value in the end.
		'_unachievedGoals',
	)

	def __init__(
		self,
		n: int,  # number of field columns
		cells: Iterable[Cell]
	):
		# cells passed as linear 'list' but represents 2D matrix n*m.
		if not isinstance(cells, tuple):
			cells = tuple(cells)
		if not cells or any(not isinstance(cell, Cell) for cell in cells):
			raise ValueError(f"`cells` must be non-empty iterable of {Cell.__name__}s")

		if not isinstance(n, int) or n <= 0 or len(cells) % n:
			raise ValueError(f"`n` must be positive int and divide len of `cells`")

		self._cells = cells
		self._n = n
		self._m = len(cells) // n
		self._totalGoals = 0
		self._unachievedGoals = 0
		self._totalBoxes = 0
		hasRunner = False
		for i, cell in enumerate(cells):
			if cell.state == CellState.RUNNER:
				if hasRunner:
					raise ValueError("Field must have exactly one runner")
				hasRunner = True
				self._runnerPos = i
			elif cell.state == CellState.BOX:
				self._totalBoxes += 1

			if cell.type_ == CellType.GOAL:
				self._totalGoals += 1
				if cell.state != CellState.BOX:
					self._unachievedGoals += 1

		if not hasRunner:
			raise ValueError("Field must have runner")

		self._winMoves = None
		self._solvable = None

	@property
	def n(self) -> int:
		return self._n

	@property
	def m(self) -> int:
		return self._m

	@property
	def solvable(self) -> bool:
		if self._solvable is None:
			self.solve()
		return self._solvable

	def getFingerprint(self) -> int:
		"""Kinda like hash of the field."""
		totalCells = len(self._cells)

		# n and all cells fully describe field.
		return hash(tuple(
			self._cells[i].getFingerprint() if i < totalCells else self.n
			for i in range(totalCells + 1)
		))

	@staticmethod
	def _cellStrGen(cells: Sequence[Cell], start: int, end: int) -> Iterable[str]:
		"""Generate string representations for cells from `start` to `end`."""
		return (str(cells[i]) for i in range(start, end))

	@staticmethod
	def _cellWithDeadGenFactory(deadBoxes: set[int]) -> Callable[[Sequence[Cell], int, int], Iterable[str]]:
		"""Convenience factory.

		Returns function with same signature as `_cellStrGen` (but taking into
		consideration `deadBoxes`, marking them as 'd') so that they can be used
		in the same context.
		"""
		def _cellWithDeadGen(cells: Sequence[Cell], start: int, end: int) -> Iterable[str]:
			return (
				'd' if i in deadBoxes else str(cells[i])
				for i in range(start, end)
			)

		return _cellWithDeadGen

	def show(
		self,
		tab: str = "",    # tabulation from the left edge of the console.
		sep: str = " ",   # cells separator
		end: str = "\n",  # rows separator
		deadBoxes: Optional[set[int]] = None
	) -> None:
		"""Print field. Pass `deadBoxes` to mark them with 'd'."""
		n = self.n
		m = self.m
		# Surround field with `self._BORDER_SYMBOL`s.
		ceil_floor = tab + sep.join(self._BORDER_SYMBOL for _ in range(n + 2))
		print(ceil_floor)

		rowGen = self._cellStrGen if deadBoxes is None else self._cellWithDeadGenFactory(deadBoxes)
		for y in range(m):
			print(
				f"{tab}{self._BORDER_SYMBOL}{sep}"
				f"{sep.join(rowGen(self._cells, start=y*n, end=(y+1)*n))}"
				f"{sep}{self._BORDER_SYMBOL}",
				end=end
			)

		print(ceil_floor)

	def showWithDeadBoxes(
		self,
		tab: str = "",
		sep: str = " ",
		end: str = "\n"
	) -> None:
		"""`self.show` with precalculating dead boxes."""
		deadBoxes: set[int] = set()
		for i, cell in enumerate(self._cells):
			if (
				cell.state == CellState.BOX
				and i not in deadBoxes
				and self._boxIsDead(i, deadBoxes)
			):
				deadBoxes.add(i)

		self.show(tab, sep, end, deadBoxes)

	@staticmethod
	def _getMovesRepr(moves: Iterable[Move] | None) -> str | None:
		"""Get compact moves string representation."""
		if moves is None:
			return None

		return "".join(str(move) for move in moves)

	def getWinMovesRepr(self) -> str | None:
		return self._getMovesRepr(self._winMoves)

	def getTargetCellIndex(self, pos: int, moveDir: MoveDir) -> int | None:
		"""Get index of the cell that is connected to the cell with given
		index `pos` by given move `moveDir`.
		"""
		y, x = divmod(pos, self.n)

		if moveDir == MoveDir.RIGHT:
			x += 1
		elif moveDir == MoveDir.UP:
			y -= 1
		elif moveDir == MoveDir.LEFT:
			x -= 1
		elif moveDir == MoveDir.DOWN:
			y += 1

		if not (0 <= x < self.n and 0 <= y < self.m):
			return None

		return y * self.n + x

	def _undoMove(self, move: Move, deadBoxes: set[int]) -> set[int]:
		"""Reverse the move and return set of dead boxes after that."""
		prevCellIndex = self.getTargetCellIndex(self._runnerPos, MoveDir.getOpposite(move.dir_))
		self._cells[prevCellIndex].state = CellState.RUNNER

		if move.type_ == MoveType.PUSH:
			# Restore box position as well.
			followCellIndex = self.getTargetCellIndex(self._runnerPos, move.dir_)
			self._cells[followCellIndex].state = CellState.EMPTY
			self._cells[self._runnerPos].state = CellState.BOX
			if self._cells[self._runnerPos].type_ == CellType.GOAL:
				self._unachievedGoals -= 1
			if self._cells[followCellIndex].type_ == CellType.GOAL:
				self._unachievedGoals += 1
		else:
			self._cells[self._runnerPos].state = CellState.EMPTY

		self._runnerPos = prevCellIndex

		return deadBoxes if move.savedDeadBoxes is None else move.savedDeadBoxes

	@staticmethod
	def _cellIsBlocked(blockedNeighbours: set[MoveDir]) -> bool:
		"""Cell is blocked if box can't be moved from it without emptying
		at least one of `blockedNeighbours`.
		"""
		return (
			len(blockedNeighbours) > 2
			or len(blockedNeighbours) == 2
			and ((MoveDir.UP in blockedNeighbours) ^ (MoveDir.DOWN in blockedNeighbours))
		)

	def _boxIsDead(
		self,
		i: int,  # cell index
		deadBoxes: set[int]
	) -> bool:
		"""Box is dead if it can't be moved in the future."""
		# It shouldn't be called under this conditions
		# if i in deadBoxes: return True

		deadNeighbours: set[MoveDir] = set()
		questionBoxes: dict[int, MoveDir] = {}
		for moveDir in MoveDir:
			targetCellIndex = self.getTargetCellIndex(i, moveDir)
			if targetCellIndex is None or self._cells[targetCellIndex].type_ == CellType.WALL:
				deadNeighbours.add(moveDir)
			elif self._cells[targetCellIndex].state == CellState.BOX:
				if targetCellIndex in deadBoxes:
					deadNeighbours.add(moveDir)
				else:
					questionBoxes[targetCellIndex] = moveDir

		if self._cellIsBlocked(deadNeighbours):
			return True

		if len(deadNeighbours) + len(questionBoxes) < 2:
			return False

		deadBoxesCopy = deadBoxes.copy()
		# For now, consider input box as dead
		deadBoxesCopy.add(i)
		for cnt, (targetCellIndex, moveDir) in enumerate(questionBoxes.items()):
			if self._boxIsDead(targetCellIndex, deadBoxesCopy):
				deadNeighbours.add(moveDir)
				if self._cellIsBlocked(deadNeighbours):
					return True

			if len(deadNeighbours) + len(questionBoxes) - (cnt + 1) < 2:
				break

		return False

	def isDead(self, deadBoxes: Optional[set[int]] = None) -> bool:
		"""Check if field is unsolvable from current position.
		Updates `deadBoxes` if it was passed into this method.
		"""
		if deadBoxes is None:
			deadBoxes: set[int] = set()

		if self._totalBoxes - len(deadBoxes) < self._unachievedGoals:
			return True

		for i, cell in enumerate(self._cells):
			if cell.state != CellState.BOX or i in deadBoxes:
				continue

			if self._boxIsDead(i, deadBoxes):
				deadBoxes.add(i)
				if self._totalBoxes - len(deadBoxes) < self._unachievedGoals:
					return True

		return False

	def solve(
		self,
		optimal: Optional[bool] = False,
		logInterval: Optional[int] = None
	) -> bool:
		"""Solve the puzzle and save the answer:
		win moves and if it's solvable.
		Return if it's solvable.

		If `optimal` is True - doesn't stop after finding the first answer,
		searches for shortest solution until all possibilities checked.

		If `logInterval` is not None - shows currently checked moves list
		every `logInterval` 'search-nodes'. If additionally `optimal` is True -
		shows each found solution which is better than previous one.
		"""
		if self._totalGoals > self._totalBoxes:
			# Theoretically impossible: not enough boxes.
			self._solvable = False
			return self._solvable

		# Save initial values.
		cells = tuple(Cell(cell.type_, cell.state) for cell in self._cells)
		runnerPos = self._runnerPos
		unachievedGoals = self._unachievedGoals

		self._solve(optimal, logInterval)

		# Restore initial values.
		self._cells = cells
		self._runnerPos = runnerPos
		self._unachievedGoals = unachievedGoals

		return self._solvable

	def _getDeadCells(self) -> set[int]:
		"""Prepare cells indices to which it makes no sense to move the box."""
		deadCells: set[int] = set()
		for i, cell in enumerate(self._cells):
			# Dead cell is REGULAR cell that have > 2 WALL neighbours or 2
			# adjacent WALL neighbours (where border must be treated as WALL)
			if cell.type_ == CellType.REGULAR:
				wallNeighbours = set()
				for moveDir in MoveDir:
					targetCellIndex = self.getTargetCellIndex(i, moveDir)
					if targetCellIndex is None or self._cells[targetCellIndex].type_ == CellType.WALL:
						wallNeighbours.add(moveDir)

				if self._cellIsBlocked(wallNeighbours):
					deadCells.add(i)

		return deadCells

	def _solve(self, optimal: bool, logInterval: int | None):
		"""Main part of `self.solve`: check it for args description.
		Uses back-track search.
		"""
		self._solvable = False
		self._winMoves = None
		# Field fingerprint to distance from initial field state relation.
		checkedFields: dict[int, int] = {self.getFingerprint(): 0}
		# Box is considered to be dead if it can not be moved in the future.
		deadBoxes: set[int] = set()
		if self.isDead(deadBoxes):
			return

		moves: list[Move] = []
		nextDir: None | MoveDir = None
		deadCells = self._getDeadCells()

		# Start solving
		moveCounter = 0
		logCounter = 0
		while True:
			# General back-track case.
			# Find next dir.
			# On first iteration it will yield MoveDir.RIGHT
			nextDir = MoveDir.getNext(nextDir)
			while nextDir is None:
				if not len(moves):
					return
				# Undo move
				lastMove = moves.pop()
				deadBoxes = self._undoMove(lastMove, deadBoxes)
				nextDir = MoveDir.getNext(lastMove.dir_)
			nextDir: MoveDir

			if self._unachievedGoals:
				# Try move.
				targetCellIndex = self.getTargetCellIndex(self._runnerPos, nextDir)
				# Not edge of the field
				if targetCellIndex is not None:
					targetCell = self._cells[targetCellIndex]
					isPassable = targetCell.isPassable()
					followCellIndex = self.getTargetCellIndex(targetCellIndex, nextDir)
					# Either passable cell, or box followed by passable cell
					# and non-dead cell
					if (
						isPassable
						or targetCell.state == CellState.BOX
						and followCellIndex is not None
						and self._cells[followCellIndex].isPassable()
						and followCellIndex not in deadCells
					):
						# Do move
						move = Move(MoveType.REGULAR if isPassable else MoveType.PUSH, nextDir)
						targetCell.state = CellState.RUNNER
						self._cells[self._runnerPos].state = CellState.EMPTY
						if not isPassable:
							self._cells[followCellIndex].state = CellState.BOX
							if targetCell.type_ == CellType.GOAL:
								self._unachievedGoals += 1
							if self._cells[followCellIndex].type_ == CellType.GOAL:
								self._unachievedGoals -= 1

						self._runnerPos = targetCellIndex

						# We should not repeat field state unless we've achieved
						# it from lower distance than previous time.
						# TODO: optimal solution search must be reworked:
						#  all fields fingerprints from previous found solution
						#  should be stored somewhere. If we hit some of this
						#  fields, _winMoves must be updated, then undo two
						#  last moves.
						fingerPrint = self.getFingerprint()
						if (
							fingerPrint not in checkedFields
							or optimal
							and checkedFields[fingerPrint] > len(moves) + 1
						):
							checkedFields[fingerPrint] = len(moves)
							isDead = False
							if move.type_ == MoveType.PUSH:
								move.savedDeadBoxes = deadBoxes.copy()
								isDead = self.isDead(deadBoxes)

							if not isDead:
								moves.append(move)
								nextDir = MoveDir.DEFAULT

								moveCounter += 1
								logCounter += 1
								if logInterval is not None and logCounter == logInterval:
									logCounter = 0
									print(f"{moveCounter:_}: {self._getMovesRepr(moves)}")

								continue

						# Else: undo move
						deadBoxes = self._undoMove(move, deadBoxes)

			else:
				# SUCCESS!
				result = self._handleSuccess(moves, deadBoxes, optimal, logInterval)
				# Check explicitly for `True`, because otherwise it will be
				# a tuple, which is also will be casted to True.
				if result is True:
					return
				lastMove, deadBoxes, nextDir = result

	def _checkStep(
		self,
		targetCellIndex: int,
		nextDir: MoveDir,
		deadCells: set[int],
		checkedFields: dict[int, int],
		moves: list[Move],
		deadBoxes: set[int],
		optimal: bool,
		logInterval: int | None,
		moveCounter: int,
		logCounter: int
	) -> None | tuple[MoveDir, set[int], int, int]:
		"""Main part of `self._solve`: check for args description.

		Tries to move runner to `targetCellIndex`, checks if it makes sense
		to continue this 'line' of moves.

		Returns updated values of:
		`nextDir`,
		`deadBoxes`,
		`moveCounter`,
		`logCounter`
		"""
		targetCell = self._cells[targetCellIndex]
		isPassable = targetCell.isPassable()
		followCellIndex = self.getTargetCellIndex(targetCellIndex, nextDir)
		# Either passable cell, or box followed by passable cell
		# and non-dead cell
		if not (
			isPassable
			or targetCell.state == CellState.BOX
			and followCellIndex is not None
			and self._cells[followCellIndex].isPassable()
			and followCellIndex not in deadCells
		):
			return None

		# Do move
		move = Move(MoveType.REGULAR if isPassable else MoveType.PUSH, nextDir)
		targetCell.state = CellState.RUNNER
		self._cells[self._runnerPos].state = CellState.EMPTY
		if not isPassable:
			self._cells[followCellIndex].state = CellState.BOX
			if targetCell.type_ == CellType.GOAL:
				self._unachievedGoals += 1
			if self._cells[followCellIndex].type_ == CellType.GOAL:
				self._unachievedGoals -= 1

		self._runnerPos = targetCellIndex

		# We should not repeat field state unless we've achieved
		# it from lower distance than previous time.
		# TODO: optimal solution search must be reworked:
		#  all fields fingerprints from previous found solution
		#  should be stored somewhere. If we hit some of this
		#  fields, _winMoves must be updated, then undo two
		#  last moves.
		fingerPrint = self.getFingerprint()
		if (
			fingerPrint not in checkedFields
			or optimal
			and checkedFields[fingerPrint] > len(moves) + 1
		):
			checkedFields[fingerPrint] = len(moves)
			isDead = False
			if move.type_ == MoveType.PUSH:
				move.savedDeadBoxes = deadBoxes.copy()
				isDead = self.isDead(deadBoxes)

			if not isDead:
				# 'Positive' case: add new move.
				moves.append(move)
				nextDir = MoveDir.DEFAULT

				moveCounter += 1
				logCounter += 1
				if logInterval is not None and logCounter == logInterval:
					logCounter = 0
					print(f"{moveCounter:_}: {self._getMovesRepr(moves)}")

				return nextDir, deadBoxes, moveCounter, logCounter

		# 'Negative' case otherwise: undo 'bad' move.
		deadBoxes = self._undoMove(move, deadBoxes)

		return nextDir, deadBoxes, moveCounter, logCounter

	def _handleSuccess(
		self,
		moves: list[Move],
		deadBoxes: set[int],
		optimal: bool,
		logInterval: Optional[float]
	) -> bool | tuple[Move, set[int], MoveDir]:
		"""Handle 'success-branch' if `self._solve`.

		Returns either True (which indicates that we are finished)
		or updated values of:
		`lastMove`,
		`deadBoxes`,
		`nextDir` - check `self._solve` for details.
		"""
		self._solvable = True
		if self._winMoves is None or len(moves) < len(self._winMoves):
			self._winMoves = tuple(Move(move.type_, move.dir_) for move in moves)
			if logInterval is not None:
				print(f"SOLUTION IN {len(self._winMoves)} MOVES FOUND:")
				print(self.getWinMovesRepr())
				print()

		if not optimal:
			return True

		# There is no sense to undo only one move, at least two, because,
		# obviously, two different moves can't get us to the win from the
		# same position.
		if len(moves) < 2:
			return True

		lastMove = moves.pop()
		deadBoxes = self._undoMove(lastMove, deadBoxes)
		lastMove = moves.pop()
		deadBoxes = self._undoMove(lastMove, deadBoxes)
		nextDir = lastMove.dir_

		return lastMove, deadBoxes, nextDir

	def showAnimation(
		self,
		moves: Iterable[Move] | str,
		# Delay before making each move, except the first one:
		# delay will be 2 seconds longer.
		delay: float = 1.0
	) -> None:
		"""Show animation by given list of moves directions.
		You can pass moves in string format. Example:
		'ruuudlr'
		It means: right, up, up, up, down, left, right
		"""
		if isinstance(moves, str):
			movesRepr = moves
			moves = tuple(Move.fromChar(c) for c in moves)
		else:
			movesRepr = self._getMovesRepr(moves)

		# Save initial values.
		cells = tuple(Cell(cell.type_, cell.state) for cell in self._cells)
		runnerPos = self._runnerPos
		unachievedGoals = self._unachievedGoals

		os.system("clear")
		print(movesRepr)
		print()
		print("Move 0")
		self.show()
		time.sleep(delay + 2)
		for i, move in enumerate(moves, start=1):
			targetCellIndex = self.getTargetCellIndex(self._runnerPos, move.dir_)
			targetCell = self._cells[targetCellIndex]
			if move.type_ == MoveType.PUSH:
				followCellIndex = self.getTargetCellIndex(targetCellIndex, move.dir_)
				followCell = self._cells[followCellIndex]
				followCell.state = CellState.BOX

			targetCell.state = CellState.RUNNER
			self._cells[self._runnerPos].state = CellState.EMPTY
			self._runnerPos = targetCellIndex

			os.system("clear")
			print(movesRepr)
			print()
			print(f"Move {i}")
			self.show()
			time.sleep(delay)

		# Restore initial values.
		self._cells = cells
		self._runnerPos = runnerPos
		self._unachievedGoals = unachievedGoals

	def showSolution(self, delay: float = 1.0):
		if self._solvable is None:
			self.solve()

		if not self._solvable:
			print(None)

		self.showAnimation(self._winMoves, delay)

	def getTotalWinMoves(self):
		return None if self._winMoves is None else len(self._winMoves)
