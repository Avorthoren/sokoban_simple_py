# -*- coding: utf-8 -*-

import time

from cell import Cell
from field import Field


if __name__ == "__main__":
	# field_ = Field(5, [
	# 	Cell.wall(),   Cell.wall(),  Cell.empty(), Cell.empty(), Cell.wall(),
	# 	Cell.empty(),  Cell.empty(), Cell.box(),   Cell.empty(), Cell.wall(),
	# 	Cell.empty(),  Cell.wall(),  Cell.goal(),  Cell.goal(),  Cell.empty(),
	# 	Cell.runner(), Cell.empty(), Cell.goal(),  Cell.wall(),  Cell.empty(),
	# 	Cell.wall(),   Cell.box(),   Cell.empty(), Cell.box(),   Cell.empty(),
	# 	Cell.wall(),   Cell.empty(), Cell.empty(), Cell.wall(),  Cell.wall()
	# ])

	# field_ = Field(6, [
	# 	Cell.goal(),   Cell.empty(), Cell.goal(),      Cell.boxOnGoal(), Cell.empty(),     Cell.empty(),
	# 	Cell.wall(),   Cell.box(),   Cell.empty(),     Cell.boxOnGoal(), Cell.empty(),     Cell.empty(),
	# 	Cell.wall(),   Cell.empty(), Cell.empty(),     Cell.boxOnGoal(), Cell.empty(),     Cell.boxOnGoal(),
	# 	Cell.wall(),   Cell.empty(), Cell.boxOnGoal(), Cell.empty(),     Cell.empty(),     Cell.goal(),
	# 	Cell.empty(),  Cell.box(),   Cell.box(),       Cell.boxOnGoal(), Cell.boxOnGoal(), Cell.box(),
	# 	Cell.runner(), Cell.goal(),  Cell.empty(),     Cell.empty(),     Cell.empty(),     Cell.empty()
	# ])

	# field_ = Field(6, [
	# 	Cell.empty(),  Cell.empty(), Cell.empty(), Cell.empty(),     Cell.goal(),  Cell.empty(),
	# 	Cell.runner(), Cell.empty(), Cell.empty(), Cell.wall(),      Cell.wall(),  Cell.empty(),
	# 	Cell.empty(),  Cell.empty(), Cell.empty(), Cell.boxOnGoal(), Cell.empty(), Cell.empty(),
	# 	Cell.goal(),   Cell.box(),   Cell.empty(), Cell.box(),       Cell.empty(), Cell.empty(),
	# 	Cell.box(),    Cell.box(),   Cell.box(),   Cell.box(),       Cell.goal(),  Cell.empty(),
	# 	Cell.goal(),   Cell.goal(),  Cell.goal(),  Cell.empty(),     Cell.empty(), Cell.empty()
	# ])

	# field_ = Field(5, [
	# 	Cell.empty(),  Cell.empty(), Cell.empty(),     Cell.goal(),  Cell.empty(),
	# 	Cell.empty(),  Cell.wall(),  Cell.empty(),     Cell.wall(),  Cell.empty(),
	# 	Cell.empty(),  Cell.box(),   Cell.runner(),    Cell.box(),   Cell.empty(),
	# 	Cell.empty(),  Cell.wall(),  Cell.empty(),     Cell.wall(),  Cell.goal(),
	# 	Cell.empty(),  Cell.empty(), Cell.boxOnGoal(), Cell.empty(), Cell.empty()
	# ])

	# field_ = Field(5, [
	# 	Cell.goal(),  Cell.empty(), Cell.empty(),  Cell.empty(), Cell.goal(),
	# 	Cell.empty(), Cell.box(),   Cell.box(),    Cell.box(),   Cell.empty(),
	# 	Cell.empty(), Cell.box(),   Cell.runner(), Cell.box(),   Cell.empty(),
	# 	Cell.goal(),  Cell.box(),   Cell.box(),    Cell.box(),   Cell.goal(),
	# 	Cell.goal(), Cell.goal(),  Cell.empty(),  Cell.goal(),  Cell.goal()
	# ])

	# field_ = Field(5, [
	# 	Cell.goal(),  Cell.empty(), Cell.empty(),  Cell.empty(), Cell.goal(),
	# 	Cell.empty(), Cell.box(),   Cell.box(),    Cell.box(),   Cell.empty(),
	# 	Cell.empty(), Cell.box(),   Cell.runner(), Cell.box(),   Cell.empty(),
	# 	Cell.goal(),  Cell.box(),   Cell.box(),    Cell.box(),   Cell.goal(),
	# 	Cell.empty(), Cell.goal(),  Cell.empty(),  Cell.goal(),  Cell.empty()
	# ])

	# field_ = Field(5, [
	# 	Cell.goal(),      Cell.empty(),     Cell.empty(),  Cell.empty(), Cell.empty(),
	# 	Cell.boxOnGoal(), Cell.wall(),      Cell.empty(),  Cell.empty(), Cell.empty(),
	# 	Cell.goal(),      Cell.box(),       Cell.empty(),  Cell.box(),   Cell.empty(),
	# 	Cell.goal(),      Cell.boxOnGoal(), Cell.box(),    Cell.box(),   Cell.empty(),
	# 	Cell.goal(),      Cell.wall(),      Cell.runner(), Cell.empty(), Cell.empty()
	# ])

	# field_ = Field(6, [
	# 	Cell.wall(),  Cell.wall(),  Cell.empty(),        Cell.empty(),     Cell.wall(),  Cell.wall(),
	# 	Cell.wall(),  Cell.wall(),  Cell.empty(),        Cell.box(),       Cell.wall(),  Cell.wall(),
	# 	Cell.wall(),  Cell.empty(), Cell.runnerOnGoal(), Cell.boxOnGoal(), Cell.goal(),  Cell.empty(),
	# 	Cell.empty(), Cell.empty(), Cell.empty(),        Cell.box(),       Cell.empty(), Cell.empty(),
	# 	Cell.empty(), Cell.empty(), Cell.wall(),         Cell.empty(),     Cell.wall(),  Cell.wall(),
	# 	Cell.empty(), Cell.empty(), Cell.empty(),        Cell.empty(),     Cell.wall(),  Cell.wall(),
	# ])

	# >>>>>>>>> BUG <<<<<<<<<<
	# field_ = Field(4, [
	# 	Cell.wall(),  Cell.empty(), Cell.empty(), Cell.wall(),
	# 	Cell.goal(),  Cell.empty(), Cell.box(),   Cell.wall(),
	# 	Cell.goal(),  Cell.box(),   Cell.empty(), Cell.wall(),
	# 	Cell.goal(),  Cell.box(),   Cell.empty(), Cell.wall(),
	# 	Cell.goal(),  Cell.box(),   Cell.empty(), Cell.wall(),
	# 	Cell.goal(),  Cell.empty(), Cell.box(),   Cell.wall(),
	# 	Cell.empty(), Cell.empty(), Cell.empty(), Cell.runner(),
	# 	Cell.wall(),  Cell.empty(), Cell.empty(), Cell.empty(),
	# ])

	field_ = Field(13, [
		Cell.empty(), Cell.empty(), Cell.wall(),  Cell.wall(), Cell.wall(),  Cell.wall(), Cell.wall(),  Cell.wall(),  Cell.wall(),  Cell.wall(),  Cell.wall(),  Cell.wall(),   Cell.wall(),
		Cell.empty(), Cell.box(),   Cell.empty(), Cell.box(),  Cell.empty(), Cell.box(),  Cell.empty(), Cell.box(),   Cell.empty(), Cell.box(),   Cell.empty(), Cell.runner(), Cell.empty(),
		Cell.empty(), Cell.goal(),  Cell.goal(),  Cell.goal(), Cell.goal(),  Cell.goal(), Cell.empty(), Cell.empty(), Cell.empty(), Cell.empty(), Cell.empty(), Cell.empty(),  Cell.empty(),
	])

	field_.show()
	print()
	print("Processing, wait...")

	t0 = time.time()
	success = field_.solve(logInterval=10000)
	print()
	print(f"Checked in {time.time() - t0:.2f} seconds")
	print(f"{field_.totalStatesChecked} states generated")
	if success:
		print()
		print(
			f"Solution with {field_.getTotalWinMoves()} total moves"
			f" ({field_.totalWinBoxMoves} PUSH-moves) found. Show? y/n"
		)
		answer = input()
		if answer == "y":
			print(field_.getWinMovesRepr())
		print()
		answer = input("Show animation? y/n\n")
		if answer == "y":
			field_.showSolution(delay=0.3)
	else:
		print()
		print("There is no solution :(")
