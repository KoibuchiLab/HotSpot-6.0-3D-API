#!/usr/bin/python

import math
import random
import os
import sys

from math import sqrt

import numpy as np

from scipy.optimize import basinhopping
from scipy.optimize import fmin_slsqp

import optimize_layout_globals

from layout import *
from power_optimizer import *



##############################################################################################
### LAYOUT OPTIMIZATION
##############################################################################################


class LayoutOptimizer(object):
	
	def __init__(self):
		global argv
		argv = optimize_layout_globals.argv
		global abort
		abort = optimize_layout_globals.abort
		global info
		info = optimize_layout_globals.info
		global pick_random_element
		pick_random_element = optimize_layout_globals.pick_random_element

		LayoutBuilder()
		PowerOptimizer()


"""Top-level optimization function"""
def optimize_layout():

        # Compute continuous solution
	if (argv.layout_scheme == "stacked"):
                solution = optimize_layout_stacked()
	elif (argv.layout_scheme == "rectilinear_straight"):
                solution = optimize_layout_rectilinear("straight")
	elif (argv.layout_scheme == "rectilinear_diagonal"):
		solution =  optimize_layout_rectilinear("diagonal")
	elif (argv.layout_scheme == "checkerboard"):
		solution =  optimize_layout_checkerboard()
	elif (argv.layout_scheme == "linear_random_greedy"):
		solution =  optimize_layout_linear_random_greedy()
	elif (argv.layout_scheme == "random_greedy"):
		solution =  optimize_layout_random_greedy()
	else:
		abort("Layout scheme '" + argv.layout_scheme + "' is not supported")

        return solution

"""Stacked layout optimization"""

def optimize_layout_stacked():

	if (argv.verbose == 0):
		sys.stderr.write("o")

	info(1, "Constructing a stacked layout")

	layout = LayoutBuilder.compute_stacked_layout()

	result = find_maximum_power_budget(layout)

        if result == None:
            return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]
		
"""Linear layout optimization"""

def optimize_layout_rectilinear(mode):

	if (argv.verbose == 0):
		sys.stderr.write("o")
	info(1, "Constructing a " + mode + " rectilinear layout")

	if (mode == "straight"):
		layout = LayoutBuilder.compute_rectilinear_straight_layout()
	elif (mode == "diagonal"):
		layout = LayoutBuilder.compute_rectilinear_diagonal_layout()
	else:
		abort("Unknown rectilinear layout mode '" + mode + "'")

	result = find_maximum_power_budget(layout)
        if (result == None):
            return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]
	
			

"""Linear random greedy layout optimization"""

def optimize_layout_linear_random_greedy():

	# Create an initial layout
	layout = Layout(argv.chip, [[1, 0.0, 0.0]], argv.medium, argv.overlap)

	
	max_num_random_trials = 5  # TODO: Don't hardcode this
	while (layout.get_num_chips() != argv.num_chips):
                info (1, "* Generating " + str(max_num_random_trials) + " candidate positions for chip #" + str(1 + layout.get_num_chips()) + " in the layout")
		num_random_trials = 0
                candidate_random_trials = []
		while (len(candidate_random_trials) < max_num_random_trials):
			last_chip_position = layout.get_chip_positions()[-1]

			# Pick a random location relative to the last chip

			# pick a random level
			possible_levels = []
			if (last_chip_position[0] == 1):
				possible_levels = [2]
			elif (last_chip_position[0] == argv.num_levels):
				possible_levels = [argv.num_levels - 1]
			else:
				possible_levels = [last_chip_position[0]-1, last_chip_position[0]+1]

			picked_level = pick_random_element(possible_levels)

                        # pick a random coordinates
			[picked_x, picked_y] = Layout.get_random_overlapping_rectangle([last_chip_position[1], last_chip_position[2]], [layout.get_chip().x_dimension, layout.get_chip().y_dimension], argv.overlap)

                        # Check that the chip can fit
                        if (not layout.can_new_chip_fit([picked_level, picked_x, picked_y])):
                            continue

                        candidate_random_trials.append([picked_level, picked_x, picked_y])

                # Pick a candidate
                max_power = -1
                picked_candidate = None
                for candidate in candidate_random_trials:
                        layout.add_new_chip(candidate) 
                        print layout.get_chip_positions()
                        info(1, "- Evaluating candidate " + str(candidate))
                        result = find_maximum_power_budget(layout) 
                        if (result != None):
                            [power_distribution, temperature] = result
                            if (sum(power_distribution) > max_power):
                                picked_candidate = candidate
                        layout.remove_chip(layout.get_num_chips() - 1)
                        
                # Add the candidate 
                info(1, "Picked candidate: " + str(candidate))
                layout.add_new_chip(picked_candidate) 
                        

        # Do the final evaluation (which was already be done, but whatever)
        result = find_maximum_power_budget(layout) 
        if (result == None):
            return None

        [power_distribution, temperature] = result

	return [layout, power_distribution, temperature]


