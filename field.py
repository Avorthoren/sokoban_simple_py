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
from __future__ import annotations
import copy
import os
import time
from typing import Dict, Generator, Set, Sequence, Union

from cell import CellType, CellState, Cell
from move import MoveType, MoveDir, Move, BoxMove
import utils


class Field:

	BORDER_SYMBOL = "x"

	def __init__(self, n: int, cells: Sequence[Cell]):
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
	def n(self) -> int:
		return self._n

	@property
	def m(self) -> int:
		return self._m

	@property
	def solvable(self) -> bool:
		return self._solvable

	def _rawCopy(self) -> Field:
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

	def _fingerprintGen(self) -> Generator[int, None, None]:
		for i, cell in enumerate(self._cells):
			if cell.state == CellState.BOX:
				yield i

		yield self._runnerComponentID

	def _getFingerprint(self) -> int:
		# All box positions and runner connectivity component
		return hash(tuple(val for val in self._fingerprintGen()))

	def _hashGen(self) -> Generator[int, None, None]:
		for cell in self._cells:
			yield hash(cell)

		yield self._n

	def __hash__(self):
		# n and all cells fully describe field
		return hash(tuple(val for val in self._hashGen()))

	def show(self, tab="", sep=" ", end="\n") -> None:
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
	def _getMovesRepr(moves: Sequence[Move]) -> str:
		if moves is None:
			return None

		return "".join(str(move) for move in moves)

	def getWinMovesRepr(self) -> str:
		return self._getMovesRepr(self._winMoves)

	def getTargetCellIndex(self, pos: int, moveDir: MoveDir) -> int:
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
	def _cellIsBlocked(blockedNeighbours: Set[MoveDir]) -> bool:
		return (
			len(blockedNeighbours) > 2
			or len(blockedNeighbours) == 2
			and ((MoveDir.UP in blockedNeighbours) ^ (MoveDir.DOWN in blockedNeighbours))
		)

	def _boxIsDead(self, i: int, deadBoxes: Set[int]) -> bool:
		"""Assumes this cell is indeed a BOX and it is not in deadBoxes

		deadBoxes is passed explicitly for recursion.
		"""
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

	def isDead(self) -> bool:
		"""Assumes it was not dead when self._deadBoxes was last updated

		Updates self._deadBoxes
		"""
		for i, cell in enumerate(self._cells):
			if (
				cell.state == CellState.BOX
				and i not in self._deadBoxes
				and self._boxIsDead(i, self._deadBoxes)
			):
				self._deadBoxes.add(i)
				if self._totalBoxes - len(self._deadBoxes) < self._unachievedGoals:
					return True

		return False

	def showWithDeadBoxes(self, tab="", sep=" ", end="\n") -> None:
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

	def _analyze(self) -> None:
		"""Find runner component index, fingerprint and all possible box moves.

		Implemented as BFS.
		"""
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

		self._boxMoves = boxMoves[self._runnerComponentID]

	def solve(self, logInterval: Union[None, int] = None) -> bool:
		if self._solvable is None:
			self._solvable = False
		else:
			return self._solvable

		# Prepare start data
		startField = self._rawCopy()
		startField._analyze()
		checkedFields = {startField._fingerprint: None}
		if startField.isDead():
			return self._solvable  # False

		# Solve field
		endFieldFingerPrint = self._solve(startField, checkedFields, logInterval)
		if endFieldFingerPrint is None:
			return self._solvable

		self._solvable = True  # False

		# Запустить _findWinMoves, передав туда словарь посещённых состояний
		# и fp конечного поля.
		self._findWinMoves(checkedFields, endFieldFingerPrint)

		return self._solvable  # True

	def _solve(
		self,
		startField: Field,
		checkedFields: Dict[int, Union[MoveDir, None]],
		logInterval: Union[None, int]
	) -> int:
		"""Find solution in terms of box moves.

		Implemented as BFS.
		"""
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

		# Start main algorithm
		runnerIDGen = utils.idGenerator()
		runners = {next(runnerIDGen): startField}


		return 0

	def _findWinMoves(
		self,
		checkedFields: Dict[int, Union[MoveDir, None]],
		endFieldFingerPrint: int
	) -> None:
		pass

	def showSolution(self, delay: Union[int, float] = 1.0) -> None:
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

	def getTotalWinMoves(self) -> Union[int, None]:
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
