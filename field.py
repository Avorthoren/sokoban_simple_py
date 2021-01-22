# -*- coding: utf-8 -*-
"""
fp - fingerprint

fp вычисляем как hash(упорядоченный список индексов клеток всех ящиков + индекс
компоненты связности бегуна).

Создаём словарь бегунов {int - id: Field}. Помещаем туда первого с rawCopy
исходного поля. Вычисляем fp, список доступных ходов и список мёртвых ящиков.
Если поле мёртвое => конец.

Храним словарь посещённых состояний:
{int - fp: BoxMove | None - ход, который привёл к этому состоянию}
Вначале там {fp(стартовое состояние): None}

Условие 0:
Перед выполнением хода нужно убедиться, что либо конечная клетка ящика - цель,
либо не мёртвая, либо unachievedGoals <= totalBoxes - (totalDeadBoxes + 1).
Для этого нужно иметь множество мёртвых клеток (общее для всех и постоянное).

После выполнения хода нужно проверить:
1. Не посещено ли это поле. Для этого нужно иметь словарь компонент связности:
   {int - cell index: int - component index}, во время вычисления которой мы
   также вычислим все возможные PUSH ходы, оставив только те из них, которые
   принадлежат компоненте связности бегуна.
2. Не является ли поле мёртвым. Для этого нужно иметь множество мёртвых ящиков,
   которое, возможно, обновится при анализе.

ПОИСК_PUSH_МАРШРУТА (_solve):
	Итерация пока есть бегуны:
		Итерация по бегунам (for runnerID in tuple(runners): ...):
			Если unachievedGoals == 0:
				return runners[runnerID]._fingerPrint

			deleteRunnerID = runnerID
			Итерация по возможным PUSH ходам:
				Если ход не удовлетвоярет условию 0:
					continue
				Если это не последний ход и список мёртвых ящиков ещё не сохранён:
					Сохраняем список мёртвых ящиков
				Делаем ход
				Если ход не удовлетворяет условию 1:
					Отменить ход
					continue
				Помещаем поле в словарь посещённых
				Если ход не удовлетворяет условию 2:
					Отменить ход
					continue
				deleteRunnerID = None
				Если это не последний ход:
					Добавить нового бегуна, сделав rawCopy поля последнего и
					установив туда сохранённый список мёртвых ящиков.
					runnerID = next(runnerIDGenerator)
					deleteRunnerID = runnerID

			Удалить бегуна deleteRunner, если он не None

	return None


ПОСТРОЕНИЕ_MOVE_МАРШРУТА (_findWinMoves):
	Построить список PUSH ходов в обратном порядке, последовательно делая PUSH
	ход обратный последнему из текущего состояния, пока не прийдём к состояния
	с последним ходом None. При этом, нам не важны положения бегуна.
	Из исходного состояния поля итерируем по PUSH ходам. Для каждого PUSH хода
	ищем список MOVE ходов поиском в ширину. Готово: вы великолепны.
"""

import copy
import os
import time