"""Random greedy layout optimization"""

def optimize_layout_random_greedy():

	abort("optimize_layout_random_greedy() is not implemented yet")

	# Create an initial layout: TODO This could be anything
	layout = Layout(argv.chip, [[1, 0.0, 0.0]], argv.medium, argv.overlap)

	max_num_random_trials = 5 # TODO: Don't hardcode this
	while (layout.get_num_chips() != argv.num_chips):
                info(1, "* Generating " + str(max_num_random_trials) + " candidate positions for chip #" + str(1 + layout.get_num_chips()) + " in the layout")
		num_random_trials = 0
                candidate_random_trials = []
		while (len(candidate_random_trials) < max_num_random_trials):

			# Pick a neighboring chip

			# TODO: Linear	
			#neighbor_of = layout.get_chip_positions()[-1]

			# Pick a random neighbor
			neighbor_of = random.uniform(0, layout.get_num_chips()-1)

			# Check whether adding a neighbor to that chip would be ok
                        # diameter-wise
			# TODO TODO TODO TODO TODO	

			# pick a random level
			possible_levels = []
			if (last_chip_position[0] == 1):
				possible_levels = [2]
			elif (last_chip_position[0] == argv.num_levels):
				possible_levels = [argv.num_levels - 1]
			else:
				possible_levels = [last_chip_position[0]-1, last_chip_position[0]+1]

			picked_level = pick_random_element(possible_levels)

                        # pick a random coordinates
			[picked_x, picked_y] = Layout.get_random_overlapping_rectangle([last_chip_position[1], last_chip_position[2]], [layout.get_chip().x_dimension, layout.get_chip().y_dimension], argv.overlap)

                        # Check that the chip can fit
                        if (not layout.can_new_chip_fit([picked_level, picked_x, picked_y])):
                            continue

                        candidate_random_trials.append([picked_level, picked_x, picked_y])

                # Pick a candidate
                max_power = -1
                picked_candidate = None
                for candidate in candidate_random_trials:
                        layout.add_new_chip(candidate) 
                        print layout.get_chip_positions()
                        info(1, "- Evaluating candidate " + str(candidate))
                        result = find_maximum_power_budget(layout) 
                        if (result != None):
                            [power_distribution, temperature] = result
                            if (sum(power_distribution) > max_power):
                                picked_candidate = candidate
                        layout.remove_chip(layout.get_num_chips() - 1)
                        
                # Add the candidate 
                info(1, "Picked candidate: " + str(candidate))
                layout.add_new_chip(picked_candidate) 

        # Do the final evaluation (which was already be done, but whatever)
        result = find_maximum_power_budget(layout) 
        if (result == None):
            return None

        [power_distribution, temperature] = result

	return [layout, power_distribution, temperature]



"""Checkboard layout optimization"""

def optimize_layout_checkerboard():

	if (argv.verbose == 0):
		sys.stderr.write("o")
	info(1, "Constructing a checkerboard layout")

	layout = LayoutBuilder.compute_checkerboard_layout()

	result = find_maximum_power_budget(layout)

        if result == None:
            return None

	print "RESULT = ", result
	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]



