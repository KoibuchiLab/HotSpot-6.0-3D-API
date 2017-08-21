#!/usr/bin/python3

import math
import random
import numpy as np

from scipy.optimize import basinhopping

from bisect import bisect_left

class Layout(object):
	"""A class that represents a chip layout"""

	def __init__(self, chip_positions, chip_type, medium):
		#  [[layer, x, y], ..., [layer, x, y]]
		self.chip_positions = chip_positions
		# "oil", "water", "air"
		self.medium = medium
		# TULSA
		self.chip_type = chip_type
		

	def get_num_chips(self):
		return len(self.chip_positions)


""" This function computes a power distribution that minimizes the temperature, and returns
    both the power distribution and the temperature, for a given power budget"""
def optimize_power_distribution(num_random_starts, layout, power_range, power_budget):

	min_temperature = -1
	best_power_distribution = []

	if (power_budget < layout.get_num_chips() * power_range[0]):
		print("Warning: Power budget is too low");
		return [None, None]
	if (power_budget > layout.get_num_chips() * power_range[1]):
		print("Warning: Power budget is too high");
		return [None, None]
	
	# Do the specified number of minimization trial
	for trial in range(0, num_random_starts):
		[temperature, power_distribution] = minimize_temperature(layout, power_range, power_budget)
		
		if ((min_temperature == -1) or (temperature < min_temperature)):
			min_temperature = temperature
			best_power_distribution = power_distribution
			print("New best result: T=", min_temperature, "Power=", best_power_distribution)

	return [min_temperature, best_power_distribution]


def minimize_temperature(layout, power_range, power_budget):
	
	# Generate a valid random start
	random_start = []
	for i in range(0, layout.get_num_chips()):
		random_start.append(power_range[1])
	while (True):
		extra = sum(random_start) - power_budget
		if (extra <= 0):
			break
		# pick a victim
		victim = random.randint(0, layout.get_num_chips()-1)
		# decrease the victim by something that makes sense
		reduction = random.uniform(0, random_start[victim] - power_range[0])
		random_start[victim]  -= reduction

	#print ("Random start: ", random_start)

	# Define constraints
	constraints = ({'type': 'eq', 'fun': lambda x:  sum(x) - power_budget},)

	# Define bounds (these seem to be ignored by the local minimizer)
	bounds = ()
	for i in range(0, layout.get_num_chips()):
		bounds = bounds + ((power_range[0], power_range[1]),)

	# Call the basinhoping algorithm with a local minimizer that handles constraints and bounds: SLSQP
	minimizer_kwargs = {
		"method": "SLSQP", 
		"args" : [layout, power_range], 
            	"constraints": constraints,
		"bounds": bounds,
	}
	
	#ret = basinhopping(layout_temperature, random_start, minimizer_kwargs=minimizer_kwargs, niter=100, accept_test=MyBounds())
	ret = basinhopping(layout_temperature, random_start, minimizer_kwargs=minimizer_kwargs, niter=100)

	# print("global minimum:  = %.4f,%.4f f(x0) = %.4f" % (ret.x[0], ret.x[1], ret.fun))
	return [ret.fun, list(ret.x)]


def layout_temperature(x, layout_and_power_range):

	# Create the input file
	input_file_name = "/tmp/layout.data"
	input_file = open(input_file_name, 'w')	
	for i in range(0, layout.get_num_chips()):
		input_file.write(layout.chip_type + " " + str(layout.chip_positions[i][0]) + " " + str(layout.chip_positions[i][1]) + " " + str(layout.chip_positions[i][2]) + " " + str((x[i])) + " " + "0\n")
	input_file.close()
	
	
	value = x[0]*(x[1] - 100) + x[2] * (x[1] -10) - x[0] * x[1] + x[2] * x[0] * x[1] + x[2] / x[0]
	# This is a hack because it seems the library ignores the bounds and will go into
        # unallowed values
	#print("EVALUATING OBJECTIVE WITH ", x, ": ", value)
	for i in range(0, layout_and_power_range[0].get_num_chips()):
		if ((x[i] < layout_and_power_range[1][0]) or (x[i] > layout_and_power_range[1][1])):
			value = 1000000
			break
	# PLUG IN CODE
	return value



##### SAMPLE MAIN

num_random_starts = 100
layout = Layout([[1, 1.0, 2.0], [2, 2.0, 2.0], [1, 3.0, 1.5]], "TULSA", "oil")
power_budget = 5.5
power_range = [1.0, 4.0]

optimize_power_distribution(num_random_starts, layout, power_range, power_budget)


