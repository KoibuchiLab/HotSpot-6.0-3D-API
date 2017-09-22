#!/usr/bin/python

import math
import random
import os
import sys
import subprocess
import itertools

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

"""A convenient function that determines whether two rectangles are overlapping """
def are_two_rectangles_overlapping(bottom_left_1, top_right_1, bottom_left_2, top_right_2):
		        
        # They don't overlap in X
        if (top_right_1[0] < bottom_left_2[0]):
	        return False
        if (top_right_2[0] < bottom_left_1[0]):
	        return False
       
        # They don't overlap in Y
        if (top_right_1[1] < bottom_left_2[1]):
	        return False
        if (top_right_2[1] < bottom_left_1[1]):
	        return False
       
        return True


"""A class that represents a chip"""
class Chip(object):

        def __init__(self, name, x_dimension, y_dimension, power_levels):
		self.name = name
		self.x_dimension = x_dimension
		self.y_dimension = y_dimension
		self.power_levels = power_levels

"""A class that represents a layout of chips"""
class Layout(object):

	def __init__(self, chip, chip_positions,  medium, topology):
		self.chip = chip
		self.medium = medium
		#  [[layer, x, y], ..., [layer, x, y]]
		self.chip_positions = chip_positions
                #  [[edge src, edge dst], ..., [edge src, edge dst]]
                self.topology = topology
		
	def get_num_chips(self):
		return len(self.chip_positions)

	def add_new_chip(self, layer, x, y):
		if (not self.can_new_chip_fit(layer, x, y)):
			abort("Can't add chip to layout")
		self.chip_positions.append([layer, x, y])
		
	def can_new_chip_fit(self, layer, x, y):
		for i in xrange(0, len(self.chip_positions)):
			existing_chip = self.chip_positions[i]
			if (existing_chip[0] != layer):
				continue
			if (are_two_rectangles_overlapping(
					[existing_chip[1], existing_chip[2]],
					[existing_chip[1] + self.chip.x_dimension, existing_chip[2] + self.chip.y_dimension],	
					[x, y],
					[x + self.chip.x_dimension, y + self.chip.y_dimension]
				)):
				return False
		return True

        def draw_in_octave(self, filename_without_extension):
            file = open(filename + ".m","w") 
            file.write("figure\n")
            file.write("hold on\n")
    
            for rect in self.positions:
                [l,x,y] = rect
                w = argv.chip.x_dimension
                h = argv.chip.y_dimension
                colors = ["b", "r", "g", "c", "k", "m"]
                color = colors[l % len(colors)]

                file.write("plot([" + str(x) + ", " + str(x + w) + "," + str(x + w) + "," + str(x) + "," + str(x) + "]" +  ", [" + str(y) + ", " + str(y) + ", "+ str(y + h) + ", " + str(y + h) +", " + str(y) +  "], " + "'" + color + "-'" + ")\n") 
            file.write("print " + filename + ".pdf\n")
            file.close()
            sys.stderr.write("File '" + filename + ".m" + "' created")
            return

""" Function to determine the actual power levels for a chip and a benchmark
"""
def find_available_power_levels(chip_name, benchmark_name):
        
        power_levels = {}

        benchmarks = ["bc", "cg", "dc", "ep", "is", "lu", "mg", "sp", "ua", "stress"]

        # Get all the power levels
        for benchmark in benchmarks:

            power_levels[benchmark] = []

            filenames = glob("./PTRACE/" + chip_name + "-" +  benchmark + "*.ptrace")

            for filename in filenames:
                    f = open(filename, "r")
                    lines = f.readlines()
                    f.close()
                    power_levels[benchmark].append(sum([float(x) for x in lines[1].rstrip().split(" ")]))

            power_levels[benchmark].sort()

        if (benchmark_name in power_levels):
            return power_levels[benchmark_name]

        elif (benchmark_name == "overall_max"):
                lengths = [len(power_levels[x]) for x in power_levels]
                if (max(lengths) != min(lengths)):
                        abort("Cannot use the \"overall_max\" benchmark mode for power levels because some benchmarks have more power measurements than others")
                maxima = []
                for i in xrange(0, min(lengths)):
                    maxima.append(max([power_levels[x][i] for x in power_levels]))

                return maxima

        else:
                abort("Unknon benchmark " + benchmark_name + " for computing power levels")
 
##############################################################################################
### HOTSPOT INTERFACE
##############################################################################################

""" The top-level function that calls hotspot to find out the max temp of a layout
 		- power_distribution: the power distribution
		- layout: the layout
"""
def compute_layout_temperature(power_distribution, layout):

	# This is a hack because it seems the scipy library ignores the bounds and will go into
        # unallowed values, so instead we return a very high temperature (lame)
	for i in range(0, layout.get_num_chips()):
		if ((power_distribution[i] < layout.chip.power_levels[0]) or (power_distribution[i] > layout.chip.power_levels[-1])):
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
		ptrace_file_name = create_ptrace_file("./PTRACE", layout.chip, suffix, power_distribution[i])
		ptrace_file_names.append(ptrace_file_name)
	input_file.close()

	# Call hotspot
	command_line = "./hotspot.py " + input_file_name + " " + layout.medium + " --no_images"
	try:
		devnull = open('/dev/null', 'w')
		proc = subprocess.Popen(command_line, stdout=subprocess.PIPE, shell=True, stderr=devnull)
	except Exception, e:
    		abort("Could not invoke hotspot.py correctly: " + str(e))
	
	string_output = proc.stdout.read().rstrip()
	try:
		#tokens = string_output.split(" ")
		#temperature = float(tokens[2])
		temperature = float(string_output)
	except:
		abort("Cannot convert HotSpot output ('" + string_output + "') to float")
	
	# Remove files
	try:
		os.remove(input_file_name)
		for file_name in ptrace_file_names:
			os.remove(file_name)
	except Exception, e:	
		sys.stderr.write("Warning: Cannot remove some tmp files...\n")
		
	if (argv.verbose > 2):
		sys.stderr.write("          Hotspot result: " + str(sum(power_distribution)) + " (" + str(power_distribution) + "): " + str(temperature) + " Celsius\n")

	return temperature



