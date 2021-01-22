# -*- coding: utf-8 -*-
"""
fp - fingerprint

fp вычисляем как hash(упорядоченный список индексов клеток всех ящиков + индекс
компоненты связности бегуна).

Создаём словарь бегунов {int - id: Field}. Помещаем туда первого с rawCopy
исходного поля. Вычисляем fp, список доступных ходов и список мёртвых ящиков.
Если поле мёртвое => конец.

Храним словарь посещённых состояний:
{int - fp: (BoxMove, int) | (None, None) - ход, который привёл к этому состоянию
           и fp предыдущего состояния
}
Вначале там {fp(стартовое состояние): (None, None)}

Условие 0:
Перед выполнением хода нужно убедиться, что либо конечная клетка либо
не мёртвая, либо после выполнения хода будет
(totalGoals - totalDeadBoxesOnGoals) <= (totalBoxes - totalDeadBoxes).
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
	Построить список PUSH ходов в обратном порядке, прыгая по checkedFields,
	пока не прийдём к состояния с последним ходом None.
	Из исходного состояния поля итерируем по PUSH ходам. Для каждого PUSH хода
	ищем список MOVE ходов поиском в ширину. Готово: вы великолепны.
"""
from __future__ import annotations
import os
import time
from typing import Dict, Generator, List, Set, Sequence, Tuple, Union

from cell import CellType, CellState, Cell
from move import MoveType, MoveDir, Move, BoxMove
import utils


