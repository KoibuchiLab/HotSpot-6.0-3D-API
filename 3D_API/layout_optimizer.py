#!/usr/bin/python

import math
import random
import os
import sys
import subprocess

from glob import glob

import argparse
from argparse import RawTextHelpFormatter
from math import sqrt


import numpy as np
from scipy.optimize import basinhopping
from scipy.optimize import fmin_slsqp

##############################################################################################
### CLASSES
##############################################################################################


"""A class that represents a chip"""
class Chip(object):

	def __init__(self, name, x_dimension, y_dimension, min_power, max_power):
		self.name = name
		self.x_dimension = x_dimension
		self.y_dimension = y_dimension
		self.min_power = min_power
		self.max_power = max_power


"""A class that represents a layout of chips"""
class Layout(object):

	def __init__(self, chip, chip_positions,  medium):
		self.chip = chip
		self.medium = medium
		#  [[layer, x, y], ..., [layer, x, y]]
		self.chip_positions = chip_positions
		
	def get_num_chips(self):
		return len(self.chip_positions)

	def add_new_chip(self, layer, x, y):
		if (not self.can_new_chip_fit(layer, x, y)):
			abort("Can't add chip to layout")
		self.chip_positions.appeng([layer, x, y])
		
	def can_new_chip_fit(self, layer, x, y):
		for i in xrange(0, len(self.chip_positions)):
			existing_chip = self.chip_positions[i]
			if (existing_chip[0] != layer):
				continue
			if (self.are_two_rectangles_overlapping(
					[existing_chip[1], existing_chip[2]],
					[existing_chip[1] + self.chip.x_dimension, existing_chip[2] + self.chip.y_dimension],	
					[x, y],
					[x + self.chip.x_dimension, y + self.chip.y_dimension]
				)):
				return False
		return True

        def are_two_rectangles_overlapping(self, bottom_left_1, top_right_1,
				        bottom_left_2, top_right_2):
		        
	        # They don't overlap in X
	        if (top_right_1[0] < bottom_left_2[0]):
		        return False;
	        if (top_right_2[0] < bottom_left_1[0]):
		        return False;
        
	        # They don't overlap in Y
	        if (top_right_1[1] < bottom_left_2[1]):
		        return False;
	        if (top_right_2[1] < bottom_left_1[1]):
		        return False;
        
	        return True

##############################################################################################
### HOTSPOT INTERFACE
##############################################################################################

def compute_layout_temperature(x, layout):

	# This is a hack because it seems the scipy library ignores the bounds and will go into
        # unallowed values, so instead we return a very high temperature (lame)
	for i in range(0, layout.get_num_chips()):
		if ((x[i] < layout.chip.min_power) or (x[i] > layout.chip.max_power)):
			return 100000


	# Create the input file and ptrace_files
	input_file_name = "/tmp/layout-optimization-tmp.data"
	ptrace_file_names = []
	input_file = open(input_file_name, 'w')	
	for i in range(0, layout.get_num_chips()):
		# Create a line in the input file
		suffix = "layout-optimization-tmp-" + str(i)
		input_file.write(layout.chip.name + " " + str(layout.chip_positions[i][0]) + " " + str(layout.chip_positions[i][1]) + " " + str(layout.chip_positions[i][2]) + " " + suffix + " " + "0\n")
		# Create the (temporary) ptrace file
		ptrace_file_name = create_ptrace_file("./PTRACE", layout.chip, suffix, x[i])
		ptrace_file_names.append(ptrace_file_name)
	input_file.close()
	
	# Call hotspot
	command_line = "./hotspot.py " + input_file_name + " " + layout.medium + " --no_images"
	try:
		devnull = open('/dev/null', 'w')
		proc = subprocess.Popen(command_line, stdout=subprocess.PIPE, shell=True, stderr=devnull)
	except Exception, e:
    		sys.stderr.write("Could not invoke hotspot.py correctly: " + str(e))
		sys.exit(1)
	
	string_output = proc.stdout.read().rstrip()
	try:
		temperature = float(string_output)
	except:
		sys.stderr.write("Cannot convert HotSpot output ('" + string_output + "') to float\n")
		sys.exit(1)
	
	# Remove files
	try:
		os.remove(input_file_name)
		for file_name in ptrace_file_names:
			os.remove(file_name)
	except Exception, e:	
		sys.stderr.write("Warning: Cannot remove some tmp files...\n")
		
	if (argv.verbose > 1):
		sys.stderr.write("Hotspot result: " + str(sum(x)) + " (" + str(x) + "): " + str(temperature) + " Celsius\n")

	return temperature



