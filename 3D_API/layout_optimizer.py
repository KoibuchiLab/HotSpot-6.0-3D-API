#!/usr/bin/python

import math
import random
import os
import sys

from math import sqrt

import numpy as np

from scipy.optimize import basinhopping
from scipy.optimize import fmin_slsqp

from layout import *
from power_optimizer import *

import utils


##############################################################################################
### LAYOUT OPTIMIZATION
##############################################################################################


class LayoutOptimizer(object):
	
	def __init__(self):
		LayoutBuilder()
		PowerOptimizer()


"""Top-level optimization function"""
def optimize_layout():

        # Compute continuous solution
	if (utils.argv.layout_scheme == "stacked"):
                solution = optimize_layout_stacked()
	elif (utils.argv.layout_scheme == "rectilinear_straight"):
                solution = optimize_layout_rectilinear("straight")
	elif (utils.argv.layout_scheme == "rectilinear_diagonal"):
		solution =  optimize_layout_rectilinear("diagonal")
	elif (utils.argv.layout_scheme == "checkerboard"):
		solution =  optimize_layout_checkerboard()
	elif (utils.argv.layout_scheme == "linear_random_greedy"):
		solution =  optimize_layout_linear_random_greedy()
	elif (utils.argv.layout_scheme == "random_greedy"):
		solution =  optimize_layout_random_greedy()
	else:
		utils.abort("Layout scheme '" + utils.argv.layout_scheme + "' is not supported")

        return solution

"""Stacked layout optimization"""

def optimize_layout_stacked():

	if (utils.argv.verbose == 0):
		sys.stderr.write("o")

	utils.info(1, "Constructing a stacked layout")

	layout = LayoutBuilder.compute_stacked_layout(utils.argv.num_chips)

	result = find_maximum_power_budget(layout)

        if result == None:
            return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]
		
"""Linear layout optimization"""

def optimize_layout_rectilinear(mode):

	if (utils.argv.verbose == 0):
		sys.stderr.write("o")
	utils.info(1, "Constructing a " + mode + " rectilinear layout")

	if (mode == "straight"):
		layout = LayoutBuilder.compute_rectilinear_straight_layout(utils.argv.num_chips)
	elif (mode == "diagonal"):
		layout = LayoutBuilder.compute_rectilinear_diagonal_layout(utils.argv.num_chips)
	else:
		utils.abort("Unknown rectilinear layout mode '" + mode + "'")

	result = find_maximum_power_budget(layout)
        if (result == None):
            return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]
	
			

"""Linear random greedy layout optimization"""

def optimize_layout_linear_random_greedy():

	# Create an initial layout
	layout = Layout(utils.argv.chip, [[1, 0.0, 0.0]], utils.argv.medium, utils.argv.overlap)

	
	max_num_random_trials = 5  # TODO: Don't hardcode this
	while (layout.get_num_chips() != utils.argv.num_chips):
                utils.info(1, "* Generating " + str(max_num_random_trials) + " candidate positions for chip #" + str(1 + layout.get_num_chips()) + " in the layout")
		num_random_trials = 0
                candidate_random_trials = []
		while (len(candidate_random_trials) < max_num_random_trials):
			[picked_level, picked_x, picked_y] = layout.get_random_feasible_neighbor_position(-1)
                        candidate_random_trials.append([picked_level, picked_x, picked_y])
				
                # Pick a candidate
                max_power = -1
                picked_candidate = None
                for candidate in candidate_random_trials:

                        layout.add_new_chip(candidate) 
                        #print layout.get_chip_positions()
                        utils.info(1, "- Evaluating candidate " + str(candidate))
                        result = find_maximum_power_budget(layout) 
                        if (result != None):
                            [power_distribution, temperature] = result
                            if (temperature <= utils.argv.max_allowed_temperature) and (sum(power_distribution) > max_power):
                                picked_candidate = candidate
			try:
                        	layout.remove_chip(layout.get_num_chips() - 1)
			except Exception:
				utils.abort("Fatal error: Graph shouldn't be disconnected here!!");	
                        
                # Add the candidate 
                utils.info(1, "Picked candidate: " + str(candidate))
                layout.add_new_chip(picked_candidate) 
                        

        # Do the final evaluation (which was already be done, but whatever)
        result = find_maximum_power_budget(layout) 
        if (result == None):
            return None

        [power_distribution, temperature] = result

	return [layout, power_distribution, temperature]


"""Random greedy layout optimization"""