""" A horrible function that creates the PTRACE files for each chip with a bunch of hardcoded
    stuff, but it's simpler than trying to come up with a programmatic solution
"""
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
		ptrace_file.write("EDGE_0 EDGE_1 EDGE_2 EDGE_3 0_NULL_0 0_NULL_1 0_CORE_0 0_CORE_1 1_NULL_0 1_NULL_1 1_CORE_0 1_CORE_1 2_NULL_0 2_NULL_1 2_CORE_0 2_CORE_1 3_NULL_0 3_NULL_1 3_CORE_0 3_CORE_1 4_NULL_0 4_NULL_1 4_CORE_0 4_CORE_1 5_NULL_0 5_NULL_1 5_CORE_0 5_CORE_1 6_NULL_0 6_NULL_1 6_CORE_0 6_CORE_1 7_NULL_0 7_NULL_1 7_CORE_0 7_CORE_1 8_NULL_0 8_NULL_1 8_CORE_0 8_CORE_1 9_NULL_0 9_NULL_1 9_CORE_0 9_CORE_1 10_NULL_0 10_NULL_1 10_CORE_0 10_CORE_1 11_NULL_0 11_NULL_1 11_CORE_0 11_CORE_1 12_NULL_0 12_NULL_1 12_CORE_0 12_CORE_1 13_NULL_0 13_NULL_1 13_CORE_0 13_CORE_1 14_NULL_0 14_NULL_1 14_CORE_0 14_CORE_1 15_NULL_0 15_NULL_1 15_CORE_0 15_CORE_1 16_NULL_0 16_NULL_1 16_CORE_0 16_CORE_1 17_NULL_0 17_NULL_1 17_CORE_0 17_CORE_1 18_NULL_0 18_NULL_1 18_CORE_0 18_CORE_1 19_NULL_0 19_NULL_1 19_CORE_0 19_CORE_1 20_NULL_0 20_NULL_1 20_CORE_0 20_CORE_1 21_NULL_0 21_NULL_1 21_CORE_0 21_CORE_1 22_NULL_0 22_NULL_1 22_CORE_0 22_CORE_1 23_NULL_0 23_NULL_1 23_CORE_0 23_CORE_1 24_NULL_0 24_NULL_1 24_CORE_0 24_CORE_1 25_NULL_0 25_NULL_1 25_CORE_0 25_CORE_1 26_NULL_0 26_NULL_1 26_CORE_0 26_CORE_1 27_NULL_0 27_NULL_1 27_CORE_0 27_CORE_1 28_NULL_0 28_NULL_1 28_CORE_0 28_CORE_1 29_NULL_0 29_NULL_1 29_CORE_0 29_CORE_1 30_NULL_0 30_NULL_1 30_CORE_0 30_CORE_1 31_NULL_0 31_NULL_1 31_CORE_0 31_CORE_1 32_NULL_0 32_NULL_1 32_CORE_0 32_CORE_1 33_NULL_0 33_NULL_1 33_CORE_0 33_CORE_1 34_NULL_0 34_NULL_1 34_CORE_0 34_CORE_1 35_NULL_0 35_NULL_1 35_CORE_0 35_CORE_1 36_NULL_0 36_NULL_1 36_CORE_0 36_CORE_1 37_NULL_0 37_NULL_1 37_CORE_0 37_CORE_1 38_NULL_0 38_NULL_1 38_CORE_0 38_CORE_1 39_NULL_0 39_NULL_1 39_CORE_0 39_CORE_1 40_NULL_0 40_NULL_1 40_CORE_0 40_CORE_1 41_NULL_0 41_NULL_1 41_CORE_0 41_CORE_1\n")
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
		abort("Error: Chip '" + chip.name+ "' unsupported!")

	ptrace_file.close()	
	return ptrace_file_name



##############################################################################################
### POWER DISTRIBUTION OPTIMIZATION (FOR A GIVEN LAYOUT and POWER BUDGET) 
##############################################################################################

"""Helper function to generate a decent random starting power distribution for searching"""
def generate_random_power_distribution(layout, total_power_budget):
	# Generate a valid random start
	power_distribution = []
	for i in range(0, layout.get_num_chips()):
		power_distribution.append(layout.chip.power_levels[-1])

	while (True):
		extra = sum(power_distribution) - total_power_budget
		if (extra <= 0):
			break
		# pick a victim
		victim = random.randint(0, layout.get_num_chips() - 1)
		# decrease the victim by something that makes sense
		reduction = random.uniform(0, min(extra, power_distribution[victim] - layout.chip.power_levels[0]))
		power_distribution[victim]  -= reduction

	return power_distribution


""" This function computes a power distribution that minimizes the temperature, and returns
    both the power distribution and the temperature, for a given power budget. It calls
    the "minimize_temperature" function to do its work

	- layout: the layout
	- total_power_budget: the total power budget
	- optimization_method: optimization method (see documentation)
	- num_random_starts: number of trials (if applicable) for the optimization
	- num_iterations: number of iterations (if applicable) for each trial
"""
def optimize_power_distribution(layout, total_power_budget, optimization_method, num_random_starts, num_iterations):

	min_temperature = -1
	best_power_distribution = []


	# Do the specified number of minimization trial
	for trial in range(0, num_random_starts):
		if (argv.verbose == 0):
			sys.stderr.write(".")
		if (argv.verbose >= 1):
			sys.stderr.write("       Temperature minimization trial for total power " + str(total_power_budget) + "\n")

		[temperature, power_distribution] = minimize_temperature(layout, total_power_budget, optimization_method, num_iterations)
		if ((min_temperature == -1) or (temperature < min_temperature)):
			min_temperature = temperature
			best_power_distribution = power_distribution
			if (argv.verbose >= 1):
				sys.stderr.write("          New lowest temperature: T= " + str(min_temperature) + "\n")
	
        
	return [min_temperature, best_power_distribution]