def create_ptrace_file(directory, chip, suffix, power):
	ptrace_file_name = directory + "/" + chip.name + "-" + suffix + ".ptrace"
	ptrace_file = open(ptrace_file_name, 'w')
	
	if (chip.name == "e5-2667v4"):
		power_per_core = power / 8
		ptrace_file.write("NULL0 NULL1 NULL2 NULL3 0_CORE 1_CORE 2_CORE 3_CORE 4_CORE 5_CORE 6_CORE 7_CORE 0_LL 1_LL 2_LL 3_LL 4_LL 5_LL 6_LL 7_LL\n")
		ptrace_file.write("0 " * 4)
		ptrace_file.write((str(power_per_core) + " ") * 8)
		ptrace_file.write("0 " * 8)	# TODO TODO TODO
		ptrace_file.write("\n")

	elif (chip.name == "phi7250"):
		power_per_core = power / (2.0 * 42.0)
		ptrate_file.write("EDGE_0 EDGE_1 EDGE_2 EDGE_3 0_NULL_0 0_NULL_1 0_CORE_0 0_CORE_1 1_NULL_0 1_NULL_1 1_CORE_0 1_CORE_1 2_NULL_0 2_NULL_1 2_CORE_0 2_CORE_1 3_NULL_0 3_NULL_1 3_CORE_0 3_CORE_1 4_NULL_0 4_NULL_1 4_CORE_0 4_CORE_1 5_NULL_0 5_NULL_1 5_CORE_0 5_CORE_1 6_NULL_0 6_NULL_1 6_CORE_0 6_CORE_1 7_NULL_0 7_NULL_1 7_CORE_0 7_CORE_1 8_NULL_0 8_NULL_1 8_CORE_0 8_CORE_1 9_NULL_0 9_NULL_1 9_CORE_0 9_CORE_1 10_NULL_0 10_NULL_1 10_CORE_0 10_CORE_1 11_NULL_0 11_NULL_1 11_CORE_0 11_CORE_1 12_NULL_0 12_NULL_1 12_CORE_0 12_CORE_1 13_NULL_0 13_NULL_1 13_CORE_0 13_CORE_1 14_NULL_0 14_NULL_1 14_CORE_0 14_CORE_1 15_NULL_0 15_NULL_1 15_CORE_0 15_CORE_1 16_NULL_0 16_NULL_1 16_CORE_0 16_CORE_1 17_NULL_0 17_NULL_1 17_CORE_0 17_CORE_1 18_NULL_0 18_NULL_1 18_CORE_0 18_CORE_1 19_NULL_0 19_NULL_1 19_CORE_0 19_CORE_1 20_NULL_0 20_NULL_1 20_CORE_0 20_CORE_1 21_NULL_0 21_NULL_1 21_CORE_0 21_CORE_1 22_NULL_0 22_NULL_1 22_CORE_0 22_CORE_1 23_NULL_0 23_NULL_1 23_CORE_0 23_CORE_1 24_NULL_0 24_NULL_1 24_CORE_0 24_CORE_1 25_NULL_0 25_NULL_1 25_CORE_0 25_CORE_1 26_NULL_0 26_NULL_1 26_CORE_0 26_CORE_1 27_NULL_0 27_NULL_1 27_CORE_0 27_CORE_1 28_NULL_0 28_NULL_1 28_CORE_0 28_CORE_1 29_NULL_0 29_NULL_1 29_CORE_0 29_CORE_1 30_NULL_0 30_NULL_1 30_CORE_0 30_CORE_1 31_NULL_0 31_NULL_1 31_CORE_0 31_CORE_1 32_NULL_0 32_NULL_1 32_CORE_0 32_CORE_1 33_NULL_0 33_NULL_1 33_CORE_0 33_CORE_1 34_NULL_0 34_NULL_1 34_CORE_0 34_CORE_1 35_NULL_0 35_NULL_1 35_CORE_0 35_CORE_1 36_NULL_0 36_NULL_1 36_CORE_0 36_CORE_1 37_NULL_0 37_NULL_1 37_CORE_0 37_CORE_1 38_NULL_0 38_NULL_1 38_CORE_0 38_CORE_1 39_NULL_0 39_NULL_1 39_CORE_0 39_CORE_1 40_NULL_0 40_NULL_1 40_CORE_0 40_CORE_1 41_NULL_0 41_NULL_1 41_CORE_0 41_CORE_1")
		# 0 0 0 0 0 0 1.800 1.800 0 0 1.800 1.800 0 0 0 0 0 0 0 0 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 0 0 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 0 0 0 0 0 0 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 0 0 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 1.800 1.800 0 0 0 0 0 0 0 0 0 0 1.800 1.800 0 0 1.800 1.800
		ptrace_file.write("0 " * 6)
		ptrace_file.write((str(power_per_core) + " ") * 2)
		ptrace_file.write("0 " * 2)
		ptrace_file.write((str(power_per_core) + " ") * 2)
		ptrace_file.write("0 " * 10)
		for i in xrange(0, 13):
			ptrace_file.write((str(power_per_core) + " ") * 2)
			ptrace_file.write("0 " * 2)
		ptrace_file.write((str(power_per_core) + " ") * 2)
		ptrace_file.write("0 " * 6)
		for i in xrange(0, 3):
			ptrace_file.write((str(power_per_core) + " ") * 2)
			ptrace_file.write("0 " * 2)
		ptrace_file.write((str(power_per_core) + " ") * 2)
		ptrace_file.write("0 " * 10)
		for i in xrange(0,3):
			ptrace_file.write((str(power_per_core) + " ") * 2)
			ptrace_file.write("0 " * 2)
		ptrace_file.write((str(power_per_core) + " ") * 2)
		ptrace_file.write("0 " * 6)
		for i in xrange(0,7):
			ptrace_file.write((str(power_per_core) + " ") * 2)
			ptrace_file.write("0 " * 2)
		ptrace_file.write((str(power_per_core) + " ") * 2)
		ptrace_file.write("0 " * 10)
		ptrace_file.write((str(power_per_core) + " ") * 2)
		ptrace_file.write("0 " * 2)
		ptrace_file.write((str(power_per_core) + " ") * 2)
		ptrace_file.write("\n")

	else:
		sys.stderr.write("Error: Chip '" + chip.name+ "' unsupported!\n")
		sys.exit(1)

	ptrace_file.close()	
	return ptrace_file_name