from cell import CellType, CellState, Cell
from move import MoveType, MoveDir, Move, BoxMove
import utils


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
		self._unachievedGoals = 0
		self._totalBoxes = 0

		totalGoals = 0
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
				totalGoals += 1
				if cell.state != CellState.BOX:
					self._unachievedGoals += 1

		if not hasRunner:
			raise ValueError("Field must have runner")

		if totalGoals > self._totalBoxes:
			raise ValueError(f"Number of total goals must be at most number of total boxes")

		self._fingerprint = None
		self._winMoves = None
		self._solvable = None
		self._runnerComponentID = None
		self._boxMoves = None
		self._deadBoxes = set()
		self._totalStatesChecked = 0

	@property
	def n(self):
		return self._n

	@property
	def m(self):
		return self._m

	@property
	def solvable(self):
		return self._solvable

	def _rawCopy(self):
		cls = self.__class__
		copy_ = cls.__new__(cls)

		copy_._cells = tuple(cell.copy() for cell in self._cells)
		copy_._n = self._n
		copy_._m = self._m
		copy_._unachievedGoals = self._unachievedGoals
		copy_._totalBoxes = self._totalBoxes
		copy_._runnerPos = self._runnerPos
		copy_._fingerprint = None
		copy_._winMoves = None
		copy_._solvable = None
		copy_._runnerComponentID = None
		copy_._boxMoves = None
		copy_._deadBoxes = set()
		copy_._totalStatesChecked = 0

		return copy_

	def _fingerprintGen(self):
		for i, cell in enumerate(self._cells):
			if cell.state == CellState.BOX:
				yield i

		yield self._runnerComponentID

	def _getFingerprint(self):
		# All box positions and runner connectivity component
		return hash(tuple(val for val in self._fingerprintGen()))

	def _hashGen(self):
		for cell in self._cells:
			yield hash(cell)

		yield self._n

	def __hash__(self):
		# n and all cells fully describe field
		return hash(tuple(val for val in self._hashGen()))

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

	# TODO: REWORK
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

	def _analyze(self):
		"""Find runner component index, fingerprint and all possible box moves."""
		# Map of passable cells that were already checked
		checkedCells = {}
		componentIDGen = utils.idGenerator()
		# These are different runners, not the ones used in _solve
		runners = {}
		runnerIDGen = utils.idGenerator()
		# Map of possible box moves for each component
		boxMoves = {}

		for i, cell in enumerate(self._cells):
			if self._runnerComponentID is not None:
				break

			if cell.isPassable() and i not in checkedCells:
				# This will be new connectivity component
				componentID = next(componentIDGen)
				checkedCells[i] = componentID
				runners[next(runnerIDGen)] = i
				boxMoves[componentID] = []

				while runners:
					for runnerID in tuple(runners):
						runnerPos = runners[runnerID]
						runnerNotMoved = True
						# Move-runner aligned with push-runner
						if runnerPos == self._runnerPos:
							self._runnerComponentID = componentID

						for moveDir in MoveDir:
							targetCellIndex = self.getTargetCellIndex(runnerPos, moveDir)
							if targetCellIndex is None:
								continue

							targetCell = self._cells[targetCellIndex]
							if targetCell.isPassable() and targetCellIndex not in checkedCells:
								# Mark cell as checked and move further
								checkedCells[targetCellIndex] = componentID
								if runnerNotMoved:
									runnerNotMoved = False
									runners[runnerID] = targetCellIndex
								else:
									runners[next(runnerIDGen)] = targetCellIndex

							elif targetCell.state == CellState.BOX:
								# Update available box moves
								followCellIndex = self.getTargetCellIndex(targetCellIndex, moveDir)
								if followCellIndex is None:
									continue

								followCell = self._cells[followCellIndex]
								if followCell.isPassable():
									boxMoves[componentID].append(BoxMove(targetCellIndex, moveDir))

						if runnerNotMoved:
							del runners[runnerID]

		if self._runnerComponentID is None:
			# This should never happen
			raise RuntimeError("Push-runner not found in any connectivity component")

		self._fingerprint = self._getFingerprint()

		print("Checked fields: ", checkedCells)
		print("Box moves: ", boxMoves)
		print("Runner component: ", self._runnerComponentID)
		print("Fingerprint: ", self._fingerprint)

		self._boxMoves = boxMoves[self._runnerComponentID]

	# def solve(self, logInterval=None):
	# 	if self._solvable is None:
	# 		self._solvable = False
	# 	else:
	# 		return self._solvable
	#
	# 	startField = self._rawCopy()
	# 	startField._analyze()
	# 	checkedFields = {startField._fingerprint: None}
	# 	if startField.isDead():
	# 		return self._solvable  # False
	#
	# 	endFieldFingerPrint = self._solve(checkedFields, logInterval)
	# 	if endFieldFingerPrint is None:
	# 		return self._solvable
	#
	# 	self._solvable = True  # False
	#
	# 	# Запустить _findWinMoves, передав туда словарь посещённых состояний
	# 	# и fp конечного поля.
	# 	self._findWinMoves(checkedFields, endFieldFingerPrint)
	#
	# 	return self._solvable  # True
	#
	# def _solve(self, logInterval):
	# 	self._solvable = False
	# 	# Field fingerprint to distance from initial field state relation.
	# 	checkedFields = {self.getFingerprint(): 0}
	# 	# Box is considered to be dead if it can not be moved in future.
	# 	deadBoxes = set()
	# 	if self.isDead(deadBoxes):
	# 		return
	#
	# 	moves = []
	# 	nextDir = MoveDir.DEFAULT
	#
	# 	# Prepare set of cell indices to which it makes no sense to move the box
	# 	deadCells = set()
	# 	for i, cell in enumerate(self._cells):
	# 		# Dead cell is REGULAR cell that have > 2 WALL neighbours or 2
	# 		# adjacent WALL neighbours (where border must be treated as WALL)
	# 		if cell.type_ == CellType.REGULAR:
	# 			wallNeighbours = set()
	# 			for moveDir in MoveDir:
	# 				targetCellIndex = self.getTargetCellIndex(i, moveDir)
	# 				if targetCellIndex is None or self._cells[targetCellIndex].type_ == CellType.WALL:
	# 					wallNeighbours.add(moveDir)
	#
	# 			if self._cellIsBlocked(wallNeighbours):
	# 				deadCells.add(i)
	#
	# 	# Start solving
	# 	moveCounter = 0
	# 	logCounter = 0
	# 	while True:
	# 		if self._unachievedGoals:
	# 			# Try move.
	# 			targetCellIndex = self.getTargetCellIndex(self._runnerPos, nextDir)
	# 			# Not edge of the field
	# 			if targetCellIndex is not None:
	# 				targetCell = self._cells[targetCellIndex]
	# 				isPassable = targetCell.isPassable()
	# 				followCellIndex = self.getTargetCellIndex(targetCellIndex, nextDir)
	# 				# Either passable cell, or box followed by passable cell
	# 				# and non-dead cell
	# 				if (
	# 					isPassable
	# 					or targetCell.state == CellState.BOX
	# 					and followCellIndex is not None
	# 					and self._cells[followCellIndex].isPassable()
	# 					and followCellIndex not in deadCells
	# 				):
	# 					# Do move
	# 					move = Move(MoveType.REGULAR if isPassable else MoveType.PUSH, nextDir)
	# 					targetCell.state = CellState.RUNNER
	# 					self._cells[self._runnerPos].state = CellState.EMPTY
	# 					if not isPassable:
	# 						self._cells[followCellIndex].state = CellState.BOX
	# 						if targetCell.type_ == CellType.GOAL:
	# 							self._unachievedGoals += 1
	# 						if self._cells[followCellIndex].type_ == CellType.GOAL:
	# 							self._unachievedGoals -= 1
	#
	# 					self._runnerPos = targetCellIndex
	#
	# 					# We should not repeat field state unless we've achieved
	# 					# it from lower distance than previous time.
	# 					# TODO: optimal solution search must be reworked:
	# 					#  all fields fingerprints from previous found solution
	# 					#  should be stored somewhere. If we hit some of this
	# 					#  fields, _winMoves must be updated, then undo two
	# 					#  last moves.
	# 					fingerPrint = self.getFingerprint()
	# 					if (
	# 						fingerPrint not in checkedFields
	# 						or checkedFields[fingerPrint] > len(moves) + 1
	# 					):
	# 						checkedFields[fingerPrint] = len(moves)
	# 						isDead = False
	# 						if move.type_ == MoveType.PUSH:
	# 							move.savedDeadBoxes = deadBoxes.copy()
	# 							isDead = self.isDead(deadBoxes)
	#
	# 						if not isDead:
	# 							moves.append(move)
	# 							nextDir = MoveDir.DEFAULT
	#
	# 							moveCounter += 1
	# 							logCounter += 1
	# 							if logInterval is not None and logCounter == logInterval:
	# 								logCounter = 0
	# 								print(f"{moveCounter}: {self._getMovesRepr(moves)}")
	#
	# 							continue
	#
	# 					# Else: undo move
	# 					deadBoxes = self._undoMove(move, deadBoxes)
	#
	# 		else:
	# 			# Success!
	# 			self._winMoves = tuple(Move(move.type_, move.dir_) for move in moves)
	# 			self._solvable = True
	#
	# 			if not optimal:
	# 				return
	#
	# 			# There is no sense to undo only one move, at least two
	# 			if len(moves) < 2:
	# 				return
	#
	# 			lastMove = moves.pop()
	# 			deadBoxes = self._undoMove(lastMove, deadBoxes)
	# 			lastMove = moves.pop()
	# 			deadBoxes = self._undoMove(lastMove, deadBoxes)
	# 			nextDir = lastMove.dir_
	#
	# 		# Find next dir
	# 		nextDir = MoveDir.getNext(nextDir)
	# 		while nextDir is None:
	# 			if not len(moves):
	# 				return
	#
	# 			# Undo move
	# 			lastMove = moves.pop()
	# 			deadBoxes = self._undoMove(lastMove, deadBoxes)
	# 			nextDir = MoveDir.getNext(lastMove.dir_)

	def _findWinMoves(self, checkedFields, endFieldFingerPrint):
		pass

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


if __name__ == "__main__":
	field = Field(5, [
		Cell.goal(),  Cell.empty(), Cell.empty(),  Cell.empty(), Cell.goal(),
		Cell.empty(), Cell.box(),   Cell.box(),    Cell.box(),   Cell.empty(),
		Cell.box(), Cell.box(),   Cell.empty(), Cell.box(),   Cell.empty(),
		Cell.goal(),  Cell.box(),   Cell.empty(),    Cell.runner(),   Cell.box(),
		Cell.empty(), Cell.goal(),  Cell.box(),  Cell.goal(),  Cell.empty()
	])

	field.show()
	print()
	field._analyze()