##############################################################################################
### TEMPERATURE MINIMIZATION (FOR A GIVEN LAYOUT and POWER BUDGET)
##############################################################################################



"""Top-level CONTINUOUS minimization function"""
def minimize_temperature(layout, total_power_budget, optimization_method, num_iterations):

	if (optimization_method == "simulated_annealing_gradient"):
		return minimize_temperature_simulated_annealing_gradient(layout, total_power_budget, num_iterations)
	elif (optimization_method == "neighbor"):
		return minimize_temperature_neighbor(layout, total_power_budget, num_iterations)
	elif (optimization_method == "gradient"):
		return minimize_temperature_gradient(layout, total_power_budget, num_iterations)
	elif (optimization_method == "random"):
		return minimize_temperature_random_continuous(layout, total_power_budget, num_iterations)
	elif (optimization_method == "uniform"):
		return minimize_temperature_uniform(layout, total_power_budget, num_iterations)
	else:
		abort("Error: Unknown optimization method '" + optimization_method)


"""Just using a uniform power distribution"""
def minimize_temperature_uniform(layout, total_power_budget, num_iterations):
	
	# Generate a uniform power distribution
        uniform_distribution = layout.get_num_chips() * [ total_power_budget / layout.get_num_chips()]

	# Compute the temperature
	temperature =  compute_layout_temperature(uniform_distribution, layout)

	return [temperature, uniform_distribution]


"""Temperature minimizer using a simple random CONTINUOUS search"""
def minimize_temperature_random_continuous(layout, total_power_budget, num_iterations):
	
	# Generate a valid random start
	random_start = generate_random_power_distribution(layout, total_power_budget)
	if (argv.verbose > 1):
		sys.stderr.write("\t\tRandom start: " + str(random_start) + "\n")

	# Compute the temperature
	temperature =  compute_layout_temperature(random_start, layout)

	return [temperature, random_start]


"""Temperature minimizer using gradient descent"""
def minimize_temperature_gradient(layout, total_power_budget, num_iterations):

        # Generate a valid random start
	random_start = generate_random_power_distribution(layout, total_power_budget)
	if (argv.verbose > 1):
		sys.stderr.write("\tGenerated a random start: " + str(random_start) + "\n")

        result = fmin_slsqp(compute_layout_temperature, random_start, args=(layout,), full_output=True, iter=num_iterations, iprint=0)

        return [result[1], result[0]]

"""Temperature minimizer using neighbor search"""
def minimize_temperature_neighbor(layout, total_power_budget, num_iterations):

        # Generate a valid random start
	random_start = generate_random_power_distribution(layout, total_power_budget)

        best_distribution = random_start
        best_temperature = compute_layout_temperature(random_start, layout)
	if (argv.verbose > 1):
		sys.stderr.write("\tGenerated a random start: " + str(best_distribution) + " (temperature = " + str(best_temperature) + ")\n")
        epsilon = 1
        for iteration in xrange(0, num_iterations):
            some_improvement = False
            for pair in list(itertools.product(xrange(0, layout.get_num_chips()), xrange(0, layout.get_num_chips()))):
                if (pair[0] == pair[1]):
                    continue
                candidate = list(best_distribution)
                candidate[pair[0]] += epsilon
                candidate[pair[1]] -= epsilon
                if (max(candidate) > max(layout.chip.power_levels)) or (min(best_distribution) < min(layout.chip.power_levels)):
                    continue
	        temperature =  compute_layout_temperature(candidate, layout)
                if (temperature < best_temperature):
                    if (argv.verbose > 1):
                        sys.stderr.write("\tNeighbor " + str(candidate) + " has temperature " + str(temperature) + "\n")
                    best_temperature = temperature
                    best_distribution = candidate
                    some_improvement = true
                    break  # We do a greedy search, which goes toward any improvement

            if (not some_improvement):
                break

        return [best_temperature, best_distribution]



"""Temperature minimizer using some simulated annealing and gradient descent"""
def minimize_temperature_simulated_annealing_gradient(layout, total_power_budget, num_iterations):
	
	# Generate a valid random start
	random_start = generate_random_power_distribution(layout, total_power_budget)
	if (argv.verbose > 1):
		sys.stderr.write("\tGenerated a random start: " + str(random_start) + "\n")

	# Define constraints
	constraints = ({'type': 'eq', 'fun': lambda x:  sum(x) - total_power_budget},)

	# Define bounds (these seem to be ignored by the local minimizer - to investigate TODO)
	bounds = ()
	for i in range(0, layout.get_num_chips()):
		bounds = bounds + ((layout.chip.power_levels[0], layout.chip.power_levels[-1]),)

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

""" Helper function to determine whether an optimization method is discrete or continuous
"""
def is_power_optimization_method_discrete(method_name):
    if method_name in ["exhaustive_discrete", "random_discrete", "greedy_random_discrete", "greedy_not_so_random_discrete", "uniform_discrete"]:
        return True
    else: 
        return False


"""Top-level function to Search for the maximum power"""
def find_maximum_power_budget(layout):

	# No search because the user specified a fixed power budget?
	if (argv.power_budget):
		[temperature, power_distribution] = optimize_power_distribution(layout, argv.power_budget, argv.powerdistopt, argv.power_distribution_optimization_num_trials, argv.power_distribution_optimization_num_iterations)
                [power_distribution, temperature] = make_power_distribution_feasible(layout, power_distribution, temperature)
		return [power_distribution, temperature]

	# No search because the minimum power possible is already above temperature?
        temperature = compute_layout_temperature([layout.chip.power_levels[0]] * layout.get_num_chips(), layout)
        if (temperature > argv.max_allowed_temperature):
                sys.stderr.write("Even setting all chips to minimum power gives a temperature of " + str(temperature) +", which is above the maximum allowed temperature of " + str(argv.max_allowed_temperature) + "\n")
                return None

	# No search because the maximum power possible is already below temperature?
        temperature = compute_layout_temperature([layout.chip.power_levels[-1]] * layout.get_num_chips(), layout)
        if (temperature <= argv.max_allowed_temperature):
		if (argv.verbose > 1):
			sys.stderr.write("We can set all chips to the max power level!")
                return [[layout.chip.power_levels[-1]] * layout.get_num_chips(), temperature]

	# DISCRETE?
        if is_power_optimization_method_discrete(argv.powerdistopt): 
                [power_distribution, temperature] = find_maximum_power_budget_discrete(layout)
                return [power_distribution, temperature]
        else: # OR CONTINUOUS?
                [power_distribution, temperature] = find_maximum_power_budget_continuous(layout)
                [power_distribution, temperature] = make_power_distribution_feasible(layout, power_distribution, temperature)
                return [power_distribution, temperature]