##############################################################################################
### POWER DISTRIBUTION OPTIMIZATION (FOR A GIVEN LAYOUT and POWER BUDGET) 
##############################################################################################

"""Tool function to generate a decent random starting point power distribution for searching"""
def generate_random_start(layout, total_power_budget):
	# Generate a valid random start
	random_start = []
	for i in range(0, layout.get_num_chips()):
		random_start.append(layout.chip.max_power)

	while (True):
		extra = sum(random_start) - total_power_budget
		if (extra <= 0):
			break
		# pick a victim
		victim = random.randint(0, layout.get_num_chips() - 1)
		# decrease the victim by something that makes sense
		reduction = random.uniform(0, min(extra, random_start[victim] - layout.chip.min_power))
		random_start[victim]  -= reduction

	return random_start


""" This function computes a power distribution that minimizes the temperature, and returns
    both the power distribution and the temperature, for a given power budget"""
def optimize_power_distribution(layout, total_power_budget, optimization_method, num_random_starts, num_iterations):

	min_temperature = -1
	best_power_distribution = []

	# Do the specified number of minimization trial
	for trial in range(0, num_random_starts):
		if (argv.verbose == 0):
			sys.stderr.write(".")
		if (argv.verbose >= 1):
			sys.stderr.write("       New trial for power distribution optimization - aiming for lowest temperature\n")

		[temperature, power_distribution] = minimize_temperature(layout, total_power_budget, optimization_method, num_iterations)
		
		if ((min_temperature == -1) or (temperature < min_temperature)):
			min_temperature = temperature
			best_power_distribution = power_distribution
			if (argv.verbose >= 1):
				sys.stderr.write("          New lowest temperature: T= " + str(min_temperature) + "\n");
	
	return [min_temperature, best_power_distribution]



"""Top-level minimization function"""
def minimize_temperature(layout, total_power_budget, optimization_method, num_iterations):

	if (optimization_method == "simulated_annealing"):
		return minimize_temperature_simulated_annealing(layout, total_power_budget, num_iterations)
	elif (optimization_method == "gradient"):
		return minimize_temperature_gradient(layout, total_power_budget, num_iterations)
	elif (optimization_method == "random"):
		return minimize_temperature_random(layout, total_power_budget, num_iterations)
	elif (optimization_method == "uniform"):
		return minimize_temperature_uniform(layout, total_power_budget, num_iterations)
	else:
		sys.stderr.write("Error: Unknown optimizastion method '" + optimizastion_method + "'")


"""Just using a uniform power distribution"""
def minimize_temperature_uniform(layout, total_power_budget, num_iterations):
	
	# Generate a uniform power distribution
        uniform_distribution = layout.get_num_chips() * [ total_power_budget / layout.get_num_chips()]

	# Compute the temperature
	temperature =  compute_layout_temperature(uniform_distribution, layout)

	return [temperature, uniform_distribution]



"""Temperature minimizer using a simple random search"""
def minimize_temperature_random(layout, total_power_budget, num_iterations):
	
	# Generate a valid random start
	random_start = generate_random_start(layout, total_power_budget)
	if (argv.verbose > 1):
		sys.stderr.write("Generated a random start: " + str(random_start) + "\n")

	# Compute the temperature
	temperature =  compute_layout_temperature(random_start, layout)

	return [temperature, random_start]


