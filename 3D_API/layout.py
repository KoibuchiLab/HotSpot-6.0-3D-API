#!/usr/bin/python

import os
import sys
import subprocess

from glob import glob

from math import sqrt
import networkx as nx

import optimize_layout_globals

FLOATING_POINT_EPSILON = 0.000001


##############################################################################################
### CHIP CLASS
##############################################################################################



"""A class that represents a chip
"""
class Chip(object):

	chip_dimensions_db = {'e5-2667v4': [0.012634, 0.014172],
                              'phi7250': [0.0315,   0.0205]}

	""" Constructor:
		- name: chip name
		- x_dimension: width
		- y_dimension: length	
		- benchmark_name: name of benchmark for power levels
	"""
        def __init__(self, name, benchmark_name):
		self.name = name
		[self.x_dimension, self.y_dimension] = self.chip_dimensions_db[name]
		self.__power_levels = self.__find_available_power_levels(self.name, benchmark_name)

	""" Retrieve the chip's available power levels, sorted
	"""
	def get_power_levels(self):
		return list(self.__power_levels)


	""" Function to determine the actual power levels for a chip and a benchmark
	"""
	@staticmethod
	def __find_available_power_levels(chip_name, benchmark_name):
        	
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
### LAYOUT CLASS
##############################################################################################

""" A class that represents a layout of chips
"""
class Layout(object):

	""" Constructor:
		- chip: a chip object
		- chip_positions: [[layer, x, y], ..., [layer, x, y]]
		- medium: air | oil | water
		- overlap: fraction of overlap necessary for two chips to be connected
	"""
	def __init__(self, chip, chip_positions,  medium, overlap):

		self.__chip = chip
		self.medium = medium
		self.__chip_positions = chip_positions
		self.__overlap = overlap

		#  Greate NetworkX graph
		self.__G = nx.Graph()
		for i in xrange(0, len(chip_positions)):
			self.__G.add_node(i)

		for i in xrange(1, len(chip_positions)):
			for j in xrange(0, i):
				# Should we add an i-j edge?
				if self.are_neighbors(self.__chip_positions[i], self.__chip_positions[j]):
					self.__G.add_edge(i, j)
	
		# Compute the diameter (which we maintain updated)
		self.__diameter = nx.diameter(self.__G)

	""" Get the chip object
	"""
	def get_chip(self):
		return self.__chip
		
	""" Get the number of chips in the layout
	"""
	def get_num_chips(self):
		return len(self.__chip_positions)


	""" Get the list of chip positions
	"""
	def get_chip_positions(self):
		return list(self.__chip_positions)

	""" Get the list of topology edges
	"""
	def get_topology(self):
		return self.__G.edges()

	""" Determines whether two chips are connected in the topology
	    (based on whether they overlap sufficiently)
	"""
	def are_neighbors(self, position1, position2):
		 if (abs(position1[0] - position2[0]) != 1):
                        return False

                 # must have enough overlap
                 overlap_area = Layout.compute_two_rectangle_overlap_area(
                        [position1[1], position1[2]],
                        [position1[1] + self.__chip.x_dimension, position1[2] + self.__chip.y_dimension],
                        [position2[1], position2[2]],
                        [position2[1] + self.__chip.x_dimension, position2[2] + self.__chip.y_dimension])

                 if (overlap_area / (self.__chip.x_dimension * self.__chip.y_dimension) < self.__overlap - FLOATING_POINT_EPSILON):
			return False

	         return True

	""" Add a new chip (position) to the layout, updating the topology accordingly
	"""
	def add_new_chip(self, new_chip):
		if not self.can_new_chip_fit(new_chip):
			abort("Cannot add chip")

		# Add the new chip
		self.__chip_positions.append(new_chip)
		# Add a node to the networkX graph
		new_node_index = len(self.__chip_positions) - 1
		self.__G.add_node(new_node_index)
		# Add edges
		for i in xrange(0, len(self.__chip_positions)-1):
			possible_neighbor = self.__chip_positions[i]
			if self.are_neighbors(possible_neighbor, new_chip):
				self.__G.add_edge(i, new_node_index)

		# Recompute the diameter
		self.__diameter = nx.diameter(self.__G)

	""" Remove a chip (by index) from the layout, updating the topology accordingly
	"""
	def remove_chip(self, index):
		# Remove the chip in the position list
		self.__chip_positions.pop(index)
		
		# Remove the node in the graph, and thus all edges
		self.__G.remove_node(index);
		# Recompute the diameter
		self.__diameter = nx.diameter(self.__G)


	""" Get the layout's diameter
	"""
	def get_diameter(self):
		return self.__diameter
				

	""" Determine whether a new chip (position) is valid (i.e., no collision)
	"""
	def can_new_chip_fit(self, position):
		[layer, x, y] = position
		for i in xrange(0, len(self.__chip_positions)):
			existing_chip = self.__chip_positions[i]
			if (existing_chip[0] != layer):
				continue
			if (Layout.compute_two_rectangle_overlap_area(
					[existing_chip[1], existing_chip[2]],
					[existing_chip[1] + self.chip.x_dimension, existing_chip[2] + self.chip.y_dimension],	
					[x, y],
					[x + self.chip.x_dimension, y + self.chip.y_dimension]) > 0.0):
				return False
		return True


	""" Draw the layout using Octave (really rudimentary)
            Will produce amusing ASCI art
	""" 
        def draw_in_octave(self):
            file = open("/tmp/layout.m","w") 
            file.write("figure\n")
            file.write("hold on\n")
    
	    max_x = 0
	    max_y = 0
            for pos in self.__chip_positions:
		[l,x,y] = pos
		max_x = max(max_x, x + self.get_chip().x_dimension)
		max_y = max(max_y, y + self.get_chip().y_dimension)
	
	    file.write("axis([0, " + str(max(max_x, max_y)) + ", 0 , " + str(max(max_x, max_y)) + "])\n");
				
 
            for rect in self.__chip_positions:
                [l,x,y] = rect
                w = self.get_chip().x_dimension
                h = self.get_chip().y_dimension
                colors = ["b", "r", "g", "c", "k", "m"]
                color = colors[l % len(colors)]

                file.write("plot([" + str(x) + ", " + str(x + w) + "," + str(x + w) + "," + str(x) + "," + str(x) + "]" +  ", [" + str(y) + ", " + str(y) + ", "+ str(y + h) + ", " + str(y + h) +", " + str(y) +  "], " + "'" + color + "-'" + ")\n") 
            file.write("print /tmp/layout.pdf\n")
            file.close()