""" Top-level function for discrete power optimization, which for now implements all three methods
    therein
"""
def find_maximum_power_budget_discrete(layout):

        # Simple exhaustive search
        if (argv.powerdistopt == "exhaustive_discrete"):
		return find_maximum_power_budget_discrete_exhaustive(layout)
	elif (argv.powerdistopt == "random_discrete"):
		return find_maximum_power_budget_discrete_random(layout)
	elif (argv.powerdistopt == "greedy_random_discrete"):
		return find_maximum_power_budget_discrete_greedy_random(layout)
	elif (argv.powerdistopt == "greedy_not_so_random_discrete"):
		return find_maximum_power_budget_discrete_greedy_not_so_random(layout)
	elif(argv.powerdistopt == "uniform_discrete"):
		return find_maximum_power_budget_discrete_uniform(layout)
	else:
		abort("Unknown discrete power budget maximization method " + argv.powerdistopt)

""" Discrete uniform search
"""
def find_maximum_power_budget_discrete_uniform(layout):
		power_levels = layout.chip.power_levels
		best_power_level = None
		best_distribution_temperature = None
		for level in power_levels:
			temperature = compute_layout_temperature([level] * layout.get_num_chips(), layout)
			if (argv.verbose > 1):
				sys.stderr.write("With power level " + str(level) + " for all chips: temperature = " + str(temperature)+ "..\n");
			if (temperature<=argv.max_allowed_temperature):
				best_power_level = level
				best_distribution_temperature = temperature
			else:
				break
				
		return [[best_power_level] * layout.get_num_chips(), best_distribution_temperature]


""" Discrete exhaustive search 
"""
def find_maximum_power_budget_discrete_exhaustive(layout):

       power_levels = layout.chip.power_levels

       best_distribution = None
       best_distribution_temperature = None
       for distribution in itertools.permutations(power_levels,layout.get_num_chips()):
           temperature =  compute_layout_temperature(distribution, layout)
           if (temperature <= argv.max_allowed_temperature):
               if (best_distribution == None) or (sum(best_distribution) < sum(distribution)):
                   best_distribution = distribution
                   best_distribution_temperature = temperature
                   if (argv.verbose > 1):
                       sys.stderr.write("Better distribution: Total=" + str(sum(best_distribution)) + "; Distribution=" + str(best_distribution) + "; Temperature= " + str(best_distribution_temperature) + "\n")
           
       return [best_distribution, best_distribution_temperature]

""" Discrete random search 
"""
def find_maximum_power_budget_discrete_random(layout):
       power_levels = layout.chip.power_levels
       distribution = layout.chip.power_levels[0] * layout.get_num_chips(); 
       best_distribution = None
       best_distribution_temperature = None
           
       for trial in xrange(0, argv.power_distribution_optimization_num_trials):
           if (argv.verbose > 1):
               sys.stderr.write("Trial #"+str(trial)+"\n")
           distribution = []
           for i in xrange(0, layout.get_num_chips()):
               distribution.append(pick_random_element(power_levels))
           temperature =  compute_layout_temperature(distribution, layout)
           if (temperature <= argv.max_allowed_temperature):
               if (best_distribution == None) or (sum(best_distribution) < sum(distribution)):
                   best_distribution = distribution
                   best_distribution_temperature = temperature
                   if (argv.verbose > 1):
                       sys.stderr.write("Better Random Trial: Total=" + str(sum(best_distribution)) + "; Distribution=" + str(best_distribution) + "; Temperature= " + str(temperature) + "\n")

       return [best_distribution, best_distribution_temperature]


""" Discrete greedy random search 
"""
def find_maximum_power_budget_discrete_greedy_random(layout):
       power_levels = layout.chip.power_levels
       
       best_best_distribution = None
       best_best_distribution_temperature = None

       for trial in xrange(0, argv.power_distribution_optimization_num_trials):

           if (argv.verbose > 1):
               sys.stderr.write("Trial #"+str(trial)+"\n")

	   # Initialize the best distribution (that we're looking for)
           best_distribution_index = [0] * layout.get_num_chips() 
           best_distribution = [power_levels[x] for x in best_distribution_index]
               
           while (True):
               # pick one non-max chip
               while (True):
	           picked = pick_random_element(range(0, layout.get_num_chips()))
   	           if (best_distribution_index[picked] == len(power_levels) - 1):
        	       continue
                   else:
                       break

	       # increase the power of that chip, tentatively
               candidate_index = list(best_distribution_index)
               candidate_index[picked] += 1

	       # Compute the temperature
               candidate = [power_levels[x] for x in candidate_index]
               temperature =  compute_layout_temperature(candidate, layout)
               sys.stderr.write("Looking at: " + str(candidate) + " - Temperature = " + str(temperature) + "\n")

               # If too hot, nevermind and give up (don't evey try another)
               if (temperature > argv.max_allowed_temperature):
                   break

               # Otherwise, great
               best_distribution_index = list(candidate_index)
               best_distribution = list(candidate)
               best_distribution_temperature = temperature
           

           if (best_best_distribution == None) or (sum(best_distribution) > sum(best_best_distribution)):
               best_best_distribution = list(best_distribution)
               best_best_distribution_temperature = best_distribution_temperature

       return [best_distribution, best_distribution_temperature]