"""Temperature minimizer using some gradient descent"""
def minimize_temperature_gradient(layout, total_power_budget, num_iterations):

        # Generate a valid random start
	random_start = generate_random_start(layout, total_power_budget)
	if (argv.verbose > 1):
		sys.stderr.write("Generated a random start: " + str(random_start) + "\n")

        result = fmin_slsqp(compute_layout_temperature, random_start, args=(layout,), full_output=True, iprint=0)

        return [result[1], result[0]]


"""Temperature minimizer using some simulated annealing and gradient descent"""
def minimize_temperature_simulated_annealing(layout, total_power_budget, num_iterations):
	
	# Generate a valid random start
	random_start = generate_random_start(layout, total_power_budget)
	if (argv.verbose > 1):
		sys.stderr.write("Generated a random start: " + str(random_start) + "\n")

	# Define constraints
	constraints = ({'type': 'eq', 'fun': lambda x:  sum(x) - total_power_budget},)

	# Define bounds (these seem to be ignored by the local minimizer - to investigate TODO)
	bounds = ()
	for i in range(0, layout.get_num_chips()):
		bounds = bounds + ((layout.chip.min_power, layout.chip.max_power),)

	# Call the basinhoping algorithm with a local minimizer that handles constraints and bounds: SLSQP
	minimizer_kwargs = {
		"method": "SLSQP", 
		"args" : layout, 
            	"constraints": constraints,
		"bounds": bounds,
	}
	
	#ret = basinhopping(layout_temperature, random_start, minimizer_kwargs=minimizer_kwargs, niter=num_iterations, accept_test=MyBounds())
	ret = basinhopping(basinhopping_objective_layout_temperature, random_start, minimizer_kwargs=minimizer_kwargs, niter=num_iterations)

	# sys.stderr.write("global minimum:  = %.4f,%.4f f(x0) = %.4f" % (ret.x[0], ret.x[1], ret.fun))
	return [ret.fun, list(ret.x)]


def basinhopping_objective_layout_temperature(x, layout):

	return compute_layout_temperature(x, layout)


##############################################################################################
### POWER OPTIMIZATION (FOR A GIVEN LAYOUT)
##############################################################################################

"""Binary search to optimize power"""
def find_maximum_power_budget(layout):

	# No binary search?
	if (argv.power_budget):
		[temperature, power_distribution] = optimize_power_distribution(layout, argv.power_budget, argv.powerdistopt, argv.power_distribution_optimization_num_trials, argv.temp_optimization_num_iterations)
		return [layout, power_distribution, temperature]

	# Binary search
	max_possible_power = argv.num_chips * argv.chip.max_power

	power_attempt = max_possible_power
	next_step_magnitude = (power_attempt - argv.num_chips * argv.chip.min_power) 
	next_step_direction = -1

	last_valid_solution = None

        if (argv.verbose > 0):
	    sys.stderr.write("New binary search for maximizing the power\n");

	while (True):
		if (argv.verbose == 0):
			sys.stderr.write("x")
		if (argv.verbose > 0):
			sys.stderr.write("    New binary search step (trying power = " + str(power_attempt) + " Watts)\n");

		[temperature, power_distribution] = optimize_power_distribution(layout, power_attempt, argv.powerdistopt, argv.power_distribution_optimization_num_trials, argv.temp_optimization_num_iterations)
		# pick new direction?
		if (temperature < argv.max_allowed_temperature):
			next_step_direction = +1
		else:
			next_step_direction = -1

		# is it a valid solution? (let's record it just in case the optimization process is chaotic)
		if (temperature < argv.max_allowed_temperature):
			last_valid_solution = [power_distribution, temperature]

		# decrease step size
		next_step_magnitude /= 2.0
		if (next_step_magnitude < argv.power_binarysearch_epsilon):
			break
		if ((temperature < argv.max_allowed_temperature) and (power_attempt == max_possible_power)):
			break

		# compute the next power attempt
		power_attempt += next_step_direction * next_step_magnitude
		
	return last_valid_solution
	

##############################################################################################
### LAYOUT OPTIMIZATION
##############################################################################################

"""Tool function to pick a random element from an array"""
def random_element(array):
	return array[random.randint(0, len(array) - 1)]

"""Function to compute a straight linear layout"""
def compute_rectilinear_straight_layout():

	positions = []

	current_level = 1
	level_direction = 1
	current_x_position = 0.0
	current_y_position = 0.0
	for i in xrange(0, argv.num_chips):
		positions.append([current_level, current_x_position, current_y_position])
		current_level += level_direction
		if (current_level > argv.num_levels):
			current_level = argv.num_levels - 1
			level_direction = -1
		if (current_level < 1):
			current_level = 2
			level_direction = 1
		current_x_position += argv.chip.x_dimension * (1 - argv.overlap);
		
	return Layout(argv.chip, positions, argv.medium)

	
