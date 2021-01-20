# -*- coding: utf-8 -*-

import os
import time

from cell import CellType, CellState, Cell
from move import MoveType, MoveDir, Move


class Field:

	BORDER_SYMBOL = "x"

	def __init__(self, n, cells):
		if not cells or not isinstance(cells, list) or any(not isinstance(cell, Cell) for cell in cells):
			raise ValueError(f"{cells.__name__} must be non-empty list of {Cell.__name__}s")

		if not isinstance(n, int) or n <= 0 or len(cells) % n:
			raise ValueError(f"{n.__name__} must be positive int and divide len of {cells.__name__}")

		# cells passed as linear list but represents 2D matrix n*m.
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
	def n(self):
		return self._n

	@property
	def m(self):
		return self._m

	@property
	def solvable(self):
		return self._solvable

	def getFingerprint(self):
		totalCells = len(self._cells)

		# n and all cells fully describe field.
		return hash(tuple(
			self._cells[i].getFingerprint() if i < totalCells else self.n
			for i in range(totalCells + 1)
		))

	def show(self, tab="", sep=" ", end="\n"):
		n = self.n
		m = self.m
		print(sep.join(self.BORDER_SYMBOL for _ in range(n+2)))
		for y in range(m):
			print(
				f"{tab}{self.BORDER_SYMBOL}{sep}"
				f"{sep.join(str(cell) for cell in self._cells[y*n : (y+1)*n])}"
				f"{sep}{self.BORDER_SYMBOL}",
				end=end
			)
		print(sep.join(self.BORDER_SYMBOL for _ in range(n+2)))

	@staticmethod
	def _getMovesRepr(moves):
		if moves is None:
			return None

		return "".join(str(move) for move in moves)

	def getWinMovesRepr(self):
		return self._getMovesRepr(self._winMoves)

	def getTargetCellIndex(self, pos, moveDir):
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

	def _undoMove(self, move, deadBoxes):
		prevCellIndex = self.getTargetCellIndex(self._runnerPos, MoveDir.getOpposite(move.dir_))
		self._cells[prevCellIndex].state = CellState.RUNNER

		if move.type_ == MoveType.PUSH:
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
	def _cellIsBlocked(blockedNeighbours):
		return (
			len(blockedNeighbours) > 2
			or len(blockedNeighbours) == 2
			and ((MoveDir.UP in blockedNeighbours) ^ (MoveDir.DOWN in blockedNeighbours))
		)

	def _boxIsDead(self, i, deadBoxes):
		deadNeighbours = set()
		questionBoxes = {}
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

	def isDead(self, deadBoxes):
		"""Updates deadBoxes"""
		for i, cell in enumerate(self._cells):
			if cell.state == CellState.BOX and self._boxIsDead(i, deadBoxes):
				deadBoxes.add(i)
				if self._totalBoxes - len(deadBoxes) < self._unachievedGoals:
					return True

		return False

	def showWithDeadBoxes(self, tab="", sep=" ", end="\n"):
		deadBoxes = set()

		for i, cell in enumerate(self._cells):
			if cell.state == CellState.BOX and self._boxIsDead(i, deadBoxes):
				deadBoxes.add(i)

		n = self.n
		m = self.m
		print(sep.join(self.BORDER_SYMBOL for _ in range(n+2)))
		for y in range(m):
			print(
				f"{tab}{self.BORDER_SYMBOL}{sep}"
				f"{sep.join('d' if i in deadBoxes else str(self._cells[i]) for i in range(y*n, (y+1)*n))}"
				f"{sep}{self.BORDER_SYMBOL}",
				end=end
			)
		print(sep.join(self.BORDER_SYMBOL for _ in range(n+2)))

	def solve(self, optimal=False, logInterval=None):
		if self._totalGoals > self._totalBoxes:
			self._solvable = False
		else:
			cells = [Cell(cell.type_, cell.state) for cell in self._cells]
			runnerPos = self._runnerPos
			unachievedGoals = self._unachievedGoals

			self._solve(optimal, logInterval)

			self._cells = cells
			self._runnerPos = runnerPos
			self._unachievedGoals = unachievedGoals

		return self.solvable

	def _solve(self, optimal, logInterval):
		self._solvable = False
		# Field fingerprint to distance from initial field state relation.
		checkedFields = {self.getFingerprint(): 0}
		# Box is considered to be dead if it can not be moved in future.
		deadBoxes = set()
		if self.isDead(deadBoxes):
			return

		moves = []
		nextDir = MoveDir.DEFAULT

		# Prepare set of cell indices to which it makes no sense to move the box
		deadCells = set()
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

		# Start solving
		moveCounter = 0
		logCounter = 0
		while True:
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
									print(f"{moveCounter}: {self._getMovesRepr(moves)}")

								continue

						# Else: undo move
						deadBoxes = self._undoMove(move, deadBoxes)

			else:
				# Success!
				self._winMoves = tuple(Move(move.type_, move.dir_) for move in moves)
				self._solvable = True

				if not optimal:
					return

				# There is no sense to undo only one move, at least two
				if len(moves) < 2:
					return

				lastMove = moves.pop()
				deadBoxes = self._undoMove(lastMove, deadBoxes)
				lastMove = moves.pop()
				deadBoxes = self._undoMove(lastMove, deadBoxes)
				nextDir = lastMove.dir_

			# Find next dir
			nextDir = MoveDir.getNext(nextDir)
			while nextDir is None:
				if not len(moves):
					return

				# Undo move
				lastMove = moves.pop()
				deadBoxes = self._undoMove(lastMove, deadBoxes)
				nextDir = MoveDir.getNext(lastMove.dir_)

	def showSolution(self, delay=1.0):
		if self._solvable is None:
			self.solve()

		if not self._solvable:
			print(None)

		cells = [Cell(cell.type_, cell.state) for cell in self._cells]
		runnerPos = self._runnerPos

		movesRepr = self.getWinMovesRepr()

		os.system("clear")
		print(movesRepr)
		print()
		print("Move 0")
		self.show()
		time.sleep(delay + 2)
		for i, move in enumerate(self._winMoves):
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

		self._cells = cells
		self._runnerPos = runnerPos

	def getTotalWinMoves(self):
		return None if self._winMoves is None else len(self._winMoves)