""" Discrete greedy not-so-random search 
"""
def find_maximum_power_budget_discrete_greedy_not_so_random(layout):
       power_levels = layout.chip.power_levels
       
       best_best_distribution = None
       best_best_distribution_temperature = None

       for trial in xrange(0, argv.power_distribution_optimization_num_trials):

           if (argv.verbose > 1):
               sys.stderr.write("Trial #"+str(trial)+"\n")

	   # Initialize the best distribution (that we're looking for)
           best_distribution_index = [0] * layout.get_num_chips() 
           best_distribution = [power_levels[x] for x in best_distribution_index]
      	   best_temperature =  compute_layout_temperature(best_distribution, layout)
               
           while (True):
	       # Evaluate all possible increases
	       pay_off = []
               if (argv.verbose > 1):
                    sys.stderr.write("Looking at all neighbors...\n")
 	       for i in xrange(0, layout.get_num_chips()):
			# If we're already at the max, set the payoff to a <0 value
			if (best_distribution_index[i] == len(power_levels) - 1):
				pay_off.append(-1.0)
                                continue
			# Otherwise compute the payoff
               		candidate_index = list(best_distribution_index)
               		candidate_index[i] += 1
			power_increase = power_levels[candidate_index[i]] - power_levels[candidate_index[i]-1]
               		candidate = [power_levels[x] for x in candidate_index]
               		temperature =  compute_layout_temperature(candidate, layout)
			if (temperature > argv.max_allowed_temperature):
				pay_off.append(-1.0)
			else:
				temperature_increase = temperature - best_temperature
				pay_off.append(power_increase / temperature_increase)

	       # If all negative, we're done
	       if (max(pay_off) < 0.0):
	            break

	       # Pick the best payoff 
               if (argv.verbose > 1):
                    sys.stderr.write("Neighbor payoffs: " + str(pay_off) + "\n")
	       picked = pay_off.index(max(pay_off))
		

               if (argv.verbose > 1):
                    sys.stderr.write("Picking neighbor #" + str(picked) + "\n")

               # Otherwise, great
               best_distribution_index[picked] +=1 
               best_distribution = [power_levels[x] for x in candidate_index]
               best_distribution_temperature = compute_layout_temperature(best_distribution, layout)
               if (argv.verbose > 1):
                    sys.stderr.write("New temperature = " + str(best_distribution_temperature) + "\n")
           
               if (best_best_distribution == None) or (sum(best_distribution) > sum(best_best_distribution)):
                    best_best_distribution = list(best_distribution)
                    best_best_distribution_temperature = best_distribution_temperature

       return [best_distribution, best_distribution_temperature]



""" Top-level function for continuous power optimization
"""
def find_maximum_power_budget_continuous(layout):

	max_possible_power = argv.num_chips * argv.chip.power_levels[-1]

	power_attempt = max_possible_power
	next_step_magnitude = (power_attempt - argv.num_chips * argv.chip.power_levels[0]) 
	next_step_direction = -1

	last_valid_solution = None

        if (argv.verbose > 0):
	    sys.stderr.write("New binary search for maximizing the power\n")

	while (True):
		if (argv.verbose == 0):
			sys.stderr.write("x")
		if (argv.verbose > 0):
			sys.stderr.write("    New binary search step (trying power = " + str(power_attempt) + " Watts)\n")

		[temperature, power_distribution] = optimize_power_distribution(layout, power_attempt, argv.powerdistopt, argv.power_distribution_optimization_num_trials, argv.power_distribution_optimization_num_iterations)
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
def pick_random_element(array):
	return array[random.randint(0, len(array) - 1)]

"""Function to compute a stacked layout"""
def compute_stacked_layout():

	positions = []
        topology = []

        if (argv.num_levels < argv.num_chips):
		abort("Not enough levels to build a stacked layout with " + \
                         str(argv.num_chips) + " chips")
            
        for level in xrange(1, argv.num_chips+1):
            positions.append([level, 0.0, 0.0])
            if (level > 1):
                topology.append([level-2, level-1])

	return Layout(argv.chip, positions, argv.medium, topology)


"""Function to compute a straight linear layout"""
def compute_rectilinear_straight_layout():

	positions = []
        topology = []

	current_level = 1
	level_direction = 1
	current_x_position = 0.0
	current_y_position = 0.0
	for i in xrange(0, argv.num_chips):
		positions.append([current_level, current_x_position, current_y_position])
                if (i > 1):
                    topology.append([i-2, i-1])
		current_level += level_direction
		if (current_level > argv.num_levels):
			current_level = argv.num_levels - 1
			level_direction = -1
		if (current_level < 1):
			current_level = 2
			level_direction = 1
		current_x_position += argv.chip.x_dimension * (1 - argv.overlap)
		
	return Layout(argv.chip, positions, argv.medium, topology)

	
"""Function to compute a diagonal linear layout"""
def compute_rectilinear_diagonal_layout():

	positions = []
        topology = []

	current_level = 1
	level_direction = 1
	current_x_position = 0.0
	current_y_position = 0.0
	for i in xrange(0, argv.num_chips):
		positions.append([current_level, current_x_position, current_y_position])
                if (i > 1):
                    topology.append([i-2, i-1])
		current_level += level_direction
		if (current_level > argv.num_levels):
			current_level = argv.num_levels - 1
			level_direction = -1
		if (current_level < 1):
			current_level = 2
			level_direction = 1
		current_x_position += argv.chip.x_dimension * (1 - sqrt(argv.overlap))
		current_y_position += argv.chip.y_dimension * (1 - sqrt(argv.overlap))
		
	return Layout(argv.chip, positions, argv.medium, topology)