"""Function to compute a diagonal linear layout"""
def compute_rectilinear_diagonal_layout():

	positions = []

	current_level = 1
	level_direction = 1
	current_x_position = 0.0
	current_y_position = 0.0
	for i in xrange(0, argv.num_chips):
		positions.append([current_level, current_x_position, current_y_position])
		current_level += level_direction
		if (current_level > argv.num_levels):
			current_level = argv.num_levels - 1
			level_direction = -1
		if (current_level < 1):
			current_level = 2
			level_direction = 1
		current_x_position += argv.chip.x_dimension * (1 - sqrt(argv.overlap));
		current_y_position += argv.chip.y_dimension * (1 - sqrt(argv.overlap));
		
	return Layout(argv.chip, positions, argv.medium)

	
"""Linear layout optimization"""
def compute_best_solution_rectilinear(mode):

	if (argv.diameter != argv.num_chips -1):
		abort("A linear layout cannot have diameter " + argv.diameter)

	if (argv.verbose == 0):
		sys.stderr.write("o");
	if (argv.verbose > 0):
		sys.stderr.write("Constructing a " + mode + " rectilinear layout\n")

	if (mode == "straight"):
		layout = compute_rectilinear_straight_layout()
	elif (mode == "diagonal"):
		layout = compute_rectilinear_diagonal_layout()
	else:
		abort("Unknown rectilinear layout mode '" + mode + "'")

	[power_distribution, temperature] = find_maximum_power_budget(layout)

	return [layout, power_distribution, temperature]
	
			

"""Linear random greedy layout optimization"""
def compute_best_solution_linear_random_greedy():

	if (argv.diameter != argv.num_chips -1):
		abort("A linear layout cannot have diameter " + argv.diameter)

	# Create an initial layout
	layout = Layout(argv.chip, [[1, 0.0, 0.0]], argv.medium)

	
	max_num_random_trials = 5
	while (layout.get_num_chips() != argv.num_chips):
                if (argv.verbose > 0):
                        sys.stderr.write("* Generating " + str(max_num_random_trials) + " candidate positions for a chip #" + str(1 + layout.get_num_chips()) + " in the layout\n")
		num_random_trials = 0
                candidate_random_trials = []
		while (len(candidate_random_trials) < max_num_random_trials):
			last_chip_position = layout.chip_positions[-1]

			# Pick a random location relative to the last chip

			# level
			possible_levels = []
			if (last_chip_position[0] == 1):
				possible_levels = [2]
			elif (last_chip_position[0] == argv.num_levels):
				possible_levels = [argv.num_levels - 1]
			else:
				possible_levels = [last_chip_position[0]-1, last_chip_position[0]+1]

			picked_level = random_element(possible_levels)

                        # x/y coordinates:
                        #  assume for now that the overlap is in the North-East region
                        # pick an x value
                        picked_x = random.uniform(last_chip_position[1], 
                                last_chip_position[1] + layout.chip.x_dimension - \
                                        argv.overlap / layout.chip.y_dimension)

            
                        # compute the y value that makes the right overlap
                        picked_y = -argv.overlap / (last_chip_position[1] + layout.chip.x_dimension \
                                - picked_x) + (last_chip_position[2] + layout.chip.y_dimension)

                        #print "OVERLAP = ", (last_chip_position[1] + layout.chip.x_dimension  - picked_x) * (last_chip_position[2] + layout.chip.y_dimension - picked_y)

