#!/usr/bin/python

import os
import sys
import subprocess
import random

from glob import glob

from math import sqrt
import networkx as nx

import utils

FLOATING_POINT_EPSILON = 0.000001


##############################################################################################
### CHIP CLASS
##############################################################################################



"""A class that represents a chip
"""
class Chip(object):

	chip_dimensions_db = {'e5-2667v4': [0.012634, 0.014172],
                              'phi7250': [0.0315,   0.0205], 
			      'base2': [ 0.013, 0.013]}

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
			utils.info(2, "\tFrequency: " + str(frequency) + "\tPower: " + str( '%.4f' % power) + "\t(" + filename + ")")

	""" Retrieve the chip's available power levels, sorted
	"""
	def get_power_levels(self):
		power_levels = [ y for (x,y,z) in self.__power_levels ]
		return list(power_levels)

	""" Retrieve the chip's available power levels AND ptrace files, sorted
	"""
	def get_power_levels_and_ptrace_files(self):
		power_levels = [ (x, y) for (f, x, y) in self.__power_levels ]
		return list(power_levels)

	""" Retrieve the chip's frequencies and power levels
	"""
	def get_frequencies_and_power_levels(self):
		power_levels = [ (f, x) for (f, x, y) in self.__power_levels ]
		return list(power_levels)

	""" Function to determine the actual power levels for a chip and a benchmark
	"""
	@staticmethod
	def __find_available_power_levels(chip_name, benchmark_name):
        	
        	power_levels = {}
		power_level_ptrace_files = {}
	
		if (chip_name == "base2"):
			benchmarks = [""]
			benchmark_name = ""
		else:
        		benchmarks = ["bc", "cg", "dc", "ep", "is", "lu", "mg", "sp", "ua", "stress"]

       		power_levels_frequency_file = {}
	
        	# Get all the benchmark, frequency, power, file info
        	for benchmark in benchmarks:
	
            		power_levels_frequency_file[benchmark] = []
		
            		filenames = glob("./PTRACE/" + chip_name + "-" +  benchmark + "*.ptrace")
		
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
                      		utils.abort("Cannot use the \"overall_max\" benchmark mode for power levels because some benchmarks have more power measurements than others")
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

		self.generate_topology_graph()

	""" Genreate a Networkx graph based on chip positions
	"""
	def generate_topology_graph(self):
		#  Greate NetworkX graph
		self.__G = nx.Graph()
		for i in xrange(0, len(self.__chip_positions)):
			self.__G.add_node(i)

		for i in xrange(1, len(self.__chip_positions)):
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
		- new_chip_position: position of the new chip
	"""
	def add_new_chip(self, new_chip_position):

		if not self.can_new_chip_fit(new_chip_position):
			utils.abort("Cannot add chip")


		# Add the new chip
		self.__chip_positions.append(new_chip_position)
		# Add a node to the networkX graph
		new_node_index = len(self.__chip_positions) - 1
		self.__G.add_node(new_node_index)
		# Add edges
		for i in xrange(0, len(self.__chip_positions)-1):
			possible_neighbor = self.__chip_positions[i]
			if self.are_neighbors(possible_neighbor, new_chip_position):
				self.__G.add_edge(i, new_node_index)

		# Recompute the diameter
		self.__diameter = nx.diameter(self.__G)

	""" Remove a chip (by index) from the layout, updating the topology accordingly
	"""
	def remove_chip(self, index):
		# Remove the chip in the position list
		self.__chip_positions.pop(index)

		# Check that the graph is still connected (by doing a copy)
		copy = self.__G.copy()
		copy.remove_node(index);
		if not nx.is_connected(copy):
			raise Exception("Graph would become disconnected");
		
		# Rebuild the graph from scratch!
		self.generate_topology_graph()


	""" Get the layout's diameter
	"""
	def get_diameter(self):
		return self.__diameter
				

	""" Determine whether a new chip (position) is valid (i.e., no collision)
	"""
	def can_new_chip_fit(self, position):
		[layer, x, y] = position
		#print "CAN FIT?:  ", [layer, x, y]
		for i in xrange(0, len(self.__chip_positions)):
			existing_chip = self.__chip_positions[i]
			#print "  Looking at xisting chip ", existing_chip
			if (existing_chip[0] != layer):
				#print "    Not in same layer so ok"
				continue
			#print  " Checking for collision"
			overlap = Layout.compute_two_rectangle_overlap_area(
					[existing_chip[1], existing_chip[2]],
					[existing_chip[1] + self.__chip.x_dimension, existing_chip[2] + self.__chip.y_dimension],	
					[x, y],
					[x + self.__chip.x_dimension, y + self.__chip.y_dimension])
			if (overlap  > 0.0):
				#print "   - NO: COLLISION! overlap = ", overlap
				return False
		#print "   - YES: FITS"
		return True


	""" Draw in 3D
	"""

	def draw_in_3D(self):

		import numpy
		import matplotlib.pyplot as plot
		from mpl_toolkits.mplot3d import Axes3D
		import matplotlib.tri as mtri
		
		################ plot_slab ###################

		def plot_slab(ax, corner, x_dim, y_dim, z_dim, color):
        		grid_resolution = z_dim / 4

		
        		other_corner = [corner[0] + x_dim, corner[1] + y_dim, corner[2] + z_dim]

			num = 10
	
        		# Plot horizontal faces
        		x_range = numpy.linspace(corner[0], other_corner[0], num = num)
        		y_range = numpy.linspace(corner[1], other_corner[1], num = num)
		
        		X, Y = numpy.meshgrid(x_range, y_range)
        		for z in [corner[2], other_corner[2]]:
                		Z = numpy.ones_like( X ) * z
                		ax.plot_wireframe(X, Y, Z, color=color)
		
        		# Plot side faces
        		for y in [corner[1], other_corner[1]]:
                		x_range = numpy.linspace(corner[0], other_corner[0], num = num)
                		z_range = numpy.linspace(corner[2], other_corner[2], num = num)
                		X, Z = numpy.meshgrid(x_range, z_range)
                		Y = numpy.ones_like( 1 ) * y
                		ax.plot_wireframe(X, Y, Z, color=color)
		
        		for x in [corner[0], other_corner[0]]:
                		y_range = numpy.linspace(corner[1], other_corner[1], num = num)
                		z_range = numpy.linspace(corner[2], other_corner[2], num = num)
                		Y, Z = numpy.meshgrid(y_range, z_range)
                		X = numpy.ones_like( 1 ) * x
                		ax.plot_wireframe(X, Y, Z, color=color)
		
		

		############ END plot_slab ###################


		level_height = 0.1
		chip_height = 0.01

       		fig = plot.figure()
       		ax = Axes3D(fig)

		
		max_level = -1
		for position in self.__chip_positions:
			xyz = [position[1], position[2], position[0] * level_height]
			r = random.uniform(0.0, 1.0)
			g = random.uniform(0.0, 1.0)
			b = random.uniform(0.0, 1.0)
			color = (r, g, b)
			if (max_level == -1) or (max_level < position[0]):
				max_level = position[0]	
        		plot_slab(ax, xyz, self.__chip.x_dimension, self.__chip.y_dimension, chip_height, color)
			
		ax.set_zlim(0, (max_level * 2) * level_height)	
        	plot.show()
		




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

	    try:
	    	os.system("octave --silent --no-window-system /tmp/layout.m");
	    except e:
		utils.info(0, "WARNING: couldn't run octave to produce layout visualizaton")
		return

            utils.info(0, "File '" + "/tmp/layout.pdf" + "' created")
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
		tmp_ptrace_file_names = []
		input_file = open(input_file_name, 'w')	
		for i in range(0, layout.get_num_chips()):

			# Determine a ptrace file
			ptrace_file_name = None
			for (power, ptrace_file) in layout.get_chip().get_power_levels_and_ptrace_files():
				if (abs(power - power_distribution[i]) < FLOATING_POINT_EPSILON):
					# Reuse an existing file
					ptrace_file_name = ptrace_file
					tokens = ptrace_file_name.split('-')
					tokens = tokens[-1].split('.')
					suffix = tokens[0]
					input_file.write(layout.get_chip().name + " " + str(layout.get_chip_positions()[i][0]) + " " + str(layout.get_chip_positions()[i][1]) + " " + str(layout.get_chip_positions()[i][2]) + " " + suffix + " " + "0\n")
					break

			if (ptrace_file_name == None):  # Couldn't find a good one, so we use a model
				suffix = "layout-optimization-tmp-" + str(i)
				input_file.write(layout.get_chip().name + " " + str(layout.get_chip_positions()[i][0]) + " " + str(layout.get_chip_positions()[i][1]) + " " + str(layout.get_chip_positions()[i][2]) + " " + suffix + " " + "0\n")
				ptrace_file_name = Layout.create_ptrace_file("./PTRACE", layout.get_chip(), suffix, power_distribution[i])
				utils.info(3, "Created a custom ptrace file since power level is custom...")
				tmp_ptrace_file_names.append(ptrace_file_name)


		input_file.close()
	
		# Call hotspot
		command_line = "./hotspot.py " + input_file_name + " " + layout.medium + " --no_images"
		try:
			devnull = open('/dev/null', 'w')
			proc = subprocess.Popen(command_line, stdout=subprocess.PIPE, shell=True, stderr=devnull)
		except Exception, e:
    			utils.abort("Could not invoke hotspot.py correctly: " + str(e))
		
		string_output = proc.stdout.read().rstrip()
		try:
			#tokens = string_output.split(" ")
			#temperature = float(tokens[2])
			temperature = float(string_output)
		except:
			utils.abort("Cannot convert HotSpot output ('" + string_output + "') to float")

		utils.info(3, "Hostpot returned temperature: " + str(temperature))
		
		# Remove files
		try:
			os.remove(input_file_name)
			# Remove tmp filenames
			for file_name in tmp_ptrace_file_names:
				os.remove(file_name)
		except Exception, e:	
			sys.stderr.write("Warning: Cannot remove some tmp files...\n")
		
		return temperature



	""" A horrible function that creates the PTRACE files for each chip with a bunch of hardcoded
    	    stuff, but it's simpler than trying to come up with a programmatic solution. This uses models
            in case the power is a continuous power that does not correspond to an available power level

            HOWEVER: if we're doing a known power, then it uses the real trace file without any modeling
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
			ptrace_file.write("0 " * 8)	# TODO TODO TODO TODO
			ptrace_file.write("\n")

		elif (chip.name == "base2"):
			# power_per_core * 4 + power_per_cache * 12 = power
			# power_per_cache = alpha + power_per_core / beta
			alpha = 0.57
			beta = 2.67
			# ==> 12 * alpha +  12 * power_per_core  / beta  + power_per_core * 4 = power
			# ==>  power_per_core = (power - 12 * alpha)  / (4 + 12 / beta)
			# ==>  power_per_cache = alpha + power_per_core / beta

			power_per_core = (power - 12 * alpha)  / (4 + 12 / beta)
			power_per_cache = alpha + power_per_core / beta

			#print "POWER = ", power
			#print "CREATED POWER = ", 12 * power_per_cache + 4 * power_per_core

			ptrace_file.write("L2C0 L2C1 L2C2 L2C3 L2C4 L2C5 L2C6 L2C7 L2C8 L2C9 L2C10 L2C11 CORE0 CORE1 CORE2 CORE3\n")
			ptrace_file.write((str(power_per_cache)+" ") * 12)
			ptrace_file.write((str(power_per_core) + " ") * 4)
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
			utils.abort("Error: Chip '" + chip.name+ "' unsupported!")
	
		ptrace_file.close()	
		return ptrace_file_name


	"""Helper function that returns a randomly placed rectangle that overlaps
    	   with another rectangle by a fixed amount, avoiding all negative coordinates
        	- rectangle1_bottom_left = [x,y]: bottom left corner of the initial rectangle
	        - rectangle_dimensions = [x,y]: size of the rectangle sides
       		- overlap: the fraction of overlap
    	   returns:
        	- [x,y]: bottom left corner of the new rectangle
	"""
	@staticmethod
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

		 #print "NORTHEAST = ", [picked_x, picked_y]
	
	         # Consider all other symmetries
	
	         # South-East
	         new_picked_x = picked_x
	         #new_picked_y = (rectangle1_y  + dim_y) - picked_y - dim_y
	         new_picked_y = (rectangle1_y  + dim_y - picked_y) + rectangle1_y - dim_y
		 #print "SOUTHEAST =  ", [new_picked_x, new_picked_y]
	         if (new_picked_x >= 0) and (new_picked_y >= 0):
	                candidates.append([new_picked_x, new_picked_y])
	
	         # North-West
	         new_picked_x = (rectangle1_x + dim_x - picked_x)  + rectangle1_x - dim_x
	         new_picked_y = picked_y
		 #print "NORTHWEST = ", [new_picked_x, new_picked_y]
	         if (new_picked_x >= 0) and (new_picked_y >= 0):
	                candidates.append([new_picked_x, new_picked_y])
	
	         # South-West
	         new_picked_x = (rectangle1_x + dim_x - picked_x)  + rectangle1_x - dim_x
	         new_picked_y = (rectangle1_y  + dim_y - picked_y) + rectangle1_y - dim_y
		 #print "SOUTHWEST = ", [new_picked_x, new_picked_y]
	         if (new_picked_x >= 0) and (new_picked_y >= 0):
	                candidates.append([new_picked_x, new_picked_y])
	
	         # At this point, we just pick one of the candidates at random
		 picked_candidate = utils.pick_random_element(candidates)
		 return picked_candidate
	
	""" Function that returns a feasible, random, neigbhot of specified chip
		- chip_index
    	   returns:
        	- [level, x, y]
	"""
	def get_random_feasible_neighbor_position(self, chip_index):
	
		chip_position = self.__chip_positions[chip_index]

                # Pick a random location relative to the last chip
		#getout = 0 #program hanging, cant find a valid random overlapping rectangle
		max_num_trials = 100
		num_trials = 0
		while (num_trials < max_num_trials):
			num_trials += 1
                	# pick a random level
                	possible_levels = []
                	if (chip_position[0] == 1):
                        	possible_levels = [2]
                	elif (chip_position[0] == utils.argv.num_levels):
                        	possible_levels = [utils.argv.num_levels - 1]
                	else:
                        	possible_levels = [chip_position[0]-1, chip_position[0]+1]
			#utils.info(1,"chip_position %s\n"%chip_position)
                	picked_level = utils.pick_random_element(possible_levels)
			#print"picked_level %s\n"%picked_level
                	[picked_x, picked_y] = Layout.get_random_overlapping_rectangle([chip_position[1], chip_position[2]], [self.__chip.x_dimension, self.__chip.y_dimension], utils.argv.overlap)
                	if (self.can_new_chip_fit([picked_level, picked_x, picked_y])):
				return [picked_level, picked_x, picked_y];
		utils.info(2, "Could not find a feasible random neighbor for chip #" + str(chip_index))
		return None

		