"""Function to compute a checkerboard layout"""
def compute_checkerboard_layout():

	positions = []
        topology = []

        if (argv.num_levels != 2):
		abort("A checkerboard layout can only be built for 2 levels")
            
        # Rather than do annoying discrete math to compute the layout in an
        # incremental fashion, we compute a large layout and then remove
        # non-needed chips

        # Compute x and y overlap assuming a square overlap area
        x_overlap = sqrt(argv.overlap * (argv.chip.x_dimension * argv.chip.y_dimension))
        y_overlap = x_overlap

        # Create level 1
        for x in xrange(0,argv.num_chips):
            for y in xrange(0,argv.num_chips):
                positions.append([1, x * (2 * argv.chip.x_dimension - 2 * x_overlap), y * (2 * argv.chip.y_dimension - 2 * y_overlap)])

        # Create level 2
        for x in xrange(0,argv.num_chips):
            for y in xrange(0,argv.num_chips):
                positions.append([2, argv.chip.x_dimension - x_overlap + x * (2 * argv.chip.x_dimension - 2 * x_overlap), argv.chip.y_dimension - y_overlap + y * (2 * argv.chip.y_dimension - 2 * y_overlap)])

        while(len(positions) > argv.num_chips):
            max_x = max([x for [l,x,y] in positions])
            max_y = max([y for [l,x,y] in positions])
            if (max_x > max_y):
                # remove chip with x = max_x and largest y
                victim_x = max_x
                candidate_y = []
                for position in positions:
                    if (position[1] == victim_x):
                        candidate_y.append(position[2])
                victim_y = max(candidate_y)
            elif (max_y >= max_x):
                # remove a chip with y = max_y and largest x
                victim_y = max_y
                candidate_x = []
                for position in positions:
                    if (position[2] == victim_y):
                        candidate_x.append(position[1])
                victim_x = max(candidate_x)

            for position in positions:
                if (position[1] == victim_x) and (position[2] == victim_y):
                    victim_l = position[0]
                    break

            positions.remove([victim_l, victim_x, victim_y])

        # Create topology
        node1 = -1
        for p1 in positions:
            node1 += 1
            node2 = -1
            for p2 in positions:
                node2 += 1
                if (node2 <= node1):
                    continue
                if (are_two_rectangles_overlapping([p1[1], p1[2]], [p1[1] + argv.chip.x_dimension, p1[2] + argv.chip.y_dimension], [p2[1], p2[2]], [p2[1] + argv.chip.x_dimension, p2[2] + argv.chip.y_dimension])):
                    topology.append([node1, node2])

	return Layout(argv.chip, positions, argv.medium, topology)


"""Stacked layout optimization"""
def optimize_layout_stacked():

	if (argv.verbose == 0):
		sys.stderr.write("o")
	if (argv.verbose > 0):
		sys.stderr.write("Constructing a stacked layout\n")

	layout = compute_stacked_layout()

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
		layout = compute_rectilinear_straight_layout()
	elif (mode == "diagonal"):
		layout = compute_rectilinear_diagonal_layout()
	else:
		abort("Unknown rectilinear layout mode '" + mode + "'")

	result = find_maximum_power_budget(layout)
        if (result == None):
            return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]
	
			
"""Helper function that returns a set of candidate (randomized) chip positions
   that overlaps with another chip, or None if nothing is found
	- layout: the layout
	- neighbor_chip_index: which chip to connect to in the layout (by index)
	- num_positions: how many positions should be returned
	- max_num_trials: how many attempts should be done before returning "not found" (None)
"""

def get_candidate_feasible_chip_positions(layout, neighbor_chip_index, num_positions, max_num_trials):

	



"""Linear random greedy layout optimization"""
def optimize_layout_linear_random_greedy():

	# Create an initial layout
	layout = Layout(argv.chip, [[1, 0.0, 0.0]], argv.medium, [])

	
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

			picked_level = pick_random_element(possible_levels)

                        # x/y coordinates:
                        #  assume for now that the overlap is in the North-East region
                        # pick an x value
                        picked_x = random.uniform(last_chip_position[1], 
                                last_chip_position[1] + layout.chip.x_dimension - \
                                        argv.overlap / layout.chip.y_dimension)

            
                        # compute the y value that makes the right overlap
                        picked_y = -argv.overlap / (last_chip_position[1] + layout.chip.x_dimension \
                                - picked_x) + (last_chip_position[2] + layout.chip.y_dimension)

                        # Symmetries 
                        four_sided_coin = pick_random_element([0])

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

                        # Check that coordinates are positive
                        if (picked_x < 0) or (picked_y < 0):
                            continue

                        # Check that the chip can fit
                        if (not layout.can_new_chip_fit(picked_level, picked_x, picked_y)):
                            continue

                        candidate_random_trials.append([picked_level, picked_x, picked_y])

                # Pick a candidate
                max_power = -1
                picked_candidate = None
                for candidate in candidate_random_trials:
                        layout.chip_positions.append(candidate) 
                        print layout.chip_positions
                        if (argv.verbose > 0):
                                sys.stderr.write("- Evaluating candidate " + str(candidate) + "\n")
                        result = find_maximum_power_budget(layout) 
                        if (result != None):
                            [power_distribution, temperature] = result
                            if (sum(power_distribution) > max_power):
                                picked_candidate = candidate
                        layout.chip_positions = layout.chip_positions[:-1]
                        
                # Add the candidate 
                if (argv.verbose > 0):
                        sys.stderr.write("Picked candidate: " + str(candidate) + "\n")
                layout.chip_positions.append(picked_candidate) 
                if (len(layout.chip_positions) > 1):
                    topology.append([len(layout.chip_positions)-2, len(layout.chip_positions)-1])
                        

        # Do the final evaluation (which was already be done, but whatever)
        result = find_maximum_power_budget(layout) 
        if (result == None):
            return None

        [power_distribution, temperature] = result

	return [layout, power_distribution, temperature]


"""Random greedy layout optimization"""
def optimize_layout_random_greedy():

# TODO