#                         file = open("base.m","w") 
#                         file.write("figure\n")
#                         file.write("hold on\n")
# 
#                         file.write("plot([" + str(last_chip_position[1]) + ", " + str(last_chip_position[1] + layout.chip.x_dimension) + "]" +  ", [" + str(last_chip_position[2]) + ", " + str(last_chip_position[2]) + "])\n") 
#                         file.write("plot([" + str(last_chip_position[1]) + ", " + str(last_chip_position[1] + layout.chip.x_dimension) + "]" +  ", [" + str(last_chip_position[2] + layout.chip.y_dimension) + ", " + str(last_chip_position[2] + layout.chip.y_dimension) + "])\n") 
#                         file.write("plot([" + str(last_chip_position[1]) + ", " + str(last_chip_position[1]) + "]" +  ", [" + str(last_chip_position[2]) + ", " + str(last_chip_position[2] + layout.chip.y_dimension) + "])\n") 
#                         file.write("plot([" + str(last_chip_position[1] + layout.chip.x_dimension) + ", " + str(last_chip_position[1] + layout.chip.x_dimension) + "]" +  ", [" + str(last_chip_position[2]) + ", " + str(last_chip_position[2] + layout.chip.y_dimension) + "])\n") 
# 
#  
#                         file.write("plot([" + str(picked_x) + ", " + str(picked_x + layout.chip.x_dimension) + "]" +  ", [" + str(picked_y) + ", " + str(picked_y) + "])\n") 
#                         file.write("plot([" + str(picked_x) + ", " + str(picked_x + layout.chip.x_dimension) + "]" +  ", [" + str(picked_y + layout.chip.y_dimension) + ", " + str(picked_y + layout.chip.y_dimension) + "])\n") 
#                         file.write("plot([" + str(picked_x) + ", " + str(picked_x) + "]" +  ", [" + str(picked_y) + ", " + str(picked_y + layout.chip.y_dimension) + "])\n") 
#                         file.write("plot([" + str(picked_x + layout.chip.x_dimension) + ", " + str(picked_x + layout.chip.x_dimension) + "]" +  ", [" + str(picked_y) + ", " + str(picked_y + layout.chip.y_dimension) + "])\n") 
 
 
                        # Symmetries 
                        four_sided_coin = random_element([0])

                        if (four_sided_coin == 0):   # North-East
                            # do nothing
                            pass

                        elif (four_sided_coin == 1): # South-East
                            # Apply a vertical symmetry
                            picked_x = picked_x
                            picked_y = (last_chip_position[2] + layout.chip.y_dimension) - \
                                           picked_y - layout.chip.y_dimension
                        
                        elif (four_sided_coin == 2): # North-West
                            # Apply a horizontal symmetry
                            picked_x = (last_chip_position[1] + layout.chip.x_dimension) - \
                                        picked_x - layout.chip.x_dimension
                            picked_y = picked_y

                        elif (four_sided_coin == 3): # South-West
                            # Apply a horizontal symmetry
                            picked_x = (last_chip_position[1] + layout.chip.x_dimension) - \
                                        picked_x - layout.chip.x_dimension
                            picked_y = (last_chip_position[2] + layout.chip.y_dimension) - \
                                           picked_y - layout.chip.y_dimension

 
#                        file.write("plot([" + str(picked_x) + ", " + str(picked_x + layout.chip.x_dimension) + "]" +  ", [" + str(picked_y) + ", " + str(picked_y) + "])\n") 
#                        file.write("plot([" + str(picked_x) + ", " + str(picked_x + layout.chip.x_dimension) + "]" +  ", [" + str(picked_y + layout.chip.y_dimension) + ", " + str(picked_y + layout.chip.y_dimension) + "])\n") 
#                        file.write("plot([" + str(picked_x) + ", " + str(picked_x) + "]" +  ", [" + str(picked_y) + ", " + str(picked_y + layout.chip.y_dimension) + "])\n") 
#                        file.write("plot([" + str(picked_x + layout.chip.x_dimension) + ", " + str(picked_x + layout.chip.x_dimension) + "]" +  ", [" + str(picked_y) + ", " + str(picked_y + layout.chip.y_dimension) + "])\n") 
#
#                        file.write("axis([-1 2 -1 2])\n")
#                        file.write("print base.pdf\n")
#                        file.close()


                        # Check that the chip can fit
                        if (not layout.can_new_chip_fit(picked_level, picked_x, picked_y)):
                            print "Can't fit!"
                            continue

                        candidate_random_trials.append([picked_level, picked_x, picked_y])

                # Pick a candidate
                max_power = -1
                picked_candidate = None
                for candidate in candidate_random_trials:
                        layout.chip_positions.append(candidate) 
                        if (argv.verbose > 0):
                                sys.stderr.write("- Evaluating candidate " + str(candidate) + "\n")
                        [power_distribution, temperature] = find_maximum_power_budget(layout) 
                        if (sum(power_distribution) > max_power):
                            picked_candidate = candidate
                        layout.chip_positions = layout.chip_positions[:-1]
                        
                # Add the candidate 
                if (argv.verbose > 0):
                        sys.stderr.write("Picked candidate: " + str(candidate) + "\n")
                layout.chip_positions.append(picked_candidate) 
                        

        # DO the final evaluation (which was already be done, but whatever)
        [power_distribution, temperature] = find_maximum_power_budget(layout) 

	return [layout, power_distribution, temperature]


def find_available_power_levels(chip_name, benchmark_name):
        
        power_levels = []

        filenames = glob("./PTRACE/" + chip_name + "-" +  benchmark_name + "*.ptrace")

        for filename in filenames:
                f = open(filename, "r")
                lines = f.readlines()
                f.close()
                power_levels.append(sum([float(x) for x in lines[1].rstrip().split(" ")]))

        power_levels.sort()
        return power_levels
        

def make_power_distribution_feasible(layout, power_distribution, initial_temperature):

        new_temperature = initial_temperature

        print "CONTINUOUS POWER LEVELS: ", power_levels

        power_levels = find_available_power_levels(argv.chip.name, "stress")
        print "AVAILABLE POWER LEVELS: ", power_levels


        lower_bound = []
        for x in power_distribution:
            for i in xrange(len(power_levels)-1, -1, -1):
                if (power_levels[i] <= x):
                    lower_bound.append(i)
                    break

