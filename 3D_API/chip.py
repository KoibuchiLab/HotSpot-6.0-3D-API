#!/usr/bin/python

from glob import glob

import utils

FLOATING_POINT_EPSILON = 0.000001

##############################################################################################
### CHIP CLASS
##############################################################################################


"""A class that represents a chip
"""


class Chip(object):
	chip_dimensions_db = {'e5-2667v4': [0.012634, 0.014172], 'phi7250': [0.0315, 0.0205], 'base2': [0.013, 0.013],  'base3': [0.013, 0.013]}
	#chip_dimensions_db = {'e5-2667v4': [0.012634, 0.014172], 'phi7250': [0.0315, 0.0205], 'base2': [10, 10],'base3': [1,1]}

	""" Constructor:
		- name: chip name
		- benchmark_name: name of benchmark for power levels
	"""

	def __init__(self, name, benchmark_name):

		self.name = name
		[self.x_dimension, self.y_dimension] = self.chip_dimensions_db[name]
		self.__power_levels = self.__find_available_power_levels(self.name, benchmark_name)
		self.__power_levels = sorted(self.__power_levels)

		utils.info(2, "Chip power levels:")
		for (frequency, power, filename) in self.__power_levels:
			utils.info(2, "\tFrequency: " + str(frequency) + "\tPower: " + str('%.4f' % power) + "\t(" + filename + ")")

	""" Retrieve the chip's available power levels, sorted
	"""

	def get_power_levels(self):
		power_levels = [y for (x, y, z) in self.__power_levels]
		return list(power_levels)

	""" Retrieve the chip's available power levels AND ptrace files, sorted
	"""

	def get_power_levels_and_ptrace_files(self):
		power_levels = [(x, y) for (f, x, y) in self.__power_levels]
		return list(power_levels)

	""" Retrieve the chip's frequencies and power levels
	"""

	def get_frequencies_and_power_levels(self):
		power_levels = [(f, x) for (f, x, y) in self.__power_levels]
		return list(power_levels)

	""" Function to determine the actual power levels for a chip and a benchmark
	"""

	@staticmethod
	def __find_available_power_levels(chip_name, benchmark_name):

		power_levels = {}
		power_level_ptrace_files = {}

		if (chip_name == "base2" or chip_name == "base3"):
			benchmarks = [""]
			benchmark_name = ""
		else:
			benchmarks = ["bc", "cg", "dc", "ep", "is", "lu", "mg", "sp", "ua", "stress"]

		power_levels_frequency_file = {}

		# Get all the benchmark, frequency, power, file info
		for benchmark in benchmarks:

			power_levels_frequency_file[benchmark] = []

			filenames = glob("./PTRACE/" + chip_name + "-" + benchmark + "*.ptrace")

			for filename in filenames:
				f = open(filename, "r")
				lines = f.readlines()
				f.close()
				sum_power = sum([float(x) for x in lines[1].rstrip().split(" ")])
				tokens = filename.split('.')
				tokens = tokens[1].split('-')
				last_part = tokens[-1]

				from string import ascii_letters
				last_part = last_part.replace(' ', '')
				for i in ascii_letters:
					last_part = last_part.replace(i, '')
				frequency = float(last_part)
				power_levels_frequency_file[benchmark].append((frequency, sum_power, filename))

			power_levels_frequency_file[benchmark] = sorted(power_levels_frequency_file[benchmark])

		# Select the relevant data
		if (benchmark_name in benchmarks):
			return power_levels_frequency_file[benchmark]

		elif (benchmark_name == "overall_max"):  # Do the "max" stuff
			lengths = [len(power_levels_frequency_file[x]) for x in power_levels_frequency_file]
			if (max(lengths) != min(lengths)):
				utils.abort(
					"Cannot use the \"overall_max\" benchmark mode for power levels because some benchmarks have more power measurements than others")
			maxima_power_levels_frequency_file = []
			for i in xrange(0, min(lengths)):
				max_benchmark = None
				max_power = None
				for benchmark in benchmarks:
					(frequency, sum_power, filename) = power_levels_frequency_file[benchmark][i]
					if (max_power == None) or (max_power < sum_power):
						max_power = sum_power
						max_benchmark = benchmark
				maxima_power_levels_frequency_file.append(power_levels_frequency_file[max_benchmark][i])

			return maxima_power_levels_frequency_file

		else:
			utils.abort("Unknown benchmark " + benchmark_name + " for computing power levels")