class LayoutBuilder(object):

	def __init__(self):
		pass

	""" Function to compute a stacked layout
	"""
	@staticmethod
	def compute_stacked_layout(num_chips):

        	positions = []
	
        	if (utils.argv.num_levels < num_chips):
                	utils.info(0, "Warning: num_levels command-line argument ignored when building a stacked layout")
	
        	for level in xrange(1, num_chips+1):
                	positions.append([level, 0.0, 0.0])
	
        	return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap)

	"""Function to compute a straight linear layout
	"""
	@staticmethod
	def compute_rectilinear_straight_layout(num_chips):

        	positions = []
	
        	if (utils.argv.num_levels < num_chips):
                	utils.info(0, "Warning: num_levels command-line argument ignored when building a linear layout")

        	current_level = 1
        	level_direction = 1
        	current_x_position = 0.0
        	current_y_position = 0.0
        	for i in xrange(0, num_chips):
                	positions.append([current_level, current_x_position, current_y_position])
                	current_level += level_direction
                	if (current_level > utils.argv.num_levels):
                        	current_level = utils.argv.num_levels - 1
                        	level_direction = -1
                	if (current_level < 1):
                        	current_level = 2
                        	level_direction = 1
                	current_x_position += utils.argv.chip.x_dimension * (1 - utils.argv.overlap)

        	return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap)

	"""Function to compute a diagonal linear layout
	"""
	@staticmethod
	def compute_rectilinear_diagonal_layout(num_chips):
	
        	positions = []

        	if (utils.argv.num_levels < num_chips):
                	utils.info(0, "Warning: num_levels command-line argument ignored when building a linear layout")
	
        	current_level = 1
        	level_direction = 1
		# HENRI DEBUG
        	current_x_position = 1
        	current_y_position = 1
        	for i in xrange(0, num_chips):
                	positions.append([current_level, current_x_position, current_y_position])
                	current_level += level_direction
                	if (current_level > utils.argv.num_levels):
                        	current_level = utils.argv.num_levels - 1
                        	level_direction = -1
                	if (current_level < 1):
                        	current_level = 2
                        	level_direction = 1
                	current_x_position += utils.argv.chip.x_dimension * (1 - sqrt(utils.argv.overlap))
                	current_y_position += utils.argv.chip.y_dimension * (1 - sqrt(utils.argv.overlap))
	
        	return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap)

	"""Function to compute a checkerboard layout"""
	@staticmethod
	def compute_checkerboard_layout(num_chips):
	
	        positions = []
	
	        if (utils.argv.num_levels != 2):
	                utils.info(0, "Warning: num_levels command-line argument ignored when building a 2-level checkboard layout")
	        if (utils.argv.overlap > 0.25):
	                utils.abort("A checkerboard layout can only be built with overlap <= 0.25")
	
	        # Rather than do annoying discrete math to compute the layout in an
	        # incremental fashion, we compute a large layout and then remove
	        # non-needed chips
	
	        # Compute x and y overlap assuming an overlap area with the same aspect
	        # ratio as the chip
	        # x_overlap * y_overlap =  overlap *  dim_x * dim_y
	        # x_overlap = alpha * dim_x
	        # y_overlap = alpha * dim_y
	        #
	        #  ====> alpha^2  = overlap
	        alpha = sqrt(utils.argv.overlap)
	        x_overlap = alpha * utils.argv.chip.x_dimension
	        y_overlap = alpha * utils.argv.chip.y_dimension
	
	        # Create level 1
	        for x in xrange(0,num_chips):
	            for y in xrange(0,num_chips):
	                positions.append([1, x * (2 * utils.argv.chip.x_dimension - 2 * x_overlap), y * (2 * utils.argv.chip.y_dimension - 2 * y_overlap)])
	
	        # Create level 2
	        for x in xrange(0,num_chips):
	            for y in xrange(0,num_chips):
	                positions.append([2, utils.argv.chip.x_dimension - x_overlap + x * (2 * utils.argv.chip.x_dimension - 2 * x_overlap), utils.argv.chip.y_dimension - y_overlap + y * (2 * utils.argv.chip.
	y_dimension - 2 * y_overlap)])
	
	        while(len(positions) > num_chips):
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
	
	        return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap)
	