#        print "LOW SOLUTION (indices): ", lower_bound
        print "LOWERED POWER LEVELS: ", [power_levels[i] for i in lower_bound]

        # exhaustively increase while possible (TODO: do a better heuristic? unclear)
        while (True):
            was_able_to_increase = False
            for i in xrange(0, len(lower_bound)):
                tentative_new_bound = lower_bound
                if (tentative_new_bound[i] < len(power_levels)-1):
                    tentative_new_bound[i] += 1
                    # Evaluate the temperate
                    tentative_power_distribution = [power_levels[x] for x in tentative_new_bound]
                    temperature = compute_layout_temperature(tentative_power_distribution, layout)
                    if (temperature <= argv.max_allowed_temperature):
                        lower_bound = tentative_new_bound
                        new_temperature = temperature
                        was_able_to_increase = True
                        @print "IMPROVED SOLUTION (indices): ", lower_bound
                        print "FEASIBLE IMPROVEMENT: ", [power_levels[i] for i in lower_bound]
                        break
            if (not was_able_to_increase):
                break


        return ([power_levels[x] for x in lower_bound], new_temperature)




"""Top-level optimization function"""
def compute_best_solution():


        # Compute continuous solution
	if (argv.layout_scheme == "rectilinear_straight"):
                continuous_solution = compute_best_solution_rectilinear("straight")
	elif (argv.layout_scheme == "rectilinear_diagonal"):
		continuous_solution =  compute_best_solution_rectilinear("diagonal")
	elif (argv.layout_scheme == "linear_random_greedy"):
		continuous_solution =  compute_best_solution_linear_random_greedy()
	else:
		abort("Layout scheme '" + argv.layout_scheme + "' is not supported")

        # Find the lower bound feasible solution that matches available frequencies 
        # (and will have lower overall power, sadly)
	[layout, power_distribution, temperature] = continuous_solution

        [power_distribution, temperature] = make_power_distribution_feasible(layout, power_distribution, temperature)

        return [layout, power_distribution, temperature]


########################################################
#####                    MAIN                     ######
########################################################

def parse_arguments():

	parser = argparse.ArgumentParser(epilog="""

LAYOUT SCHEMES (--layout, -L):

  - rectilinear_straight: 
       chips are along the x axis in a straight line, using all levels
       in a "bouncing ball" fashion

  - rectilinear_diagonal: 
       chips are along the x-y axis diagonal in a straight line, using
       all levels in a "bouncing ball" fashion

  - linear_random_greedy: 
       a greedy randomized search for a linear but non-rectilinear layout,
       using all levels in a "bouncing ball fashion". The main difference
       with the rectilinear methods is that the overlap between chip n
       and chip n+1 is arbitrarily shaped.

TEMPERATURE OPTIMIZATION METHODS ('--tempopt', '-t'):

  - uniform:
        baseline approach that simply assigns the same power to all chips. 
        Completely ignored the '--powerdistopt_num_trials', '-P' and the
        '--tempopt_num_iterations', '-T' options.

  - random: 
	given a layout and a given power budget, just do a random
	search. For this method there are X trials (as specified with
	'--powerdistopt_num_trials', '-P') and for each trial there
	are Y iterations (as specified with '--tempopt_num_iterations',
	'-T'). For this method, this simply means there are X*Y random
	attempts, and a typicall approach to do 1000 attempts would be
	'-P 1 -T 1000'. In other words, the notion ot "trial" here is
	not really needed.

  - gradient: 
	given a layout and a given power budget, just do a gradient
	descent.  (using scipy's fmin_slsqp constrained gradient descent
	algorithm).  For this method there are X trials (as specified
	with '--powerdistopt_num_trials', '-P') and for each trial there
	are Y iterations (as specified with '--tempopt_num_iterations',
	'-T'). Therefore, there are X random starting points and for
	each the gradient descent algorithm is invoked. Y is passed to
	the fmin_slsqp function as its number of iterations.


  - simulated_annealing
	given a layout and a given power budget, just do a simulated
	annealing search (using basinhopping from scipy, with the SLSQP
	constrained gradient descent algorithm).  For this method there
	are X trials (as specified with '--powerdistopt_num_trials',
	'-P') and for each trial there are Y iterations (as specified
	with '--tempopt_num_iterations', '-T'). Therefore, there are X
	random starting points and for each the basinhopping algorithm
	is invoked. Y is passed to the basinhopping algorithm as its
	number of iterations.



VISUAL PROGRESS OUTPUT:

  'o': a layout construction
  'x': a binary search step (searching for highest power)
  '.': a power distribution optimization trial (searching for lower temperature)

	""", 
	formatter_class=RawTextHelpFormatter)

	parser.add_argument('--medium', '-m', action='store', 
			    required=True, dest='medium', 
			    metavar='<cooling medium>',
                            help='"air", "oil", "water"')

	parser.add_argument('--chip', '-c', action='store', 
                            dest='chip_name', metavar='<chip name>',
                            required=True, help='options: "e5-2667v4", "phi7250"')

	parser.add_argument('--numchips', '-n', action='store', type=int,
                            dest='num_chips', metavar='<# of chips>',
                            required=True, help='the number of chips')

	parser.add_argument('--diameter', '-d', action='store', type=int,
                            dest='diameter', metavar='<diameter>',
                            required=True, help='the network diameter')

	parser.add_argument('--layout_scheme', '-L', action='store', 
                            dest='layout_scheme', metavar='<layout scheme>',
                            required=True, help='options: "rectilinear_straight", "rectilinear_diagonal", "linear_random_greedy"')

	parser.add_argument('--numlevels', '-l', action='store', type=int,
                            dest='num_levels', metavar='<# of levels>',
                            required=True, help='the number of vertical levels')

	parser.add_argument('--tempopt', '-t', action='store', 
			    required=True,
                            dest='powerdistopt', 
			    metavar='<power distribution optimization method>',
                            help='"uniform", "random", "gradient", "simulated_annealing"')

	parser.add_argument('--tempopt_num_iterations', '-T', action='store', 
			    required=True, type=int,
                            dest='temp_optimization_num_iterations', 
			    metavar='<# of iterations>',
                            help='number of iterations used for temperature optimization')

	parser.add_argument('--powerdistopt_num_trials', '-P', action='store', 
			    required=True, type=int,
                            dest='power_distribution_optimization_num_trials', 
			    metavar='<# of trials>',
                            help='number of trials used for power distribution optimization')

	parser.add_argument('--overlap', '-O', action='store', default = 1.0 / 9.0,
		            type=float, required=False,
                            dest='overlap', metavar='<chip area overlap>',
                            help='the fraction of chip area overlap fraction (default = 1/9)')

	parser.add_argument('--powerbudget', '-p', action='store',
		            type=float, required=False,
                            dest='power_budget', metavar='<total power>',
                            help='the power of the whole system (precludes the search for the maximum power)')

	parser.add_argument('--power_binarysearch_epsilon', '-b', action='store',
		            type=float, required=False, default=10,
                            dest='power_binarysearch_epsilon', metavar='<threshold in Watts>',
                            help='the step size, in Watts, at which the binary search for the total power budget stops (default = 0.1)')

	parser.add_argument('--max_allowed_temperature', '-a', action='store',
		            type=float, required=False, default=80,
                            dest='max_allowed_temperature', metavar='<temperature in Celsius>',
                            help='the maximum allowed temperature for the layout')

	parser.add_argument('--verbose', '-v', action='store', type=int,
		            required=False, default=0,
                            dest='verbose', metavar='<verbosity level>',
                            help='verbosity level for debugging/curiosity')

	return parser.parse_args()


