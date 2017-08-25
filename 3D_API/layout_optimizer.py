#!/usr/bin/python

import math
import random
import os
import sys
import subprocess

import numpy as np
from scipy.optimize import basinhopping
from bisect import bisect_left

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


def chip_is_supported(chip):

	if (chip.name == "phi7250"):
		return True
	elif (chip.name == "e5-2667v4"):
		return True
	else:
		return False


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


def create_ptrace_file(directory, chip, suffix, power):
	ptrace_file_name = directory + "/" + chip.name + "-" + suffix + ".ptrace"
	ptrace_file = open(ptrace_file_name, 'w')
	
	if (chip.name == "e5-2667v4"):
		power_per_core = power / 8
		ptrace_file.write("NULL0 NULL1 NULL2 NULL3 0_CORE 1_CORE 2_CORE 3_CORE 4_CORE 5_CORE 6_CORE 7_CORE 0_LL 1_LL 2_LL 3_LL 4_LL 5_LL 6_LL 7_LL\n")
		ptrace_file.write("0 " * 4)
		ptrace_file.write((str(power_per_core) + " ") * 8)
		ptrace_file.write("0 " * 8)	# TODO
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




""" This function computes a power distribution that minimizes the temperature, and returns
    both the power distribution and the temperature, for a given power budget"""
def optimize_power_distribution(layout, total_power_budget, optimization_method, num_random_starts, num_iterations):

	min_temperature = -1
	best_power_distribution = []

	# Validate arguments
	if (total_power_budget < layout.get_num_chips() * layout.chip.min_power):
		sys.stderr.write("Error: Power budget is too low\n")
		return [None, None]
	if (total_power_budget > layout.get_num_chips() * layout.chip.max_power):
		sys.stderr.write("Error: Power budget is too high\n")
		return [None, None]

	if (not chip_is_supported(layout.chip)):
		sys.stderr.write("Error: Chip '" + layout.chip.name + "' is not supported!\n")
		return [None, None]
	
	# Do the specified number of minimization trial
	for trial in range(0, num_random_starts):
		[temperature, power_distribution] = minimize_temperature(layout, total_power_budget, optimization_method, num_iterations)
		
		if ((min_temperature == -1) or (temperature < min_temperature)):
			min_temperature = temperature
			best_power_distribution = power_distribution
			sys.stderr.write("** New best result: T= " + str(min_temperature) + ", Power= " + str(sum(best_power_distribution)) + " ("+str(best_power_distribution) + ") **\n")

	return [min_temperature, best_power_distribution]



"""Top-level minimization function"""
def minimize_temperature(layout, total_power_budget, optimization_method, num_iterations):

	if (optimization_method == "basinhopping"):
		return minimize_temperature_basinhopping(layout, total_power_budget, num_iterations)
	elif (optimization_method == "random"):
		return minimize_temperature_random(layout, total_power_budget, num_iterations)
	else:
		sys.stderr.write("Error: Unknown optimizastion method '" + optimizastion_method + "'")



"""Temperature minimizer using a simple random search"""
def minimize_temperature_random(layout, total_power_budget, num_iterations):
	
	# Generate a valid random start
	random_start = generate_random_start(layout, total_power_budget)
	sys.stderr.write("Random start: " + str(random_start) + "\n")

	# Compute the temperature
	temperature =  compute_layout_temperature(random_start, layout)

	return [temperature, random_start]


"""Temperature minimizer using some simulated annealing"""
def minimize_temperature_basinhopping(layout, total_power_budget, num_iterations):
	
	# Generate a valid random start
	random_start = generate_random_start(layout, total_power_budget)
	sys.stderr.write("Random start: " + str(random_start) + "\n")

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
		
	sys.stderr.write(str(sum(x)) + " (" + str(x) + "): " + str(temperature) + "\n")

	return temperature



###############################################################################
##### SAMPLE MAIN

# TODO: What are the min_power and max_power below?
Xeon5 = Chip("e5-2667v4", 0.012634, 0.014172, 10.0, 100.0)
Phi   = Chip("phi7250",   0.0315,   0.0205,   10,   100.0)


# These should come from command-line arguments
num_random_starts = 1
num_iterations = 1

#optimization_method = "random"
optimization_method = "basinhopping"


layout = Layout(Xeon5, [[1, 0.0, 0.0], [2, 1.00, 0.00], [3, 0.5, 0.5]], "oil")

total_power_budget = 50


[temperature, power_distribution] = optimize_power_distribution(layout, total_power_budget, optimization_method, num_random_starts, num_iterations)

if (temperature == None):
	sys.stderr.write("Couldn't optimize\n")
	sys.exit(0)

print "Temperature=", temperature
print "Power distribution=", power_distribution


