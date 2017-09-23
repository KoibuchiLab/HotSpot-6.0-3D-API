#!/usr/bin/python

import math
import random
import os
import sys
import itertools

import argparse
from argparse import RawTextHelpFormatter

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
		LayoutBuilder()
		PowerOptimizer()

"""Tool function to pick a random element from an array"""

def pick_random_element(array):
	return array[random.randint(0, len(array) - 1)]

"""Stacked layout optimization"""

def optimize_layout_stacked():

	if (argv.verbose == 0):
		sys.stderr.write("o")
	if (argv.verbose > 0):
		sys.stderr.write("Constructing a stacked layout\n")

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
	if (argv.verbose > 0):
		sys.stderr.write("Constructing a " + mode + " rectilinear layout\n")

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
	
			
"""Helper function that returns a randomly placed rectangle that overlaps
   with another rectangle by a fixed amount, avoiding all negative coordinates
	- rectangle1_bottom_left = [x,y]: bottom left corner of the initial rectangle
	- rectangle_dimensions = [x,y]: size of the rectangle sides
	- overlap: the fraction of overlap
   returns:
	- [x,y]: bottom left corner of the new rectangle
"""

def get_random_overlapping_rectangle(rectangle1_bottom_left, rectangle_dimensions, overlap):
		
	 [rectangle1_x, rectangle1_y] = rectangle1_bottom_left
	 [dim_x, dim_y] = rectangle_dimensions

         candidates = []

         # Assume for now that the overlap is in the North-East region
         # pick an x value
         picked_x = random.uniform(rectangle1_x, rectangle1_x + dim_x - overlap * dim_x)

         # compute the y value that makes the right overlap
         picked_y = rectangle1_y + dim_y - (overlap * dim_x * dim_y) / (rectangle1_x  + dim_x - picked_x)

	 # Add this to the set of candidates
         candidates.append([picked_x, picked_y]) 

         # Consider all other symmetries

         # South-East
         new_picked_x = picked_x
         new_picked_y = (rectangle1_y  + dim_y) - picked_y - dim_y
	 if (new_picked_x >= 0) and (new_picked_y >= 0):
		candidates.append([new_picked_x, new_picked_y])
         
         # North-West
         new_picked_x = (rectangle1_x + dim_x) - picked_x - dim_x
         new_picked_y = picked_y
	 if (new_picked_x >= 0) and (new_picked_y >= 0):
		candidates.append([new_picked_x, new_picked_y])

         # South-West
         new_picked_x = (rectangle1_x + dim_x) - picked_x - dim_x
         new_picked_y = (rectangle1_y + dim_y) - picked_y - dim_y
	 if (new_picked_x >= 0) and (new_picked_y >= 0):
		candidates.append([new_picked_x, new_picked_y])

	 # At this point, we just pick one of the candidates at random
 	 return pick_random_element(candidates)	



"""Linear random greedy layout optimization"""

def optimize_layout_linear_random_greedy():

	# Create an initial layout
	layout = Layout(argv.chip, [[1, 0.0, 0.0]], argv.medium, argv.overlap)

	
	max_num_random_trials = 5  # TODO: Don't hardcode this
	while (layout.get_num_chips() != argv.num_chips):
                if (argv.verbose > 0):
                        sys.stderr.write("* Generating " + str(max_num_random_trials) + " candidate positions for chip #" + str(1 + layout.get_num_chips()) + " in the layout\n")
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
			[picked_x, picked_y] = get_random_overlapping_rectangle([last_chip_position[1], last_chip_position[2]], [layout.get_chip().x_dimension, layout.get_chip().y_dimension], argv.overlap)

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
                        if (argv.verbose > 0):
                                sys.stderr.write("- Evaluating candidate " + str(candidate) + "\n")
                        result = find_maximum_power_budget(layout) 
                        if (result != None):
                            [power_distribution, temperature] = result
                            if (sum(power_distribution) > max_power):
                                picked_candidate = candidate
                        layout.remove_chip(layout.get_num_chips() - 1)
                        
                # Add the candidate 
                if (argv.verbose > 0):
                        sys.stderr.write("Picked candidate: " + str(candidate) + "\n")
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
                if (argv.verbose > 0):
                        sys.stderr.write("* Generating " + str(max_num_random_trials) + " candidate positions for chip #" + str(1 + layout.get_num_chips()) + " in the layout\n")
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
			[picked_x, picked_y] = get_random_overlapping_rectangle([last_chip_position[1], last_chip_position[2]], [layout.get_chip().x_dimension, layout.get_chip().y_dimension], argv.overlap)

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
                        if (argv.verbose > 0):
                                sys.stderr.write("- Evaluating candidate " + str(candidate) + "\n")
                        result = find_maximum_power_budget(layout) 
                        if (result != None):
                            [power_distribution, temperature] = result
                            if (sum(power_distribution) > max_power):
                                picked_candidate = candidate
                        layout.remove_chip(layout.get_num_chips() - 1)
                        
                # Add the candidate 
                if (argv.verbose > 0):
                        sys.stderr.write("Picked candidate: " + str(candidate) + "\n")
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
	if (argv.verbose > 0):
		sys.stderr.write("Constructing a checkerboard layout\n")

	layout = LayoutBuilder.compute_checkerboard_layout()

	result = find_maximum_power_budget(layout)

        if result == None:
            return None

	print "RESULT = ", result
	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]


""" Function to take a continuous power distribution and make it feasible by rounding up
    power specs to available discrete DFVS power levels. (doing some "clever" optimization
    to try to regain some of the lost power due to rounding off)
"""

def make_power_distribution_feasible(layout, power_distribution, initial_temperature):

        new_temperature = initial_temperature

        if (argv.verbose > 0):
            sys.stderr.write("Continuous solution: Total= " + str(sum(power_distribution)) + "; Distribution= " + str(power_distribution) + "\n")

        power_levels = layout.get_chip().get_power_levels(argv.power_benchmark)


        lower_bound = []
        for x in power_distribution:
            for i in xrange(len(power_levels)-1, -1, -1):
                if (power_levels[i] <= x):
                    lower_bound.append(i)
                    break

        if (argv.verbose > 0):
            sys.stderr.write("Conservative feasible power distribution: " + str([power_levels[i] for i in lower_bound]) + "\n")

        # exhaustively increase while possible (TODO: do a better heuristic? unclear)
        while (True):
            was_able_to_increase = False
            for i in xrange(0, len(lower_bound)):
                tentative_new_bound = lower_bound[:]
                if (tentative_new_bound[i] < len(power_levels)-1):
                    tentative_new_bound[i] += 1
                    # Evaluate the temperate
                    tentative_power_distribution = [power_levels[x] for x in tentative_new_bound]
                    temperature = Layout.compute_layout_temperature(layout, tentative_power_distribution)
                    if (temperature <= argv.max_allowed_temperature):
                        lower_bound = tentative_new_bound[:]
                        new_temperature = temperature
                        was_able_to_increase = True
                        if (argv.verbose > 0):
                            sys.stderr.write("Improved feasible power distribution: " + str([power_levels[i] for i in lower_bound]) + "\n")
                        break
            if (not was_able_to_increase):
                break


        return ([power_levels[x] for x in lower_bound], new_temperature)




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


def abort(message):
	sys.stderr.write("Error: " + message + "\n")
	sys.exit(1)