def abort(message):
	sys.stderr.write("Error: " + message + "\n")
	sys.exit(1)


# Parse command-line arguments
argv = parse_arguments()

if (argv.chip_name == "e5-2667v4"):
	# TODO: REad values from files?  and specify benchmark name?
	#argv.chip = Chip("e5-2667v4", 0.012634, 0.014172, 59.47, 162.9)
        argv.chip = Chip("e5-2667v4", 0.012634, 0.014172, 59.47, 162.9)
elif (argv.chip_name == "phi7250"):
	# TODO: 10 and 100???
	argv.chip = Chip("phi7250",   0.0315,   0.0205,   10,   100.0)
else:
	abort("Chip '" + argv.chip_name + "' not supported")

if (argv.num_chips < 1):
	abort("The number of chips (--numchips, -n) should be >0")

if (argv.diameter < 1):
	abort("The diameter (--diameter, -d) should be >0")

if (argv.diameter > argv.num_chips):
	abort("The diameter (--diameter, -d) should <= the number of chips")

if (argv.num_levels < 2):
	abort("The number of levels (--numlevels, -d) should be >1")

if ((argv.overlap < 0.0) or (argv.overlap > 1.0)):
	abort("The overlap (--overlap, -O) should be between 0.0 and 1.0")

if (argv.temp_optimization_num_iterations < 0):
	abort("The number of iterations for temperature optimization (--tempopt_num_iterations, -T) should be between > 0")

if (argv.power_distribution_optimization_num_trials < 0):
	abort("The number of trials for power distribution optimization (--poweropt_num_trials, -P) should be between > 0")

if ((argv.medium != "water") and (argv.medium != "oil") and (argv.medium != "air")):
	abort("Unsupported cooling medium '" + argv.medium + "'")


[layout, power_distribution, temperature] = compute_best_solution()

print "----------- OPTIMIZATION RESULTS -----------------"
print "Layout =", layout.chip_positions
print "Power budget = ", sum(power_distribution)
print "Power distribution =", power_distribution
print "Temperature =", temperature

sys.exit(0)



#############################################################################################
#############################################################################################