"""Checkboard layout optimization"""
def optimize_layout_checkerboard():

	if (argv.verbose == 0):
		sys.stderr.write("o")
	if (argv.verbose > 0):
		sys.stderr.write("Constructing a checkerboard layout\n")

	layout = compute_checkerboard_layout()

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

        power_levels = find_available_power_levels(argv.chip.name, argv.power_benchmark)


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
                    temperature = compute_layout_temperature(tentative_power_distribution, layout)
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


########################################################
#####                    MAIN                     ######
########################################################

def parse_arguments():

	parser = argparse.ArgumentParser(epilog="""

LAYOUT SCHEMES (--layout, -L):

  - stacked:
       chips are stacked vertically. 
       (-d flag ignored)

  - rectilinear_straight: 
       chips are along the x axis in a straight line, using all levels
       in a "bouncing ball" fashion.
       (-d flag ignored)

  - rectilinear_diagonal: 
       chips are along the x-y axis diagonal in a straight line, using
       all levels in a "bouncing ball" fashion.
       (-d flag ignored)

  - checkerboard:
       a 2-level checkerboard layout, that's built to minimize diameter.
       (-d flag ignored)

  - linear_random_greedy: 
       a greedy randomized search for a linear but non-rectilinear layout,
       using all levels in a "bouncing ball fashion". The main difference
       with the rectilinear methods is that the overlap between chip n
       and chip n+1 is arbitrarily shaped. 
       (-d flag ignored)

  - random_greedy:
	a greedy randomized search that incrementally adds chips
        to a starting layout. 

POWER DISTRIBUTION OPTIMIZATION METHODS ('--powerdistopt', '-t'):

  - exhaustive_discrete: 
	given a layout, do and exhaustive search that evaluates all
	possible discrete power level combinations.  Completely
	ignores the '--powerdistopt_num_trials', '-T' and the
	'--powerdistopt_num_iterations', '-I' options.

  - random_discrete: 
	given a layout, just do a random search over the discrete power
	level combinations. For this method there are X trials (as
	specified with '--powerdistopt_num_trials', '-T').  Completely
	ignores the '--powerdistopt_num_iterations', '-I' option.

  - greedy_random_discrete: 
	given a layout, do a greedy neighbor search over the discrete
	power level design space (greedily increase from minimum
	power levels until no longer possible).  For this method there
	are X trials (as specified with '--powerdistopt_num_trials',
	'-T').	Completely ignores the '--powerdistopt_num_iterations',
	'-I' option.

  - greedy_not_so_random_discrete: 
	given a layout, do a neighbor search over the discrete power level
	design space, looking for the neighbor that achieves the best
	payoff (largest "increase in power" / "increase in temperature"
	ratio.	For this method there are X trials (as specified with
	'--powerdistopt_num_trials', '-T'). Completely ignores the
	'--powerdistopt_num_iterations', '-I' option.


  - random_continuous: 
	given a layout and a power budget, just do a random CONTINOUS
	search, and then make the solution discrete (i.e., feasible). For 
        this method there are X trials (as specified with '--powerdistopt_num_trials', '-T').
        Completely ignores the '--powerdistopt_num_iterations', '-I' option.

  - uniform:
        given a layout and a power budget, this baseline CONTINUOUS approach
        that simply assigns the same power to all chips, and then makes
        the solution discrete (i.e., feasible).  Completely
        ignores the '--powerdistopt_num_trials', '-T' and the
        '--powerdistopt_num_iterations', '-I' options.

  - gradient: 
	given a layout and a power budget, just do a CONTINOUS
	gradient descent (using scipy's fmin_slsqp constrained gradient
	descent algorithm), and then make the solution discrete (i.e.,
	feasible).  For this method there are X trials (as specified with
	'--powerdistopt_num_trials', '-T') and for each trial there are
	Y iterations (as specified with '--powerdistopt_num_iterations',
	'-I'). Therefore, there are X random starting points and for
	each the gradient descent algorithm is invoked. Y is passed to
	the fmin_slsqp function as its number of iterations.

  - neighbor: 
	given a layout and a given power budget, just do a CONTINUOUS
	neighbor search, and then make the solution discrete (i.e.,
	feasible).  For this method there are X trials (as specified with
	'--powerdistopt_num_trials', '-T') and for each trial there are
	Y iterations (as specified with '--powerdistopt_num_iterations',
	'-I'). Therefore, there are X random starting points and for
	each the neighbor search algorithm is invoked with Y iterations.

  - simulated_annealing_gradient
	given a layout and a given power budget, just do a CONTINUOUS
	simulated annealing search (using basinhopping from scipy, with
	the SLSQP constrained gradient descent algorithm), and then make
	the solution discrete (i.e., feasible).  For this method there
	are X trials (as specified with '--powerdistopt_num_trials',
	'-P') and for each trial there are Y iterations (as specified
	with '--powerdistopt_num_iterations', '-T'). Therefore, there are X
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
                            required=True, help='the network diameter (ignored for layouts with known/fixed diameter)')

	parser.add_argument('--layout_scheme', '-L', action='store', 
                            dest='layout_scheme', metavar='<layout scheme>',
                            required=True, help='options: "rectilinear_straight", "rectilinear_diagonal",\n"checkerboard", "linear_random_greedy", "stacked",\n"random_greedy"')

	parser.add_argument('--numlevels', '-l', action='store', type=int,
                            dest='num_levels', metavar='<# of levels>',
                            required=True, help='the number of vertical levels')

	parser.add_argument('--powerdistopt', '-t', action='store', 
			    required=True,
                            dest='powerdistopt', 
			    metavar='<power distribution optimization method>',
                            help='"uniform_discrete", "exhaustive_discrete", "random_discrete", "greedy_random_discrete", "greedy_not_so_random_discrete", \n "uniform", "random", "gradient", "neighbor",\n"simulated_annealing_gradient"')

	parser.add_argument('--powerdistopt_num_iterations', '-I', action='store', 
			    required=True, type=int,
                            dest='power_distribution_optimization_num_iterations', 
			    metavar='<# of iterations>',
                            help='number of iterations used for each power distribution optimization trial')

	parser.add_argument('--powerdistopt_num_trials', '-T', action='store', 
			    required=True, type=int,
                            dest='power_distribution_optimization_num_trials', 
			    metavar='<# of trials>',
                            help='number of trials used for power distribution optimization')

	parser.add_argument('--power_benchmark', '-B', action='store', default = "overall_max",
		            required=False,
                            dest='power_benchmark', metavar='<power benchmark>',
                            help='benchmark used to determine available chip power levels (default: overall_max)')


	parser.add_argument('--overlap', '-O', action='store', default = 1.0 / 9.0,
		            type=float, required=False,
                            dest='overlap', metavar='<chip area overlap>',
                            help='the fraction of chip area overlap fraction (default = 1/9)')

	parser.add_argument('--power_budget', '-p', action='store',
		            type=float, required=False,
                            dest='power_budget', metavar='<total power>',
                            help='the power of the whole system (precludes the search for the maximum power)')

	parser.add_argument('--power_binarysearch_epsilon', '-b', action='store',
		            type=float, required=False, default=10,
                            dest='power_binarysearch_epsilon', metavar='<threshold in Watts>',
                            help='the step size, in Watts, at which the binary search for the maximum\npower budget stops (default = 0.1)')

	parser.add_argument('--max_allowed_temperature', '-a', action='store',
		            type=float, required=False, default=80,
                            dest='max_allowed_temperature', metavar='<temperature in Celsius>',
                            help='the maximum allowed temperature for the layout (default: 80)')

	parser.add_argument('--grid_size', '-g', action='store',
		            type=int, required=False, default=2048,
                            dest='grid_size', metavar='<Hotspot temperature map size>',
                            help='the grid size used by Hotspot (larger means more RAM and more CPU; default: 2048)')

	parser.add_argument('--verbose', '-v', action='store', 
                            type=int, required=False, default=0,
                            dest='verbose', metavar='<integer verbosity level>',
                            help='verbosity level for debugging/curiosity')

	return parser.parse_args()


def abort(message):
	sys.stderr.write("Error: " + message + "\n")
	sys.exit(1)


# Parse command-line arguments
argv = parse_arguments()

if (argv.chip_name == "e5-2667v4"):
        power_levels = find_available_power_levels(argv.chip_name, argv.power_benchmark)
        argv.chip = Chip("e5-2667v4", 0.012634, 0.014172, power_levels)
#        argv.chip = Chip("e5-2667v4", 10, 10, power_levels)
elif (argv.chip_name == "phi7250"):
        power_levels = find_available_power_levels(argv.chip_name, argv.power_benchmark)
	argv.chip = Chip("phi7250",   0.0315,   0.0205,   power_levels)
else:
	abort("Chip '" + argv.chip_name + "' not supported")

if (argv.num_chips < 1):
	abort("The number of chips (--numchips, -n) should be >0")

if (argv.layout_scheme == "stacked") or (argv.layout_scheme == "rectilinear_straight") or (argv.layout_scheme == "rectilinear_diagonal") or (argv.layout_scheme == "linear_random_greedy") or (argv.layout_scheme == "checkerboard"):
    argv.diameter = argv.num_chips

if (argv.diameter < 1):
	abort("The diameter (--diameter, -d) should be >0")

if (argv.diameter > argv.num_chips):
    abort("The diameter (--diameter, -d) should <= the number of chips")
        
if (argv.num_levels < 2):
	abort("The number of levels (--numlevels, -d) should be >1")

if ((argv.overlap < 0.0) or (argv.overlap > 1.0)):
	abort("The overlap (--overlap, -O) should be between 0.0 and 1.0")

if (argv.power_distribution_optimization_num_iterations < 0):
	abort("The number of iterations for power distribution optimization (--powerdistopt_num_iterations, -I) should be between > 0")

if (argv.power_distribution_optimization_num_trials < 0):
	abort("The number of trials for power distribution optimization (--powerdistopt_num_trials, -T) should be between > 0")

if ((argv.medium != "water") and (argv.medium != "oil") and (argv.medium != "air")):
	abort("Unsupported cooling medium '" + argv.medium + "'")

if (argv.powerdistopt == "exhaustive_discrete") or (argv.powerdistopt == "uniform") or (argv.powerdistopt == "random") or (argv.powerdistopt == "random_discrete") or (argv.powerdistopt == "greedy_random_discrete") or (argv.powerdistopt == "greedy_not_so_random_discrete") or (argv.powerdistopt == "uniform_discrete"):
        argv.power_distribution_optimization_num_iterations = 1

if (argv.powerdistopt == "exhaustive_discrete") or (argv.powerdistopt == "uniform") or (argv.powerdistopt == "uniform_discrete"):
        argv.power_distribution_optimization_num_trials = 1 

if argv.power_budget:
    if (argv.powerdistopt == "exhaustive_discrete") or (argv.powerdistopt == "random_discrete") or (argv.powerdistopt == "greedy_random_discrete") or (argv.powerdistopt == "greedy_not_so_random_discrete") or (argv.powerdistopt == "uniform_discrete"):
        abort("Cannot use discrete power distribution optimization method with a fixed power budget")

# Recompile cell.c with specified grid size
os.system("gcc -Ofast cell.c -o cell -DGRID_SIZE=" + str(argv.grid_size))

solution = optimize_layout()

if (solution == None):
    print "************* OPTIMIZATION FAILED ***********"
else:

    [layout, power_distribution, temperature] = solution
    
    print "----------- OPTIMIZATION RESULTS -----------------"
    print "Chip = ", layout.chip.name
    print "Chip power levels = ", layout.chip.power_levels
    print "Layout =", layout.chip_positions
    print "Topology = ", layout.topology
    print "Power budget = ", sum(power_distribution)
    print "Power distribution =", power_distribution
    print "Temperature =", temperature

sys.exit(0)


#############################################################################################
#############################################################################################