#            sys.stderr.write("File '" + "/tmp/layout.m" + "' created")

	    os.system("octave --silent --no-window-system /tmp/layout.m");
            sys.stderr.write("File '" + "/tmp/layout.pdf" + "' created\n")
            return


	"""  Compute the overlap area between two rectangles 
        """
	@staticmethod
	def compute_two_rectangle_overlap_area(bottom_left_1, top_right_1, bottom_left_2, top_right_2):
		        	
        	# They don't overlap in X
        	if (top_right_1[0] < bottom_left_2[0]):
	        	return 0.0
        	if (top_right_2[0] < bottom_left_1[0]):
	        	return 0.0
       	
        	# They don't overlap in Y
        	if (top_right_1[1] < bottom_left_2[1]):
	        	return 0.0
        	if (top_right_2[1] < bottom_left_1[1]):
	        	return 0.0
	
		# Compute the overlap in X
		if max(bottom_left_1[0], bottom_left_2[0]) < min(top_right_1[0], top_right_2[0]):
			x_overlap = min(top_right_1[0], top_right_2[0]) - max(bottom_left_1[0], bottom_left_2[0]) 
		else:
			x_overlap = 0.0
			
		# Compute the overlap in Y
		if max(bottom_left_1[1], bottom_left_2[1]) < min(top_right_1[1], top_right_2[1]):
			y_overlap = min(top_right_1[1], top_right_2[1]) - max(bottom_left_1[1], bottom_left_2[1]) 
		else:
			y_overlap = 0.0
		
		return x_overlap * y_overlap
 

	""" A function that hotspot to find out the max temp of the layout
			- the layout
 			- power_distribution: the power distribution
	"""
	@staticmethod
	def compute_layout_temperature(layout, power_distribution):
	
		# This is a hack because it seems the scipy library ignores the bounds and will go into
        	# unallowed values, so instead we return a very high temperature (lame)
		for i in range(0, layout.get_num_chips()):
			if ((power_distribution[i] < layout.get_chip().get_power_levels()[0]) or (power_distribution[i] > layout.get_chip().get_power_levels()[-1])):
				return 100000
	
	
		# Create the input file and ptrace_files
		input_file_name = "/tmp/layout-optimization-tmp.data"
		ptrace_file_names = []
		input_file = open(input_file_name, 'w')	
		for i in range(0, layout.get_num_chips()):
			# Create a line in the input file
			suffix = "layout-optimization-tmp-" + str(i)
			input_file.write(layout.get_chip().name + " " + str(layout.get_chip_positions()[i][0]) + " " + str(layout.get_chip_positions()[i][1]) + " " + str(layout.get_chip_positions()[i][2]) + " " + suffix + " " + "0\n")
			# Create the (temporary) ptrace file
			ptrace_file_name = Layout.create_ptrace_file("./PTRACE", layout.get_chip(), suffix, power_distribution[i])
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
		
		return temperature



	""" A horrible function that creates the PTRACE files for each chip with a bunch of hardcoded
    	stuff, but it's simpler than trying to come up with a programmatic solution
	"""
	@staticmethod
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




class LayoutBuilder(object):

	def __init__(self):
		# Comamnd-line arguments
                global argv
                argv = optimize_layout_globals.argv
		global abort
                abort = optimize_layout_globals.abort

	@staticmethod
	def compute_stacked_layout():

        	positions = []
	
        	if (argv.num_levels < argv.num_chips):
                	abort("Not enough levels to build a stacked layout with " + \
                        	str(argv.num_chips) + " chips")
	
        	for level in xrange(1, argv.num_chips+1):
                	positions.append([level, 0.0, 0.0])
	
        	return Layout(argv.chip, positions, argv.medium, argv.overlap)