class Field:
	# Aliases:
	# {field fingerprint: (last box move, prev field fingerprint)}
	CheckedFields = Dict[int, Union[Tuple[BoxMove, int], Tuple[None, None]]]
	# {cell index: (last move dir, prev cell index)}
	CheckedCells = Dict[int, Union[Tuple[MoveDir, int], Tuple[None, None]]]

	BORDER_SYMBOL = "x"

	def __init__(self, n: int, cells: Sequence[Cell]):
		if not cells or not isinstance(cells, list) or any(not isinstance(cell, Cell) for cell in cells):
			raise ValueError(f"{cells.__name__} must be non-empty list of {Cell.__name__}s")

		if not isinstance(n, int) or n <= 0 or len(cells) % n:
			raise ValueError(f"{n.__name__} must be positive int and divide len of {cells.__name__}")

		# cells passed as linear list but represents 2D matrix n*m.
		self._cells = tuple(cells)
		self._n = n
		self._m = len(cells) // n
		self._totalGoals = 0
		self._unachievedGoals = 0
		self._totalBoxes = 0

		hasRunner = False
		for i, cell in enumerate(cells):
			if cell.hasRunner():
				if hasRunner:
					raise ValueError("Field must have exactly one runner")
				hasRunner = True
				self._runnerPos = i
			elif cell.hasBox():
				self._totalBoxes += 1

			if cell.isGoal():
				self._totalGoals += 1
				if cell.state != CellState.BOX:
					self._unachievedGoals += 1

		if not hasRunner:
			raise ValueError("Field must have runner")

		if self._totalGoals > self._totalBoxes:
			raise ValueError(f"Number of total goals must be at most number of total boxes")

		self._deadBoxes = set()
		self._totalDeadBoxesOnGoals = 0
		self._totalStatesChecked = 0
		self._fingerprint = None
		self._totalWinBoxMoves = None
		self._winMoves = None if self._unachievedGoals else []
		self._solvable = None if self._unachievedGoals else True
		self._runnerComponentID = None
		self._boxMoves = None

	@property
	def n(self) -> int:
		return self._n

	@property
	def m(self) -> int:
		return self._m

	@property
	def solvable(self) -> bool:
		return self._solvable

	@property
	def totalStatesChecked(self):
		return self._totalStatesChecked

	@property
	def totalWinBoxMoves(self):
		return self._totalWinBoxMoves

	def _rawCopy(self) -> Field:
		cls = self.__class__
		copy_ = cls.__new__(cls)

		copy_._cells = tuple(cell.copy() for cell in self._cells)
		copy_._n = self._n
		copy_._m = self._m
		copy_._totalGoals = self._totalGoals
		copy_._unachievedGoals = self._unachievedGoals
		copy_._totalBoxes = self._totalBoxes
		copy_._runnerPos = self._runnerPos
		copy_._deadBoxes = set()
		copy_._totalDeadBoxesOnGoals = self._totalDeadBoxesOnGoals

		return copy_

	def _fingerprintGen(self) -> Generator[int, None, None]:
		for i, cell in enumerate(self._cells):
			if cell.hasBox():
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
	def _getMovesRepr(moves: Sequence[Move]) -> Union[str, None]:
		if moves is None:
			return None

		return "".join(str(move) for move in moves)

	def getWinMovesRepr(self) -> str:
		return self._getMovesRepr(self._winMoves)

	def getTargetCellIndex(self, pos: int, moveDir: MoveDir) -> Union[int, None]:
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

	def _undoBoxMove(
		self,
		unachievedGoals: int,
		runnerCellIndex: int,
		boxCellIndex: int,
		targetCellIndex: int,
		totalDeadBoxesOnGoals: int
	) -> None:
		self._unachievedGoals = unachievedGoals
		self._cells[targetCellIndex].state = CellState.EMPTY
		self._cells[boxCellIndex].state = CellState.BOX
		self._runnerPos = runnerCellIndex
		self._cells[runnerCellIndex].state = CellState.RUNNER
		self._totalDeadBoxesOnGoals = totalDeadBoxesOnGoals

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
			if targetCellIndex is None or self._cells[targetCellIndex].isWall():
				deadNeighbours.add(moveDir)
			elif self._cells[targetCellIndex].hasBox():
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
				cell.hasBox()
				and i not in self._deadBoxes
				and self._boxIsDead(i, self._deadBoxes)
			):
				self._deadBoxes.add(i)
				if cell.isGoal():
					self._totalDeadBoxesOnGoals += 1

				if (self._totalGoals - self._totalDeadBoxesOnGoals) > (self._totalBoxes - len(self._deadBoxes)):
					return True

		return False

	def showWithDeadBoxes(self, tab="", sep=" ", end="\n") -> None:
		deadBoxes = set()

		for i, cell in enumerate(self._cells):
			if cell.hasBox() and self._boxIsDead(i, deadBoxes):
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
		"""Find runner component id, fingerprint and all possible box moves.

		Implemented as BFS.
		"""
		self._runnerComponentID = None
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

							elif targetCell.hasBox():
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
		checkedFields = {startField._fingerprint: (None, None)}
		if startField.isDead():
			return self._solvable  # False

		# Solve field
		endFieldFingerPrint = self._solve(startField, checkedFields, logInterval)
		if endFieldFingerPrint is None:
			return self._solvable

		self._solvable = True  # False

		# Construct runner moves
		self._findWinMoves(checkedFields, endFieldFingerPrint)

		return self._solvable  # True

	def _solve(
		self,
		startField: Field,
		checkedFields: CheckedFields,
		logInterval: Union[None, int]
	) -> Union[int, None]:
		"""Find solution in terms of box moves.

		Implemented as BFS.
		"""
		# Prepare set of cell indices to which it makes no sense to move the box
		deadCells = set()
		for i, cell in enumerate(self._cells):
			# Dead cell is REGULAR cell that have > 2 WALL neighbours or 2
			# adjacent WALL neighbours (where border must be treated as WALL)
			if cell.isRegular():
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
		logCounter = 1
		step = 0
		while runners:
			step += 1
			if logInterval is not None:
				print(f"STEP {step}")
			# <<< DEBUG BLOCK
			# print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
			# print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
			# print(f"STEP {step}")
			# print(f"{len(runners)} active runners")
			# input()
			# print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
			# <<< END DEBUG BLOCK
			for runnerID in tuple(runners):
				field = runners[runnerID]
				# <<< DEBUG BLOCK
				# print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
				# print(f"Runner #{runnerID}")
				# field.show()
				# print()
				# print("Box moves:", field._boxMoves)
				# <<< END DEBUG BLOCK
				if not field._unachievedGoals:
					self._totalStatesChecked = len(checkedFields)
					return field._fingerprint  # <<< SUCCESS EXIT POINT

				runnerToDeleteID = runnerID
				savedDeadBoxes = None
				boxMoves = field._boxMoves
				runnerCellIndex = field._runnerPos
				prevFieldFingerprint = field._fingerprint
				unachievedGoals = field._unachievedGoals
				totalDeadBoxesOnGoals = field._totalDeadBoxesOnGoals
				for i, boxMove in enumerate(boxMoves):
					# print(boxMove, end=": ")  # <<< DEBUG
					runnerCell = field._cells[runnerCellIndex]
					boxCellIndex = boxMove.startCellIndex
					boxCell = field._cells[boxCellIndex]
					targetCellIndex = field.getTargetCellIndex(boxMove.startCellIndex, boxMove.dir_)
					targetCell = field._cells[targetCellIndex]
					newUnachievedGoals = unachievedGoals + int(boxCell.isGoal()) - int(targetCell.isGoal())

					# Check if target field is dead (light version)
					# (totalGoals - totalDeadBoxesOnGoals) > (totalBoxes - totalDeadBoxes)
					if (
						targetCellIndex in deadCells
						and (
							field._totalGoals - (totalDeadBoxesOnGoals + int(targetCell.isGoal()))
						) > (
							field._totalBoxes - (len(field._deadBoxes) + 1)
						)
					):
						# print("CONDITION 0 FAILS")  # <<< DEBUG
						continue

					# Save dead boxes for undo move in future
					if i != len(boxMoves) - 1 and savedDeadBoxes is None:
						savedDeadBoxes = field._deadBoxes.copy()

					# Do move
					runnerCell.state = CellState.EMPTY
					boxCell.state = CellState.RUNNER
					field._runnerPos = boxCellIndex
					targetCell.state = CellState.BOX
					field._unachievedGoals = newUnachievedGoals

					# Check if field was not checked earlier
					field._analyze()
					if field._fingerprint in checkedFields:
						# print("CONDITION 1 FAILS")  # <<< DEBUG
						field._undoBoxMove(unachievedGoals, runnerCellIndex, boxCellIndex, targetCellIndex, totalDeadBoxesOnGoals)
						continue

					checkedFields[field._fingerprint] = (boxMove, prevFieldFingerprint)

					if logInterval is not None:
						logCounter += 1
						if logCounter == logInterval:
							logCounter = 0
							print(f"{len(checkedFields)} total fields generated, {len(runners)} active runners")

					# Check if field is not dead
					if field.isDead():
						# print("CONDITION 2 FAILS")  # <<< DEBUG
						field._undoBoxMove(unachievedGoals, runnerCellIndex, boxCellIndex, targetCellIndex, totalDeadBoxesOnGoals)
						continue

					# print(f"ALLOWED MOVE for runner #{runnerID}")  # <<< DEBUG

					# Create new runner if needed
					if i != len(boxMoves) - 1:
						runnerID = next(runnerIDGen)
						runnerToDeleteID = runnerID
						field: Field = field._rawCopy()
						runners[runnerID] = field
						field._deadBoxes = savedDeadBoxes
						field._undoBoxMove(unachievedGoals, runnerCellIndex, boxCellIndex, targetCellIndex, totalDeadBoxesOnGoals)
						continue

					# Since move was successful, we don't need to delete this
					# runner
					runnerToDeleteID = None

				if runnerToDeleteID is not None:
					del runners[runnerToDeleteID]

		self._totalStatesChecked = len(checkedFields)

		return None  # <<< FAIL EXIT POINT

	def _findWinMoves(
		self,
		checkedFields: CheckedFields,
		endFieldFingerPrint: int
	) -> None:
		# Construct box moves sequence
		winBoxMovesReversed = []
		lastBoxMove, prevFieldFingerprint = checkedFields[endFieldFingerPrint]
		while lastBoxMove is not None:
			winBoxMovesReversed.append(lastBoxMove)
			lastBoxMove, prevFieldFingerprint = checkedFields[prevFieldFingerprint]

		self._totalWinBoxMoves = len(winBoxMovesReversed)

		# Finally construct win moves
		self._winMoves = []
		field = self._rawCopy()
		for boxMove in reversed(winBoxMovesReversed):
			moveDir = boxMove.dir_
			boxCellIndex = boxMove.startCellIndex
			targetCellIndex = field.getTargetCellIndex(boxCellIndex, moveDir)
			runnerCellIndex = field.getTargetCellIndex(boxCellIndex, MoveDir.getOpposite(moveDir))

			# Find and append REGULAR moves
			field._appendMovesUntil(runnerCellIndex, self._winMoves)

			# Do and append PUSH move
			field._runnerPos = boxCellIndex
			field._cells[boxCellIndex].state = CellState.RUNNER
			field._cells[targetCellIndex].state = CellState.BOX
			field._cells[runnerCellIndex].state = CellState.EMPTY

			self._winMoves.append(Move(MoveType.PUSH, moveDir))

	def _appendMovesUntil(self, finalCellIndex: int, moves: List[Move]) -> None:
		"""Updates moves"""
		startCellIndex = self._runnerPos
		if startCellIndex == finalCellIndex:
			return

		# {cell index: (last move dir, prev cell index)}
		checkedCells = {self._runnerPos: (None, None)}
		self._bsfBetween(startCellIndex, finalCellIndex, checkedCells)

		movesToAppendReversed = []
		lastMoveDir, prevCellIndex = checkedCells[finalCellIndex]
		while lastMoveDir is not None:
			lastMoveDir: MoveDir  # PyCharm type checker is stupid
			movesToAppendReversed.append(Move(MoveType.REGULAR, lastMoveDir))
			lastMoveDir, prevCellIndex = checkedCells[prevCellIndex]

		moves.extend(reversed(movesToAppendReversed))

	def _bsfBetween(
		self,
		startCellIndex: int,
		finalCellIndex: int,
		checkedCells: CheckedCells
	) -> None:
		"""Updates checkedCells"""
		runnerIDGen = utils.idGenerator()
		runners = {next(runnerIDGen): startCellIndex}
		while runners:
			for runnerID in tuple(runners):
				currentPos = runners[runnerID]
				runnerNotMoved = True
				if currentPos == finalCellIndex:
					return  # <<< SUCCESS EXIT POINT

				for moveDir in MoveDir:
					targetCellIndex = self.getTargetCellIndex(currentPos, moveDir)
					if targetCellIndex is None:
						continue

					targetCell = self._cells[targetCellIndex]
					if targetCell.isPassable() and targetCellIndex not in checkedCells:
						# Mark cell as checked and move further
						checkedCells[targetCellIndex] = (moveDir, currentPos)
						if runnerNotMoved:
							runnerNotMoved = False
							runners[runnerID] = targetCellIndex
						else:
							runners[next(runnerIDGen)] = targetCellIndex

				if runnerNotMoved:
					del runners[runnerID]

		print()
		self.show()
		raise RuntimeError(
			f"There is no possible REGULAR moves sequence"
			f" between cells {startCellIndex} and {finalCellIndex}"
		)

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

	def _putRunnerIn(self, cellIndex):
		if not self._cells[cellIndex].isPassable:
			raise ValueError(f"Cell #{cellIndex} is not passable")

		self._cells[self._runnerPos].state = CellState.EMPTY
		self._cells[cellIndex].state = CellState.RUNNER
		self._runnerPos = cellIndex


