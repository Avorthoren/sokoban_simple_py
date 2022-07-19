# -*- coding: utf-8 -*-

import time

from cell import Cell
from field import Field


if __name__ == "__main__":
	field = Field(5, [
		Cell.wall(),   Cell.wall(),  Cell.empty(), Cell.empty(), Cell.wall(),
		Cell.empty(),  Cell.empty(), Cell.box(),   Cell.empty(), Cell.wall(),
		Cell.empty(),  Cell.wall(),  Cell.goal(),  Cell.goal(),  Cell.empty(),
		Cell.runner(), Cell.empty(), Cell.goal(),  Cell.wall(),  Cell.empty(),
		Cell.wall(),   Cell.box(),   Cell.empty(), Cell.box(),   Cell.empty(),
		Cell.wall(),   Cell.empty(), Cell.empty(), Cell.wall(),  Cell.wall()
	])

	# field = Field(6, [
	# 	Cell.goal(),   Cell.empty(), Cell.goal(),      Cell.boxOnGoal(), Cell.empty(),     Cell.empty(),
	# 	Cell.wall(),   Cell.box(),   Cell.empty(),     Cell.boxOnGoal(), Cell.empty(),     Cell.empty(),
	# 	Cell.wall(),   Cell.empty(), Cell.empty(),     Cell.boxOnGoal(), Cell.empty(),     Cell.boxOnGoal(),
	# 	Cell.wall(),   Cell.empty(), Cell.boxOnGoal(), Cell.empty(),     Cell.empty(),     Cell.goal(),
	# 	Cell.empty(),  Cell.box(),   Cell.box(),       Cell.boxOnGoal(), Cell.boxOnGoal(), Cell.box(),
	# 	Cell.runner(), Cell.goal(),  Cell.empty(),     Cell.empty(),     Cell.empty(),     Cell.empty()
	# ])

	# field = Field(6, [
	# 	Cell.empty(),  Cell.empty(), Cell.empty(), Cell.empty(),     Cell.goal(),  Cell.empty(),
	# 	Cell.runner(), Cell.empty(), Cell.empty(), Cell.wall(),      Cell.wall(),  Cell.empty(),
	# 	Cell.empty(),  Cell.empty(), Cell.empty(), Cell.boxOnGoal(), Cell.empty(), Cell.empty(),
	# 	Cell.goal(),   Cell.box(),   Cell.empty(), Cell.box(),       Cell.empty(), Cell.empty(),
	# 	Cell.box(),    Cell.box(),   Cell.box(),   Cell.box(),       Cell.goal(),  Cell.empty(),
	# 	Cell.goal(),   Cell.goal(),  Cell.goal(),  Cell.empty(),     Cell.empty(), Cell.empty()
	# ])

	# field = Field(5, [
	# 	Cell.empty(),  Cell.empty(), Cell.empty(),     Cell.goal(),  Cell.empty(),
	# 	Cell.empty(),  Cell.wall(),  Cell.empty(),     Cell.wall(),  Cell.empty(),
	# 	Cell.empty(),  Cell.box(),   Cell.runner(),    Cell.box(),   Cell.empty(),
	# 	Cell.empty(),  Cell.wall(),  Cell.empty(),     Cell.wall(),  Cell.goal(),
	# 	Cell.empty(),  Cell.empty(), Cell.boxOnGoal(), Cell.empty(), Cell.empty()
	# ])

	# field = Field(5, [
	# 	Cell.goal(),  Cell.empty(), Cell.empty(),  Cell.empty(), Cell.goal(),
	# 	Cell.empty(), Cell.box(),   Cell.box(),    Cell.box(),   Cell.empty(),
	# 	Cell.empty(), Cell.box(),   Cell.runner(), Cell.box(),   Cell.empty(),
	# 	Cell.goal(),  Cell.box(),   Cell.box(),    Cell.box(),   Cell.goal(),
	# 	Cell.empty(),  Cell.goal(),  Cell.empty(),  Cell.goal(),  Cell.empty()
	# ])

	field.show()
	print()
	# print(f"{'Dead' if field.isDead() else 'Alive'}")
	# field.showWithDeadBoxes()
	print("Processing, wait...")

	t0 = time.time()
	if field.solve(logInterval=100000):
		print()
		print(f"Checked in {time.time() - t0:.2f} seconds")
		print(f"Solution with {field.getTotalWinMoves()} total moves found. Show? y/n")
		answer = input()
		if answer == "y":
			print(field.getWinMovesRepr())
		print()
		answer = input("Show animation? y/n\n")
		if answer == "y":
			field.showSolution(delay=0.3)
	else:
		print()
		print(f"Checked in {time.time() - t0} seconds")
		print("There is no solution :(")