def optimize_layout_random_greedy():

	#utils.abort("optimize_layout_random_greedy() is not implemented yet")

	# Create an initial layout: For now, a diagonal rectilinear layout
	layout = LayoutBuilder.compute_rectilinear_diagonal_layout(utils.argv.diameter + 1)

	# While num_chips != desired num_chips
	#	while num_valid_candidates != NUM_CANDIDATES
   	#		pick a random chip in the layout
   	#		pick a random feasible neigbhor
   	#		add that neighbor to the layout
   	#		compute diameter
   	#		remove chip from the layout	
   	#		if diameter not too big:
   	#			add that chip position to the list of valid candidates
   	#	
   	#	At this point we have NUM_CANDIDATES candidates
   	#	for each candidate:
	#		add candidate
   	#		Compute power distribution  (if returns None: temperature is too high)
	#			- returns   power distribution AND temperature
   	#		remove candidate
	#	pick the best candidate (highest sum power, breaking ties by temperature)
	#	add it into the layout for good
   	#


	max_num_random_trials = 20 # TODO: Don't hardcode this
	while (layout.get_num_chips() != utils.argv.num_chips):
                utils.info(1, "* Generating " + str(max_num_random_trials) + " candidate positions for chip #" + str(1 + layout.get_num_chips()) + " in the layout")
		num_random_trials = 0
                candidate_random_trials = []
		while (len(candidate_random_trials) < max_num_random_trials):
			#print"trial %s\n"%len(candidate_random_trials)
			#utils.info(1,"layout.chip position is "+layout.chip_positions)
			# Pick a neighboring chip
			# TODO: NOT ALWAYS PICK A NEIGHBOR OF THE LAST CHIP
                        # TODO: I.E., DON'T PASS -1 THERE
			#[picked_level, picked_x, picked_y] = layout.get_random_feasible_neighbor_position(-1)
			#print"current diameter is %s\n"%layout.get_diameter()
			#print"num chips is %s\n"%layout.get_num_chips()
			random_chip = utils.pick_random_element(range(0, layout.get_num_chips())) 
			# cant add to two ends w/o violating diameter
			#print"layout contains %s chips\n"% layout.get_num_chips()
			#random_chip = utils.pick_random_element(layout.get_chip_positions())
			#print"chip positions are %s\n"%layout.get_chip_positions()
			#print"position 1 is %s\n"%layout.get_chip_positions(1)
			#print"random chip value is %s\n"%random_chip
			result = layout.get_random_feasible_neighbor_position(random_chip)
			if result == None: 
				continue
			[picked_level, picked_x, picked_y] = result
			utils.info(1, "Candidate random neighbor of chip " + str(random_chip) + " : " + str([picked_level, picked_x, picked_y]))
                        candidate_random_trials.append([picked_level, picked_x, picked_y])
			#print"candidate_random_trials contains %s\n"%candidate_random_trials
                # Pick a candidate
		print "CANDIDATES FOUND = ", candidate_random_trials
                max_power = -1
                picked_candidate = None
                for candidate in candidate_random_trials:
			print "TENTATIVELY ADDING ", candidate
                        layout.add_new_chip(candidate) 
                        #print layout.get_chip_positions()
                        if(layout.get_diameter()<=utils.argv.diameter):
                            utils.info(1, "- Layout diameter is good at value " + str(layout.get_diameter()))
                            utils.info(1, "- Evaluating candidate " + str(candidate))
                            result = find_maximum_power_budget(layout) 
                            if (result != None):
                                [power_distribution, temperature] = result
				utils.info(1, "  - Temperature = " + str(temperature))
                                if (sum(power_distribution) > max_power):
                                    picked_candidate = candidate
			else:
			    utils.info(1, "- Layout diameter is too big")

                        layout.remove_chip(layout.get_num_chips() - 1)
                        
                # Add the candidate 
		if picked_candidate == None:
			utils.abort("Could not find a candidate that met the temperature constraint")

                utils.info(1, "Picked candidate: " + str(candidate))
                layout.add_new_chip(picked_candidate) 

        # Do the final evaluation (which was already be done, but whatever)
        result = find_maximum_power_budget(layout) 
        if (result == None):
            return None

        [power_distribution, temperature] = result

	return [layout, power_distribution, temperature]



"""Checkboard layout optimization"""

def optimize_layout_checkerboard():

	if (utils.argv.verbose == 0):
		sys.stderr.write("o")
	utils.info(1, "Constructing a checkerboard layout")

	layout = LayoutBuilder.compute_checkerboard_layout(utils.argv.num_chips)

	result = find_maximum_power_budget(layout)

        if result == None:
            return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]