def forTest():
	indexes = (
		 0,  1,  2,      4,  5,
		 6,  7,  8,         11,
		12, 13, 14,     16, 17,
		18,     20,     22, 23,
		                28, 29,
		30, 31, 32, 33, 34, 35
	)
	field_ = Field(6, [
		Cell.runner(), Cell.empty(), Cell.empty(), Cell.wall(),     Cell.goal(),  Cell.empty(),
		Cell.empty(),  Cell.empty(), Cell.empty(), Cell.wall(),      Cell.wall(),  Cell.empty(),
		Cell.empty(),  Cell.empty(), Cell.empty(), Cell.boxOnGoal(), Cell.empty(), Cell.empty(),
		Cell.goal(),   Cell.box(),   Cell.empty(), Cell.box(),       Cell.empty(), Cell.empty(),
		Cell.box(),    Cell.box(),   Cell.box(),   Cell.box(),       Cell.goal(),  Cell.empty(),
		Cell.goal(),   Cell.goal(),  Cell.goal(),  Cell.empty(),     Cell.empty(), Cell.empty()
	])

	field_.show()

	for cellIndex in indexes:
		field_._putRunnerIn(cellIndex)
		field_._analyze()
		print(field_._fingerprint)


if __name__ == "__main__":
	forTest()
