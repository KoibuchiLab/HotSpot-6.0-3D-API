#!/usr/bin/python

import math
import random
import numpy as np
import subprocess

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
def optimize_power_distribution(layout, power_range, power_budget, num_random_starts, num_iterations):

	min_temperature = -1
	best_power_distribution = []

	# Validate arguments
	if (power_budget < layout.get_num_chips() * power_range[0]):
		print("Warning: Power budget is too low")
		return [None, None]
	if (power_budget > layout.get_num_chips() * power_range[1]):
		print("Warning: Power budget is too high")
		return [None, None]

	if (not (layout.chip_type == "e5-2667v4")):
		print "Only processor type supported for now is e5-2667v4"
		return [None, None]
	
	# Do the specified number of minimization trial
	for trial in range(0, num_random_starts):
		[temperature, power_distribution] = minimize_temperature(layout, power_range, power_budget, num_iterations)
		
		if ((min_temperature == -1) or (temperature < min_temperature)):
			min_temperature = temperature
			best_power_distribution = power_distribution
			print("New best result: T=", min_temperature, "Power=", best_power_distribution)

	return [min_temperature, best_power_distribution]


def minimize_temperature(layout, power_range, power_budget, num_iterations):
	
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

	# Define bounds (these seem to be ignored by the local minimizer - to investigate)
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
	
	#ret = basinhopping(layout_temperature, random_start, minimizer_kwargs=minimizer_kwargs, niter=num_iterations, accept_test=MyBounds())
	print "CALLING BASINHOPPING"
	ret = basinhopping(layout_temperature, random_start, minimizer_kwargs=minimizer_kwargs, niter=num_iterations)

	# print("global minimum:  = %.4f,%.4f f(x0) = %.4f" % (ret.x[0], ret.x[1], ret.fun))
	return [ret.fun, list(ret.x)]

def create_ptrace_file(directory, chip_type, suffix, power):
	ptrace_file_name = directory + "/" + chip_type + "-" + suffix + ".ptrace"
	ptrace_file = open(ptrace_file_name, 'w')
	
	if (chip_type == "e5-2667v4"):
		power_per_core = power / 8
		ptrace_file.write("NULL0 NULL1 NULL2 NULL3 0_CORE 1_CORE 2_CORE 3_CORE 4_CORE 5_CORE 6_CORE 7_CORE 0_LL 1_LL 2_LL 3_LL 4_LL 5_LL 6_LL 7_LL\n")
		ptrace_file.write("0 ")
		ptrace_file.write("0 ")
		ptrace_file.write("0 ")
		ptrace_file.write("0 ")
		ptrace_file.write(str(power_per_core) + " ")
		ptrace_file.write(str(power_per_core) + " ")
		ptrace_file.write(str(power_per_core) + " ")
		ptrace_file.write(str(power_per_core) + " ")
		ptrace_file.write(str(power_per_core) + " ")
		ptrace_file.write(str(power_per_core) + " ")
		ptrace_file.write(str(power_per_core) + " ")
		ptrace_file.write(str(power_per_core) + " ")
		ptrace_file.write("0 ")	# TODO
		ptrace_file.write("0 ")	# TODO
		ptrace_file.write("0 ")	# TODO
		ptrace_file.write("0 ")	# TODO
		ptrace_file.write("0 ")	# TODO
		ptrace_file.write("0 ")	# TODO
		ptrace_file.write("0 ")	# TODO
		ptrace_file.write("0 ")	# TODO	
		ptrace_file.write("\n")

	else:
		print "Chip type '"+chip_type+"' unsupported!"
		sys.exit(1)

	ptrace_file.close()	
	return ptrace_file_name



def layout_temperature(x, arguments):

	# Un-marshall arguments
	layout = arguments[0]
	power_range = arguments[1]

	# This is a hack because it seems the scipy library ignores the bounds and will go into
        # unallowed values, so instead we return a very high temperature (lame)
	for i in range(0, layout.get_num_chips()):
		if ((x[i] < power_range[0]) or (x[i] > power_range[1])):
			return 100000


	# Create the input file and ptrace_files
	input_file_name = "/tmp/layout-optimization-tmp.data"
	ptrace_file_names = []
	input_file = open(input_file_name, 'w')	
	for i in range(0, layout.get_num_chips()):
		# Create a line in the input file
		suffix = "layout-optimization-tmp-" + str(i)
		input_file.write(layout.chip_type + " " + str(layout.chip_positions[i][0]) + " " + str(layout.chip_positions[i][1]) + " " + str(layout.chip_positions[i][2]) + " " + suffix + " " + "0\n")
		# Create the (temporary) ptrace file
		ptrace_file_name = create_ptrace_file("./PTRACE", layout.chip_type, suffix, x[i])
		ptrace_file_names.append(ptrace_file_name)
	input_file.close()
	
	# Call hotspot
	
	# TODO
	command_line = "python hotspot.py " + input_file_name + " " + layout.medium
	print "COMMAND_LINE=", command_line
	try:
		proc = subprocess.Popen(command_line, stdout=subprocess.PIPE)
	except Exception, e:
    		print 'Could not invoke hotspot.py correctly: ', str(e)
		sys.exit(1)
	
	output = proc.stdout.read()	
	print "HOTSTPOT OUTPUT = ", output

	sys.exit(0)



	# Remove files
	os.remove(input_file_name)
	for file_name in ptrace_file_names:
		os.remove(file_name)
	
		

	return 42



###############################################################################
##### SAMPLE MAIN

# These should come from command-line arguments?
num_random_starts = 100
num_iterations = 10

# tulsa 1 0.00 0.00 1380 0
# e5-2667v4 2 0.011 0.011 is3600 0
# e5-2667v4 1 0.001 0.031 cg2400 0
# tulsa 1 0.03 0.03 185 0
# phi7250 1 0.03 0.00 1300 0 
# tulsa 2 0.04 0.04 1380 0

layout = Layout([[1, 0.0, 0.0], [2, 0.00, 0.00], [3, 0.0, 0.0]], "e5-2667v4", "oil")
power_budget = 10.5
power_range = [1.0, 4.0]


[temperature, power_distribution] = optimize_power_distribution(layout, power_range, power_budget, num_random_starts, num_iterations)

if (temperature == None):
	print "Couldn't optimize"
	sys.exit(0)

print "Temperature=", temperature
print "Power distribution=", power_distribution


