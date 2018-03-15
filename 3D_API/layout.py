#!/usr/bin/python

import networkx as nx
import os
import random
import subprocess
import sys
from math import sqrt
#from numba import jit

import utils

FLOATING_POINT_EPSILON = 0.000001

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
		- inductor_properties: [[layer to which inductor belongs, x, y, x_dim, y_dim], ..., [layer, x, y, x_dim, y_dim]]
	"""

	def __init__(self, chip, chip_positions, medium, overlap,
				 inductor_properties):

		self.__chip = chip
		self.__medium = medium
		self.__chip_positions = chip_positions
		self.__overlap = overlap
		self.__diameter = 0
		self.__all_pairs_shortest_path_lengths = {}
		self.__inductor_properties = inductor_properties
		#self.draw_in_3D(None, True) # for debugging
		self.generate_topology_graph()

	""" Generate a Networkx graph based on chip positions
	"""
	#@jit
	def generate_topology_graph(self):
		#  Greate NetworkX graph
		self.__G = nx.Graph()
		for i in xrange(0, len(self.__chip_positions)):
			self.__G.add_node(i)
		for i in xrange(1, len(self.__chip_positions)):
			for j in xrange(0, i):
				# Should we add an i-j edge?
				if self.are_connected_neighbors(self.__chip_positions[i], self.__chip_positions[j]):
					self.__G.add_edge(i, j)

		if not nx.is_connected(self.__G):
			raise Exception("Graph is disconnected");

		# Compute the diameter (which we maintain updated)
		self.__diameter = nx.diameter(self.__G)

		# Compute all pairs shortest path lengths
		self.__all_pairs_shortest_path_lengths = dict(nx.all_pairs_shortest_path_length(self.__G))

	""" Get the chip object
	"""

	def get_chip(self):
		return self.__chip

	""" Get the overlap
	"""

	def get_overlap(self):
		return self.__overlap

	""" Get the medium
	"""

	def get_medium(self):
		return self.__medium

	""" Get the number of chips in the layout
	"""

	def get_num_chips(self):
		return len(self.__chip_positions)

	""" Get the number of levels in the layout
	"""

	def get_num_levels(self):
		levels = [level for [level, x, y] in self.__chip_positions]
		return max(levels)

	""" Get the number of edges in the layout
	"""

	def get_num_edges(self):
		return (self.__G.number_of_edges())

	""" Get the list of chip positions
	"""

	def get_chip_positions(self):
		return list(self.__chip_positions)

	""" Get the list of inductors positions
		"""

	def get_inductor_properties(self):
		return list(self.__inductor_properties)

	""" Get the list of topology edges
	"""

	def get_topology(self):
		return self.__G.edges()


	""" Get the layout's ASPL
	"""

	def get_ASPL(self):
		return nx.average_shortest_path_length(self.__G)

	""" Get the layout's diameter
	"""

	def get_diameter(self):
		return self.__diameter

	""" Get a chip's longest shortest path over all other chip
	"""
	#@jit
	def get_longest_shortest_path_from_chip(self, chip_index):
		# print "===> ", self.__all_pairs_shortest_path_lengths
		# print "INDEX = ", chip_index
		# print "===> ", self.__all_pairs_shortest_path_lengths[chip_index]
		return max([self.__all_pairs_shortest_path_lengths[chip_index][z] for z in
					self.__all_pairs_shortest_path_lengths[chip_index]])


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
		# print "-->", position1, position2, "overlap=", overlap_area / (self.__chip.x_dimension * self.__chip.y_dimension)

		if (overlap_area / (
				self.__chip.x_dimension * self.__chip.y_dimension) < self.__overlap - FLOATING_POINT_EPSILON):
			return False
		return True

	""" Determines whether two chips are connected with INDUCTOR in the topology
		(based on whether they overlap sufficiently)
	"""
	#@jit
	def are_connected_neighbors(self, position1, position2):

		# Quick check
		if (abs(position1[0] - position2[0]) != 1):  # same level check
			# print 'Quick Check'
			return False
		for inductor in self.__inductor_properties:

			# Is inductor at the correct level?
			if inductor[0] != min(position1[0], position2[0]):
				continue

			# Is the inductor contained in chip #1?
			if not Layout.rectangle_is_contained_in([inductor[1], inductor[2]], [inductor[1] + inductor[3], inductor[2] + inductor[4]], [position1[1], position1[2]], [position1[1] + self.__chip.x_dimension, position1[2] + self.__chip.y_dimension]):
				# print '\nCHIP 1\n'
				continue

			# Is the inductor contained in chip #2?
			if not Layout.rectangle_is_contained_in([inductor[1], inductor[2]], [inductor[1] + inductor[3], inductor[2] + inductor[4]], [position2[1], position2[2]], [position2[1] + self.__chip.x_dimension, position2[2] + self.__chip.y_dimension]):
				# print '\nCHIP 2\n'
				continue

			# print inductor
			return True

		return False

	"""
	checks for cross talk by checking if any inductors overlap
		- tentative_inductor: tentative inductor position
	Returns True if there is crosstalk
	"""
	#@jit
	def check_cross_talk(self, tentative_inductor):

		utils.info(2, 'Checking for CROSSTALK')

		existing_inductors = self.__inductor_properties
		for existing_inductor in existing_inductors:
			if (not abs(tentative_inductor[0] - existing_inductor[0]) == 1):
				utils.info(3,"inductors are more than 1 level appart, cross talk cant happen")
				continue
			overlap_area = Layout.compute_two_rectangle_overlap_area(
				[existing_inductor[1], existing_inductor[2]],
				[existing_inductor[1] + existing_inductor[3], existing_inductor[2] + existing_inductor[4]],
				[tentative_inductor[1], tentative_inductor[2]],
				[tentative_inductor[1] + tentative_inductor[3], tentative_inductor[2] + tentative_inductor[4]])
			#print 'overlap is ', overlap_area
			if overlap_area-FLOATING_POINT_EPSILON > 0.0:
				utils.info(2, "WARNING: CROSSTALK at inductor levels " + str(existing_inductor[0]) + " and " + str(
					tentative_inductor[0]))
				return True
		return False

	"""
	Finds x and y for new inductor based off the postion of two chips different chips
		- position1: [level, x, y]
		- position2: [level, x, y]
	Returns [level,x,y, x_dim, y_dim] coordinates for new inductor
	"""
	#@jit
	def get_new_inductor_properties(self, position1, position2):

		utils.info(2, 'finding new inductor position')

		if not position1[0] == position2[0]:
			level = min(position1[0], position2[0])
			x = max(position1[1], position2[1])
			y = max(position1[2], position2[2])
			x_dim = abs(min(position1[1] + self.__chip.x_dimension, position2[1] + self.__chip.x_dimension) - x)
			y_dim = abs(min(position1[2] + self.__chip.y_dimension, position2[2] + self.__chip.y_dimension) - y)

			return [level, x, y, x_dim, y_dim]
		utils.abort("New inductor position not possible, Chips are on the same level")

	""" Add a new chip (position) to the layout, updating the topology accordingly
		- new_chip_position: position of the new chip
	"""
	
	def add_new_chip(self, new_chip_position):

		# Just a check in case the user decided to add something without
		# first checking that it was possible
		#self.draw_in_3D(None,True)
		if not self.can_new_chip_fit(new_chip_position): #checks if chips collide
			#print 'new chip position is ' ,new_chip_position, 'num chips is ',len(self.get_chip_positions())
			#self.draw_in_3D(None,True)
			utils.abort("Cannot add chip") ###TODO: do we abort here?
			#print "warning"
		# adds inductors
		if self.connect_new_chip(new_chip_position):
			# Add the new chip
			self.__chip_positions.append(new_chip_position)

		# Rebuild the graph from scratch!
		try:
			self.generate_topology_graph()
		except Exception as e:
			raise e

	""" connects new chip by adding inductor(s) where they will fit and appends new inductor to inductor_properties
			-new_chip_position: position of new chip
		Returns True if inductors added
	"""
	#@jit
	def connect_new_chip(self, new_chip_position):
		original_inductor_count = len(self.__inductor_properties)
		num_inductor = 0
		for position in self.__chip_positions:
			new_inductor_property = []
			if not self.are_neighbors(position, new_chip_position): #check if chips overlap properly
				continue
			new_inductor_property = self.get_new_inductor_properties(position, new_chip_position)
			if not self.can_new_inductor_fit(new_inductor_property): #check if inductor can be added where overlap is
				continue
			if self.check_cross_talk(new_inductor_property):
				continue
			self.__inductor_properties.append(new_inductor_property)
			utils.info(3, "Connecting chip by adding inductor")
			num_inductor +=1
			if num_inductor>1:
				utils.info(3,"\nBRIDGE!!!\n")
				#self.draw_in_3D(None, True)
		if original_inductor_count < len(self.__inductor_properties):
			return True
		utils.info(2, "Could not connect new chip")
		return False

	""" Remove a chip (by index) from the layout, updating the topology accordingly
	"""
	#@jit
	def remove_chip(self, index):

		# Remove the inductors for that chip
		chip_position = self.__chip_positions[index]
		for inductor in list(self.__inductor_properties):
			if ((inductor[0] != chip_position[0]) and (inductor[0] != chip_position[0] - 1)):
				continue
			if not Layout.rectangle_is_contained_in([inductor[1], inductor[2]], [inductor[1] + inductor[3], inductor[2] + inductor[4]], [chip_position[1], chip_position[2]], [chip_position[1] + self.__chip.x_dimension, chip_position[2] + self.__chip.y_dimension]):
				continue
			self.__inductor_properties.remove(inductor)

		# Remove the chip in the position list
		self.__chip_positions.pop(index)

		# Check that the graph is still connected (by doing a copy)
		self.__G.remove_node(index);
		if not nx.is_connected(self.__G):
			raise Exception("Graph would become disconnected");

		# Rebuild the graph from scratch!
		self.generate_topology_graph()

	""" Determine whether a new chip (position) is valid (i.e., no collision)
	"""
	#@jit
	def can_new_chip_fit(self, position):
		[layer, x, y] = position
		# print "CAN FIT?:  ", [layer, x, y]
		for i in xrange(0, len(self.__chip_positions)):
			existing_chip = self.__chip_positions[i]
			# print "  Looking at xisting chip ", existing_chip
			if (existing_chip[0] != layer):
				# print "    Not in same layer so ok"
				continue
			# print  " Checking for collision"
			overlap = Layout.compute_two_rectangle_overlap_area(
				[existing_chip[1], existing_chip[2]],
				[existing_chip[1] + self.__chip.x_dimension, existing_chip[2] + self.__chip.y_dimension],
				[x, y],
				[x + self.__chip.x_dimension, y + self.__chip.y_dimension])
			if (overlap - FLOATING_POINT_EPSILON> 0.0):
				#print "   - NO: COLLISION! overlap = ", overlap
				return False
		# print "   - YES: FITS"

		return True

	""" Determine whether a new inductor (position) is valid (i.e., no collision)
		Returns True if can fit
	"""
	#@jit
	def can_new_inductor_fit(self, position):
		[layer, x, y, x_dim, y_dim] = position
		# print "CAN FIT?:  ", [layer, x, y]
		for i in xrange(0, len(self.__inductor_properties)):
			existing_inductor = self.__inductor_properties[i]
			# print "  Looking at xisting chip ", existing_inductor
			if (existing_inductor[0] != layer):
				# print "    Not in same layer so ok"
				continue
			# print  " Checking for collision"
			overlap = Layout.compute_two_rectangle_overlap_area(
				[existing_inductor[1], existing_inductor[2]],
				[existing_inductor[1] + existing_inductor[3], existing_inductor[2] + existing_inductor[4]],
				[x, y],
				[x + x_dim, y + y_dim])
			if (overlap - FLOATING_POINT_EPSILON > 0.0):
				# print "   - NO: COLLISION! overlap = ", overlap
				utils.info(0, 'inductor collision, can\'t place here')
				return False
		# print "   - YES: FITS"

		return True

	""" Draw in 3D
	"""

	def draw_in_3D(self, figure_filename, show_plot):

		import numpy
		import matplotlib.pyplot as plot
		from mpl_toolkits.mplot3d import Axes3D

		################ plot_cuboid ###################

		def plot_cuboid(ax, corner, x_dim, y_dim, z_dim, color):
			grid_resolution = z_dim / 4

			other_corner = [corner[0] + x_dim, corner[1] + y_dim, corner[2] + z_dim]

			num = 10

			# Plot horizontal faces
			x_range = numpy.linspace(corner[0], other_corner[0], num=num)
			y_range = numpy.linspace(corner[1], other_corner[1], num=num)

			X, Y = numpy.meshgrid(x_range, y_range)
			for z in [corner[2], other_corner[2]]:
				Z = numpy.ones_like(X) * z
				ax.plot_wireframe(X, Y, Z, color=color)

			# Plot side faces
			for y in [corner[1], other_corner[1]]:
				x_range = numpy.linspace(corner[0], other_corner[0], num=num)
				z_range = numpy.linspace(corner[2], other_corner[2], num=num)
				X, Z = numpy.meshgrid(x_range, z_range)
				Y = numpy.ones_like(1) * y
				ax.plot_wireframe(X, Y, Z, color=color)

			for x in [corner[0], other_corner[0]]:
				y_range = numpy.linspace(corner[1], other_corner[1], num=num)
				z_range = numpy.linspace(corner[2], other_corner[2], num=num)
				Y, Z = numpy.meshgrid(y_range, z_range)
				X = numpy.ones_like(1) * x
				ax.plot_wireframe(X, Y, Z, color=color)

		############ END plot_cuboid ###################

		level_height = 0.1
		chip_height = 0.01
		induction_zone = 2 * level_height + chip_height

		fig = plot.figure()
		ax = Axes3D(fig)

		max_level = -1
		for position in self.__chip_positions:
			# print 'chip level is ', position[0]
			xyz = [position[1], position[2], position[0] * level_height]
			r = random.uniform(0.1, 0.9)
			g = random.uniform(0.1, 0.9)
			b = random.uniform(0.1, 0.9)
			color = (r, g, b)
			if (max_level == -1) or (max_level < position[0]):
				max_level = position[0]
			plot_cuboid(ax, xyz, self.__chip.x_dimension, self.__chip.y_dimension, chip_height, color)

		# Layout.compute_two_rectangle_overlap_area()
		for position in self.__inductor_properties:
			xyz = [position[1], position[2], position[0] * level_height + .01]
			# print 'inductor level is ', position[0],' xyz = ', xyz
			r = 0
			g = 0
			b = 0
			color = (r, g, b)
			if (max_level == -1) or (max_level < position[0]):
				max_level = position[0]
			# plot_cuboid(ax, xyz, self.__chip.x_dimension - (self.__chip.x_dimension*(1-sqrt(self.__overlap))), self.__chip.y_dimension - (self.__chip.y_dimension*(1-sqrt(self.__overlap))), induction_zone, color)
			plot_cuboid(ax, xyz, position[3], position[4], level_height - chip_height, color)

		ax.set_zlim(0, (max_level * 2) * level_height)
		ax.azim = +0
		ax.elev = 90

		if (figure_filename):
			fig.savefig(figure_filename, bbox_inches='tight')

		if show_plot:
			plot.show()

	""" Draw the layout using Octave (really rudimentary)
			Will produce amusing ASCI art
		(DEPRECATED)
	"""

	def draw_in_octave(self, filename):
		file = open("/tmp/layout.m", "w")
		file.write("figure\n")
		file.write("hold on\n")

		max_x = 0
		max_y = 0
		for pos in self.__chip_positions:
			[l, x, y] = pos
			max_x = max(max_x, x + self.get_chip().x_dimension)
			max_y = max(max_y, y + self.get_chip().y_dimension)

		file.write("axis([0, " + str(max(max_x, max_y)) + ", 0 , " + str(max(max_x, max_y)) + "])\n");

		for rect in self.__chip_positions:
			[l, x, y] = rect
			w = self.get_chip().x_dimension
			h = self.get_chip().y_dimension
			colors = ["b", "r", "g", "c", "k", "m"]
			color = colors[l % len(colors)]

			file.write("plot([" + str(x) + ", " + str(x + w) + "," + str(x + w) + "," + str(x) + "," + str(
				x) + "]" + ", [" + str(y) + ", " + str(y) + ", " + str(y + h) + ", " + str(y + h) + ", " + str(
				y) + "], " + "'" + color + "-'" + ")\n")
		file.write("print " + filename + "\n")
		file.close()

		try:
			os.system("octave --silent --no-window-system /tmp/layout.m");
		except e:
			utils.info(0, "WARNING: couldn't run octave to produce layout visualizaton")
			return

		utils.info(0, "File '" + filename + "' created")
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

	"""  Is a rectangle included in another (first one contained in second one)
		"""

	@staticmethod
	def rectangle_is_contained_in(bottom_left_1, top_right_1, bottom_left_2, top_right_2):

		if (bottom_left_1[0] < bottom_left_2[0] - FLOATING_POINT_EPSILON) or (bottom_left_1[1] < bottom_left_2[1] - FLOATING_POINT_EPSILON):
			# print '\ninductor x = ',bottom_left_1[0],'\nchip x = ',bottom_left_2[0],'\ninductor y = ',bottom_left_1[1],'\nchip y = ',bottom_left_2[1]
			return False
		if (top_right_1[0] > top_right_2[0] + FLOATING_POINT_EPSILON) or (top_right_1[1] > top_right_2[1] + FLOATING_POINT_EPSILON):
			# print '\ninductor top x = ',top_right_1[0],'\nchip top x = ',top_right_2[0],'\ninductor  top y = ',top_right_1[1],'\nchip top y = ',top_right_2[1],'\n'
			return False
		return True

	""" A function that hotspot to find out the max temp of the layout
			- the layout
			 - power_distribution: the power distribution
	"""

	@staticmethod
	def compute_layout_temperature(layout, power_distribution):

		# This is a hack because it seems the scipy library ignores the bounds and will go into
		# unallowed values, so instead we return a very high temperature (lame)
		for i in range(0, layout.get_num_chips()):
			if ((power_distribution[i] < layout.get_chip().get_power_levels()[0]) or (
					power_distribution[i] > layout.get_chip().get_power_levels()[-1])):
				return 100000

		# Create the input file and ptrace_files
		random_number = random.randint(0, 100000000)
		input_file_name = "/tmp/layout-optimization-tmp-" + str(random_number) + ".data"
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
					input_file.write(layout.get_chip().name + " " + str(layout.get_chip_positions()[i][0]) + " " + str(
						layout.get_chip_positions()[i][1]) + " " + str(
						layout.get_chip_positions()[i][2]) + " " + suffix + " " + "0\n")
					break

			if (ptrace_file_name == None):  # Couldn't find a good one, so we use a model
				suffix = "layout-optimization-tmp-" + str(i)
				input_file.write(layout.get_chip().name + " " + str(layout.get_chip_positions()[i][0]) + " " + str(
					layout.get_chip_positions()[i][1]) + " " + str(
					layout.get_chip_positions()[i][2]) + " " + suffix + " " + "0\n")
				ptrace_file_name = Layout.create_ptrace_file("./PTRACE", layout.get_chip(), suffix,
															 power_distribution[i])
				utils.info(3, "Created a custom ptrace file since power level is custom...")
				tmp_ptrace_file_names.append(ptrace_file_name)

		input_file.close()

		# Call hotspot
		if utils.argv.test:
			# command_line = "./fake_hotspot_LL.py " + input_file_name + " " + layout.get_medium() + " --no_images"
			return 58
			#command_line = "python fake_hotspot_LL.py " + input_file_name + " " + layout.get_medium() + " --no_images"
		# print "calling FAKE hotspot"
		else:
			# print "calling real hotspot"
			command_line = "./hotspot.py " + input_file_name + " " + layout.get_medium() + " --no_images"
		utils.info(3, "--> " + command_line)
		# layout.draw_in_3D("./broken2.pdf", False)
		try:
			devnull = open('/dev/null', 'w')
			proc = subprocess.Popen(command_line, stdout=subprocess.PIPE, shell=True, stderr=devnull)
		except Exception, e:
			utils.abort("Could not invoke hotspot.py correctly: " + str(e))

		string_output = proc.stdout.read().rstrip()
		#		print 'STRING OUTPUT ',string_output
		try:
			# tokens = string_output.split(" ")
			# temperature = float(tokens[2])
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
			ptrace_file.write(
				"NULL0 NULL1 NULL2 NULL3 0_CORE 1_CORE 2_CORE 3_CORE 4_CORE 5_CORE 6_CORE 7_CORE 0_LL 1_LL 2_LL 3_LL 4_LL 5_LL 6_LL 7_LL\n")
			ptrace_file.write("0 " * 4)
			ptrace_file.write((str(power_per_core) + " ") * 8)
			ptrace_file.write("0 " * 8)  # TODO TODO TODO TODO
			ptrace_file.write("\n")

		elif (chip.name == "base2"):
			# power_per_core * 4 + power_per_cache * 12 = power
			# power_per_cache = alpha + power_per_core / beta
			alpha = 0.57
			beta = 2.67
			# ==> 12 * alpha +  12 * power_per_core  / beta  + power_per_core * 4 = power
			# ==>  power_per_core = (power - 12 * alpha)  / (4 + 12 / beta)
			# ==>  power_per_cache = alpha + power_per_core / beta

			power_per_core = (power - 12 * alpha) / (4 + 12 / beta)
			power_per_cache = alpha + power_per_core / beta

			# print "POWER = ", power
			# print "CREATED POWER = ", 12 * power_per_cache + 4 * power_per_core

			ptrace_file.write("L2C0 L2C1 L2C2 L2C3 L2C4 L2C5 L2C6 L2C7 L2C8 L2C9 L2C10 L2C11 CORE0 CORE1 CORE2 CORE3\n")
			ptrace_file.write((str(power_per_cache) + " ") * 12)
			ptrace_file.write((str(power_per_core) + " ") * 4)
			ptrace_file.write("\n")

		elif (chip.name == "phi7250"):
			power_per_core = power / (2.0 * 42.0)
			ptrace_file.write(
				"EDGE_0 EDGE_1 EDGE_2 EDGE_3 0_NULL_0 0_NULL_1 0_CORE_0 0_CORE_1 1_NULL_0 1_NULL_1 1_CORE_0 1_CORE_1 2_NULL_0 2_NULL_1 2_CORE_0 2_CORE_1 3_NULL_0 3_NULL_1 3_CORE_0 3_CORE_1 4_NULL_0 4_NULL_1 4_CORE_0 4_CORE_1 5_NULL_0 5_NULL_1 5_CORE_0 5_CORE_1 6_NULL_0 6_NULL_1 6_CORE_0 6_CORE_1 7_NULL_0 7_NULL_1 7_CORE_0 7_CORE_1 8_NULL_0 8_NULL_1 8_CORE_0 8_CORE_1 9_NULL_0 9_NULL_1 9_CORE_0 9_CORE_1 10_NULL_0 10_NULL_1 10_CORE_0 10_CORE_1 11_NULL_0 11_NULL_1 11_CORE_0 11_CORE_1 12_NULL_0 12_NULL_1 12_CORE_0 12_CORE_1 13_NULL_0 13_NULL_1 13_CORE_0 13_CORE_1 14_NULL_0 14_NULL_1 14_CORE_0 14_CORE_1 15_NULL_0 15_NULL_1 15_CORE_0 15_CORE_1 16_NULL_0 16_NULL_1 16_CORE_0 16_CORE_1 17_NULL_0 17_NULL_1 17_CORE_0 17_CORE_1 18_NULL_0 18_NULL_1 18_CORE_0 18_CORE_1 19_NULL_0 19_NULL_1 19_CORE_0 19_CORE_1 20_NULL_0 20_NULL_1 20_CORE_0 20_CORE_1 21_NULL_0 21_NULL_1 21_CORE_0 21_CORE_1 22_NULL_0 22_NULL_1 22_CORE_0 22_CORE_1 23_NULL_0 23_NULL_1 23_CORE_0 23_CORE_1 24_NULL_0 24_NULL_1 24_CORE_0 24_CORE_1 25_NULL_0 25_NULL_1 25_CORE_0 25_CORE_1 26_NULL_0 26_NULL_1 26_CORE_0 26_CORE_1 27_NULL_0 27_NULL_1 27_CORE_0 27_CORE_1 28_NULL_0 28_NULL_1 28_CORE_0 28_CORE_1 29_NULL_0 29_NULL_1 29_CORE_0 29_CORE_1 30_NULL_0 30_NULL_1 30_CORE_0 30_CORE_1 31_NULL_0 31_NULL_1 31_CORE_0 31_CORE_1 32_NULL_0 32_NULL_1 32_CORE_0 32_CORE_1 33_NULL_0 33_NULL_1 33_CORE_0 33_CORE_1 34_NULL_0 34_NULL_1 34_CORE_0 34_CORE_1 35_NULL_0 35_NULL_1 35_CORE_0 35_CORE_1 36_NULL_0 36_NULL_1 36_CORE_0 36_CORE_1 37_NULL_0 37_NULL_1 37_CORE_0 37_CORE_1 38_NULL_0 38_NULL_1 38_CORE_0 38_CORE_1 39_NULL_0 39_NULL_1 39_CORE_0 39_CORE_1 40_NULL_0 40_NULL_1 40_CORE_0 40_CORE_1 41_NULL_0 41_NULL_1 41_CORE_0 41_CORE_1\n")
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
			for i in xrange(0, 3):
				ptrace_file.write((str(power_per_core) + " ") * 2)
				ptrace_file.write("0 " * 2)
			ptrace_file.write((str(power_per_core) + " ") * 2)
			ptrace_file.write("0 " * 6)
			for i in xrange(0, 7):
				ptrace_file.write((str(power_per_core) + " ") * 2)
				ptrace_file.write("0 " * 2)
			ptrace_file.write((str(power_per_core) + " ") * 2)
			ptrace_file.write("0 " * 10)
			ptrace_file.write((str(power_per_core) + " ") * 2)
			ptrace_file.write("0 " * 2)
			ptrace_file.write((str(power_per_core) + " ") * 2)
			ptrace_file.write("\n")

		else:
			utils.abort("Error: Chip '" + chip.name + "' unsupported!")

		ptrace_file.close()
		return ptrace_file_name

	"""Helper function that returns a randomly placed rectangle that overlaps
		   with another rectangle by a fixed amount, avoiding all negative coordinates
			- rectangle1_bottom_left = [x,y]: bottom left corner of the initial rectangle
			- rectangle_dimensions = [x,y]: size of the rectangle sides
			   - overlap: the fraction of overlap
		- shape:
			- "strip"	(full length of the chip)
			- "square"	(same aspect ratio as the chip)
			- "strip or square"
			- "any"
		   returns:
			- [x,y]: bottom left corner of the new rectangle
	"""

	@staticmethod
	def get_random_overlapping_rectangle(rectangle1_bottom_left, rectangle_dimensions, overlap, shape):

		if shape is None:
			# print 'shape is', None
			shape = "any"

		[rectangle1_x, rectangle1_y] = rectangle1_bottom_left
		[dim_x, dim_y] = rectangle_dimensions

		candidates = []

		if shape == "strip or square":
			if (random.uniform(0, 1) < 0.5):
				shape = "strip"
			else:
				shape = "square"

		# Assume for now that the overlap is in the North-East region

		if shape == "any":
			# pick an x value
			picked_x = random.uniform(rectangle1_x, rectangle1_x + dim_x - overlap * dim_x)
			# compute the y value that makes the right overlap
			picked_y = rectangle1_y + dim_y - (overlap * dim_x * dim_y) / (rectangle1_x + dim_x - picked_x)
		elif shape == "strip":
			picked_x = rectangle1_x + (1.0 - overlap) * dim_x
			picked_y = rectangle1_y
		elif shape == "square":
			picked_x = rectangle1_x + dim_x - sqrt(overlap) * dim_x
			picked_y = rectangle1_y + dim_y - sqrt(overlap) * dim_y
		else:
			utils.abort("get_random_overlapping_rectangle(): Invalid shape parameter " + str(shape))

		# Add this to the set of candidates
		candidates.append([picked_x, picked_y])

		# print "NORTHEAST = ", [picked_x, picked_y]

		# Consider all other symmetries

		# South-East
		new_picked_x = picked_x
		# new_picked_y = (rectangle1_y  + dim_y) - picked_y - dim_y
		new_picked_y = (rectangle1_y + dim_y - picked_y) + rectangle1_y - dim_y
		# print "SOUTHEAST =  ", [new_picked_x, new_picked_y]
		if (new_picked_x >= 0) and (new_picked_y >= 0):
			candidates.append([new_picked_x, new_picked_y])

		# North-West
		new_picked_x = (rectangle1_x + dim_x - picked_x) + rectangle1_x - dim_x
		new_picked_y = picked_y
		# print "NORTHWEST = ", [new_picked_x, new_picked_y]
		if (new_picked_x >= 0) and (new_picked_y >= 0):
			candidates.append([new_picked_x, new_picked_y])

		# South-West
		new_picked_x = (rectangle1_x + dim_x - picked_x) + rectangle1_x - dim_x
		new_picked_y = (rectangle1_y + dim_y - picked_y) + rectangle1_y - dim_y
		# print "SOUTHWEST = ", [new_picked_x, new_picked_y]
		if (new_picked_x >= 0) and (new_picked_y >= 0):
			candidates.append([new_picked_x, new_picked_y])

		# At this point, we just pick one of the candidates at random
		picked_candidate = utils.pick_random_element(candidates)
		return picked_candidate


	""" Function that returns a feasible, random, neigbhor of specified chip
		- chip_index
		   returns:
			- [level, x, y]
	"""
	#@jit
	def get_random_feasible_neighbor_position(self, chip_index):
		chip_position = self.__chip_positions[chip_index]

		# Pick a random location relative to the last chip
		# getout = 0 #program hanging, cant find a valid random overlapping rectangle
		max_num_trials = 100
		num_trials = 0
		"""
		xdim = utils.argv.chip.x_dimension
		ydim = utils.argv.chip.y_dimension
		xhalf = chip_position[1]+.5*xdim
		yhalf = chip_position[2]+.5*ydim
		inductor = self.__inductor_properties[-1]
		ix = inductor[1]
		iy = inductor[2]
		ixx = inductor[3]
		iyy = inductor[4]
		ixxhalf = inductor[1]+inductor[3]
		iyyhalf = inductor[2]+inductor[4]
		print 'inductor ',ix, '' ,iy,' ',ixxhalf,' ',iyyhalf
		print 'chip position is ', chip_position
		print 'x half = ',xhalf,'\nyhalf = ',yhalf,'\n'
		"""
		while (num_trials < max_num_trials):
			num_trials += 1
			# pick a random level
			possible_levels = []
			if (chip_position[0] == 1):
				possible_levels = [2]
			elif (chip_position[0] == utils.argv.num_levels):
				possible_levels = [utils.argv.num_levels - 1]
			else:
				possible_levels = [chip_position[0] - 1, chip_position[0] + 1]
			# utils.info(1,"chip_position %s\n"%chip_position)
			picked_level = utils.pick_random_element(possible_levels)
			# print"picked_level %s\n"%picked_level
			[picked_x, picked_y] = Layout.get_random_overlapping_rectangle([chip_position[1], chip_position[2]], [self.__chip.x_dimension, self.__chip.y_dimension], utils.argv.overlap, utils.argv.constrained_overlap_geometry)
			#print 'picked = ',picked_x,' ', picked_y
			if (self.can_new_chip_fit([picked_level, picked_x, picked_y])):
				if not self.check_cross_talk(self.get_new_inductor_properties([picked_level, picked_x, picked_y], chip_position)):
					utils.info(3, "Found a feasible random neighbor for chip #" + str(chip_index))
					#print "!!!GREAT!!!"
					return [picked_level, picked_x, picked_y];
		utils.info(3, "Could not find a feasible random neighbor for chip #" + str(chip_index))
		return None
		#return [3,0.078,0.07475]


##############################################################################################
### LAYOUT BUILDER CLASS
##############################################################################################


class LayoutBuilder(object):

	def __init__(self):
		pass

	""" Function to compute a stacked layout
	"""

	@staticmethod
	def compute_stacked_layout(num_chips):
		"""
		MAX num_chips > 9 does not seem to work.  Hotspot.c fails to produce tmp.grid.steady
		"""
		# utils.abort(" inductor_properties need to be added when building")
		inductor_properties = []
		if (utils.argv.overlap is None):
			utils.abort(" Need to specifiy Overlap")
		positions = []
		inductor_x_dim = inductor_y_dim = utils.argv.chip.x_dimension - (
				utils.argv.chip.x_dimension * (1 - sqrt(utils.argv.overlap)))
		for level in xrange(1, num_chips + 1):
			positions.append([level, 0.0, 0.0])
			if level % 2 == 0:
				inductor_properties.append([level, 0, 0, inductor_x_dim, inductor_y_dim])
			else:
				inductor_properties.append(
					[level, utils.argv.chip.x_dimension - inductor_x_dim, utils.argv.chip.y_dimension - inductor_y_dim,
					 inductor_x_dim, inductor_y_dim])
		return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap, inductor_properties[:-1])

	"""Function to compute a straight linear layout
	"""

	@staticmethod
	def compute_rectilinear_straight_layout(num_chips):

		positions = []
		inductor_properties = []
		current_level = 1
		level_direction = 1
		inductor_level = 1
		inductor_direction = 1
		current_x_position = 0.0
		current_y_position = 0.0
		for i in xrange(0, num_chips):
			positions.append([current_level, current_x_position, current_y_position])
			current_level += level_direction
			if (current_level > utils.argv.num_levels):
				current_level = utils.argv.num_levels - 1
				level_direction = -1
			# print 'first if'
			if (current_level < 1):
				current_level = 2
				level_direction = 1
			# print 'second if'
			# print '\tcurrent level is ', current_level#, '\npositions ',positions
			current_x_position += utils.argv.chip.x_dimension * (1 - utils.argv.overlap)
			# print "\t\tinductor level is ", min(current_level,positions[i][0])
			inductor_properties.append([min(current_level, positions[i][0]), current_x_position, current_y_position,
										utils.argv.chip.x_dimension - (
												utils.argv.chip.x_dimension * (1 - utils.argv.overlap)),
										utils.argv.chip.y_dimension])
		# inductor_level = 1
		# print 'inductor properites', inductor_properties
		return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap, inductor_properties[:-1])

	"""Function to compute a diagonal linear layout
	"""

	@staticmethod
	def compute_rectilinear_diagonal_layout(num_chips):

		if utils.argv.overlap > .25:
			utils.info(0, 'WARNING overlap too big\nchips may collide on same level and crosstalk likely')
		positions = []
		inductor_properties = []
		current_level = 1
		level_direction = 1
		# HENRI DEBUG
		current_x_position = 0
		current_y_position = 0
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
			inductor_properties.append([min(current_level, positions[i][0]), current_x_position, current_y_position, (utils.argv.chip.x_dimension * sqrt(utils.argv.overlap)), (utils.argv.chip.y_dimension * sqrt(utils.argv.overlap))])

		return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap, inductor_properties[:-1])

	#	return layout

	"""Function to compute a cradle layout """

	@staticmethod
	def compute_cradle_layout(num_chips):
		###################################
		### TODO
		###	- correct collision when diagonal cradle overlap >.25
		### - check on -C options, both???
		###################################

		positions = []
		inductor_properties = []
		any = -1

		if num_chips != 3:
			utils.abort("Can only compute a cradle  with 3 chips")

		x_dim = utils.argv.chip.x_dimension
		y_dim = utils.argv.chip.y_dimension

		if x_dim != y_dim:
			utils.abort("Cannot compute a cradle layout non-square chips (to be implemented)")
		#print 'shape ',utils.argv.constrained_overlap_geometry

		overlap = utils.argv.overlap
		overlap_shape = utils.argv.constrained_overlap_geometry
		if overlap_shape is None:
			overlap_shape = 'any'
		if 'any' in overlap_shape:
			overlap_shape = 'square' ###set to square b/c it gives more potions when adding
			#any = utils.pick_random_element([0,1])
			#overlap_shape = random.choice(['square','strip']) ###TODO: set globally???
			#print "\n\nany is "+str(any)+"\n\n"
		"""apply shift"""
		shift = 5
		x_shift = x_dim * shift
		y_shift = y_dim * shift

		# Add the base structures on top of each other
		current_level = 1
		current_orientation = 0
		if 'strip' in overlap_shape:
			chip1_level = chip3_level = current_level+1
			chip2_level = current_level

			chip1_x = 0 * x_dim
			chip1_y = chip2_y = chip3_y = (1 - overlap) * y_dim

			chip2_x = chip1_x + (1 - overlap) * x_dim

			chip3_x = chip2_x + (1 - overlap) * x_dim

			inductor1_level = inductor2_level = current_level
			inductor1_x = chip2_x
			inductor1_y = chip2_y
			inductor1_xdim = inductor2_xdim = x_dim * (overlap)
			inductor1_ydim = inductor2_ydim = y_dim

			inductor2_x = chip3_x
			inductor2_y = chip3_y
		elif 'square' in overlap_shape:
			if overlap > .25:
				utils.abort("\nCan't build cradle with overlap greater than .25 and square overlap\nCollisions occur\nChange overlap or shape contraiant")
			chip1_level = chip3_level = current_level+1
			chip2_level = current_level

			chip1_x = 0 * x_dim
			chip1_y = (1 - overlap) * y_dim

			chip2_x = chip1_x + x_dim*(1-sqrt(overlap))
			chip2_y = chip1_y + y_dim*(1-sqrt(overlap))

			chip3_x = chip2_x + x_dim*(1-sqrt(overlap))
			chip3_y = chip2_y + y_dim*(1-sqrt(overlap))

			inductor1_level = inductor2_level = current_level

			inductor1_x = chip2_x
			inductor1_y = chip2_y

			inductor2_x = chip3_x
			inductor2_y = chip3_y

			inductor1_xdim = inductor2_xdim = x_dim * sqrt(overlap)
			inductor1_ydim = inductor2_ydim = y_dim * sqrt(overlap)
		else:
			utils.abort("Invalid shape  constraint")  # dont know if this check is needed

		positions.append([chip1_level, chip1_x + x_shift, chip1_y + y_shift])
		positions.append([chip2_level, chip2_x + x_shift, chip2_y + y_shift])
		positions.append([chip3_level, chip3_x + x_shift, chip3_y + y_shift])
		inductor_properties.append([inductor1_level, inductor1_x + x_shift, inductor1_y + y_shift, inductor1_xdim, inductor1_ydim])
		inductor_properties.append([inductor2_level, inductor2_x + x_shift, inductor2_y + y_shift, inductor2_xdim, inductor2_ydim])

						# # Is there an extra chip?
		# if (num_chips % 3 == 1):
		#     positions.append([current_level, (1 - overlap) * x_dim, (1 - overlap) * y_dim])
		return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap, inductor_properties)

	"""Function to comput double helix"""
	@staticmethod
	def compute_double_helix(num_chips):
		utils.info(0,"Warning level, diameter, and shape constraints ignored")
		positions = []
		inductor_properties = []
		any = -1
		helices = 1 #TODO: set from argument

		x_dim = utils.argv.chip.x_dimension
		y_dim = utils.argv.chip.y_dimension

		if x_dim != y_dim:
			utils.abort("Cannot compute a cradle layout non-square chips (to be implemented)")

		overlap = utils.argv.overlap
		overlap_shape = utils.argv.constrained_overlap_geometry

		"""apply shift"""
		shift = 5
		x_shift = x_dim * shift
		y_shift = y_dim * shift
		inductor_xdim = x_dim*sqrt(overlap)
		inductor_ydim = y_dim*sqrt(overlap)

		# Add the base structures on top of each other
		current_level = 1
		highest_level = 1

		for helix in range(1,helices+1): #TODO: only works for 1 helix level
			chip1_x = 0
			chip1_y = 0
			chip1_level = helix
			#print 'chip 1 level ', chip1_level

			chip2_level = chip3_level = chip1_level+1
			chip2_x = chip1_x + x_dim*(1-sqrt(overlap))
			chip2_y = chip1_y + y_dim*(1-sqrt(overlap))
			chip3_x = chip1_x - x_dim*(1-sqrt(overlap))
			chip3_y = chip1_y - y_dim*(1-sqrt(overlap))
			ind2_level = ind3_level = chip1_level
			ind2_x = chip2_x
			ind2_y = chip2_y
			ind3_x = chip1_x
			ind3_y = chip1_y
			#print ind2_level,' ',ind3_level
			#print 'chip 2 level ', chip2_level

			chip4_level = chip5_level = chip1_level+2
			chip4_x = chip5_x = chip1_x
			chip4_y = chip1_y+y_dim
			chip5_y = chip1_y-y_dim
			ind4_level = ind5_level = chip2_level
			ind4_x = ind2_x
			ind4_y = ind2_y + inductor_ydim
			ind5_x = ind3_x
			ind5_y = ind3_y - inductor_ydim
			#print ind4_level,' ',ind5_level
			#print chip4_level,' ',chip5_level
			#print 'chip 4 level ', chip4_level

			highest_level = chip6_level = chip7_level = chip1_level+3
			chip6_x = chip1_x - x_dim*(1-sqrt(overlap))
			chip6_y = chip1_y + y_dim*(1-sqrt(overlap))
			chip7_x = chip1_x + x_dim*(1-sqrt(overlap))
			chip7_y = chip1_y - y_dim*(1-sqrt(overlap))
			ind6_level = ind7_level = chip4_level
			ind6_x = chip6_x
			ind6_y = chip6_y
			ind7_x = chip7_x
			ind7_y = chip7_y
			#print 'chip 6 level ', chip6_level

			positions.append([chip1_level, chip1_x + x_shift, chip1_y + y_shift])
			positions.append([chip2_level, chip2_x + x_shift, chip2_y + y_shift])
			positions.append([chip3_level, chip3_x + x_shift, chip3_y + y_shift])
			positions.append([chip4_level, chip4_x + x_shift, chip4_y + y_shift])
			positions.append([chip5_level, chip5_x + x_shift, chip5_y + y_shift])
			positions.append([chip6_level, chip6_x + x_shift, chip6_y + y_shift])
			positions.append([chip7_level, chip7_x + x_shift, chip7_y + y_shift])

			inductor_properties.append([ind2_level, ind2_x + x_shift, ind2_y + y_shift, inductor_xdim, inductor_ydim])
			inductor_properties.append([ind3_level, ind3_x + x_shift, ind3_y + y_shift, inductor_xdim, inductor_ydim])
			inductor_properties.append([ind4_level, ind4_x + x_shift, ind4_y + y_shift, inductor_xdim, inductor_ydim])
			inductor_properties.append([ind5_level, ind5_x + x_shift, ind5_y + y_shift, inductor_xdim, inductor_ydim])
			inductor_properties.append([ind6_level, ind6_x + x_shift, ind6_y + y_shift, inductor_xdim, inductor_ydim])
			inductor_properties.append([ind7_level, ind7_x + x_shift, ind7_y + y_shift, inductor_xdim, inductor_ydim])
			#inductor_properties.append([ind8_level, ind8_x + x_shift, ind8_y + y_shift, inductor_xdim, inductor_ydim])

		if len(positions)%8!=0:
			positions.append([highest_level+1,chip1_x + x_shift,chip1_y+ y_shift])
			inductor_properties.append([highest_level, ind2_x - inductor_xdim+ x_shift, ind2_y + y_shift, inductor_xdim, inductor_ydim])
			inductor_properties.append([highest_level, ind3_x + inductor_xdim + x_shift, ind3_y + y_shift, inductor_xdim, inductor_ydim])

		return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap, inductor_properties)
#layout = Layout(7,positions,utils.argv.medium, utils.argv.overlap,)
			#inductor_properties.append([chip1_level, chip1_x + x_shift, chip1_y + y_shift, inductor_xdim, inductor_ydim])


	"""Function to compute a bridge layout """

	@staticmethod
	def compute_bridge_layout(num_chips):
		# utils.abort("inductor_properties need to be added when building")
		positions = []
		inductor_properties = []

		if (num_chips < 3):
			utils.abort("Cannot compute bridge layout with fewer than 3 chips")

		if ((num_chips % 3 != 0) and (num_chips % 3 != 1)):
			utils.abort("Cannot compute a bridge layout with a number of chips that's not of the form 3*k or 3*k+1")

		x_dim = utils.argv.chip.x_dimension
		y_dim = utils.argv.chip.y_dimension

		if (x_dim != y_dim):
			utils.abort("Cannot compute a bridge layout non-square chips")

		overlap = utils.argv.overlap

		# Add the base structures on top of each other
		current_level = 1
		current_orientation = 0
		for i in xrange(0, num_chips / 3):
			if current_orientation == 0:
				positions.append([current_level + 1, (1 - overlap) * x_dim, (1 - overlap) * y_dim])
				positions.append([current_level, 0 * x_dim, (1 - overlap) * y_dim])
				positions.append([current_level, 2 * (1 - overlap) * x_dim, (1 - overlap) * y_dim])
			# inductor_properties.append([current_level,(1 - overlap) * x_dim,(1 - overlap) * y_dim, x_dim*(overlap),y_dim])
			# inductor_properties.append([current_level,2*((1 - overlap) * x_dim), (1 - overlap) * y_dim, x_dim*(overlap),y_dim])
			else:
				utils.abort("Inductors need to be added")
				positions.append([current_level + 1, (1 - overlap) * x_dim, (1 - overlap) * y_dim])
				positions.append([current_level, (1 - overlap) * x_dim, 0])
				positions.append([current_level, (1 - overlap) * x_dim, 2 * (1 - overlap) * y_dim])

			current_level += 2
			current_orientation = 1 - current_orientation

		# Is there an extra chip?
		if (num_chips % 3 == 1):
			positions.append([current_level, (1 - overlap) * x_dim, (1 - overlap) * y_dim])

		layout = Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap, inductor_properties)
		for chip in positions:
			layout.connect_new_chip(chip)

		"""
		# Apply some shift for breathing room
		x_shift = x_dim * 3
		y_shift = y_dim * 3
		new_positions = []
		for [l, x, y] in positions:
			new_positions.append([l, x+ x_shift, y + y_shift])
		positions = new_positions
		"""
		# layout = Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap)
		# layout.draw_in_3D(None, True)
		# print "---> POSITIONS=", positions

		return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap, inductor_properties)

	"""Function to compute a generalized checkerboard layout (overlap > 0.25) """

	@staticmethod
	def compute_generalized_checkerboard_layout(num_chips):
		utils.abort("inductor_properties need to be added when building")

		positions = []

		if (num_chips < 3):
			utils.abort("Cannot compute a generalized checkerboard layout with fewer than 3 chips")

		if ((num_chips % 3 != 0) and (num_chips % 3 != 1)):
			utils.abort(
				"Cannot compute a generalized checkerboard layout with a number of chips that's not of the form 3*k or 3*k+1")

		x_dim = utils.argv.chip.x_dimension
		y_dim = utils.argv.chip.y_dimension

		if (x_dim != y_dim):
			utils.abort("Cannot compute a generalized checkerboard layout non-square chips")

		overlap = utils.argv.overlap

		# Add the base structures on top of each other
		current_level = 1
		current_orientation = 0
		for i in xrange(0, num_chips / 3):
			if current_orientation == 0:
				positions.append([current_level, (1 - overlap) * x_dim, (1 - overlap) * y_dim])
				positions.append([current_level + 1, 0 * x_dim, (1 - overlap) * y_dim])
				positions.append([current_level + 1, 2 * (1 - overlap) * x_dim, (1 - overlap) * y_dim])
			else:
				positions.append([current_level, (1 - overlap) * x_dim, (1 - overlap) * y_dim])
				positions.append([current_level + 1, (1 - overlap) * x_dim, 0])
				positions.append([current_level + 1, (1 - overlap) * x_dim, 2 * (1 - overlap) * y_dim])

			current_level += 2
			current_orientation = 1 - current_orientation

		# Is there an extra chip?
		if (num_chips % 3 == 1):
			positions.append([current_level, (1 - overlap) * x_dim, (1 - overlap) * y_dim])

		# Apply some shift for breathing room
		x_shift = x_dim * 3
		y_shift = y_dim * 3
		new_positions = []
		for [l, x, y] in positions:
			new_positions.append([l, x + x_shift, y + y_shift])
		positions = new_positions

		# layout = Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap)
		# layout.draw_in_3D(None, True)
		# print "---> POSITIONS=", positions

		return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap)

	@staticmethod
	def plot_custom_layout(positions):
		layout = Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap)
		layout.draw_in_3D(None, True)

	"""Function to compute a checkerboard layout"""

	@staticmethod
	def compute_checkerboard_layout(num_chips):
		utils.abort("inductor_properties need to be added when building")

		if (utils.argv.overlap > 0.5):
			utils.abort("A checkerboard layout can only be built with overlap <= 0.25")

		if (utils.argv.overlap > 0.25):
			utils.info(2, "Computing a generalized checkerboard with more than 1/4-th overlap")
			return LayoutBuilder.compute_generalized_checkerboard_layout(num_chips)

		if (num_chips == 3):
			utils.info(2, "Computing a generalized checkerboard with 3 chips")
			return LayoutBuilder.compute_generalized_checkerboard_layout(num_chips)

		positions = []
		alpha = sqrt(utils.argv.overlap)
		x_overlap = alpha * utils.argv.chip.x_dimension
		y_overlap = alpha * utils.argv.chip.y_dimension

		x_offset = utils.argv.chip.x_dimension - x_overlap
		y_offset = utils.argv.chip.y_dimension - y_overlap

		if ((num_chips == 5) and (utils.argv.num_levels == 2)):
			# Create level 1
			positions.append([1, 0 + 0 * x_offset, y_offset + 0 * y_offset])
			positions.append([1, 0 + 0 * x_offset, y_offset + 2 * y_offset])
			positions.append([1, 0 + 2 * x_offset, y_offset + 0 * y_offset])
			positions.append([1, 0 + 2 * x_offset, y_offset + 2 * y_offset])

			# Create level 2
			positions.append([2, x_offset + 0 * x_offset, 2 * y_offset])

		elif ((num_chips == 9) and (utils.argv.num_levels == 2)):
			# Create level 1
			positions.append([1, x_offset + 0 * x_offset, y_offset + 0 * y_offset])
			positions.append([1, x_offset + 0 * x_offset, y_offset + 2 * y_offset])
			positions.append([1, x_offset + 2 * x_offset, y_offset + 0 * y_offset])
			positions.append([1, x_offset + 2 * x_offset, y_offset + 2 * y_offset])

			# Create level 2
			positions.append([2, 0 + 0 * x_offset, 2 * y_offset])
			positions.append([2, 0 + 2 * x_offset, 0 * y_offset])
			positions.append([2, 0 + 2 * x_offset, 2 * y_offset])
			positions.append([2, 0 + 2 * x_offset, 4 * y_offset])
			positions.append([2, 0 + 4 * x_offset, 2 * y_offset])

		elif ((num_chips == 9) and (utils.argv.num_levels == 3)):

			# Create level 1
			positions.append([1, 0 + 0 * x_offset, y_offset + 0 * y_offset])
			positions.append([1, 0 + 0 * x_offset, y_offset + 2 * y_offset])
			positions.append([1, 0 + 2 * x_offset, y_offset + 0 * y_offset])
			positions.append([1, 0 + 2 * x_offset, y_offset + 2 * y_offset])

			# Create level 2
			positions.append([2, x_offset + 0 * x_offset, 2 * y_offset])

			# Create level 3
			positions.append([3, 0 + 0 * x_offset, y_offset + 0 * y_offset])
			positions.append([3, 0 + 0 * x_offset, y_offset + 2 * y_offset])
			positions.append([3, 0 + 2 * x_offset, y_offset + 0 * y_offset])
			positions.append([3, 0 + 2 * x_offset, y_offset + 2 * y_offset])

		elif ((num_chips == 13) and (utils.argv.num_levels == 2)):
			# Create level 2
			positions.append([2, x_offset + 0 * x_offset, y_offset + 0 * y_offset])
			positions.append([2, x_offset + 0 * x_offset, y_offset + 2 * y_offset])
			positions.append([2, x_offset + 2 * x_offset, y_offset + 0 * y_offset])
			positions.append([2, x_offset + 2 * x_offset, y_offset + 2 * y_offset])

			# Create level 2
			positions.append([1, 0 + 0 * x_offset, 0 * y_offset])
			positions.append([1, 0 + 0 * x_offset, 2 * y_offset])
			positions.append([1, 0 + 0 * x_offset, 4 * y_offset])
			positions.append([1, 0 + 2 * x_offset, 0 * y_offset])
			positions.append([1, 0 + 2 * x_offset, 2 * y_offset])
			positions.append([1, 0 + 2 * x_offset, 4 * y_offset])
			positions.append([1, 0 + 4 * x_offset, 0 * y_offset])
			positions.append([1, 0 + 4 * x_offset, 2 * y_offset])
			positions.append([1, 0 + 4 * x_offset, 4 * y_offset])

		elif ((num_chips == 13) and (utils.argv.num_levels == 3)):

			# Create level 1
			positions.append([1, x_offset + 0 * x_offset, y_offset + 0 * y_offset])
			positions.append([1, x_offset + 0 * x_offset, y_offset + 2 * y_offset])
			positions.append([1, x_offset + 2 * x_offset, y_offset + 0 * y_offset])
			positions.append([1, x_offset + 2 * x_offset, y_offset + 2 * y_offset])

			# Create level 2
			positions.append([2, 0 + 0 * x_offset, 2 * y_offset])
			positions.append([2, 0 + 2 * x_offset, 0 * y_offset])
			positions.append([2, 0 + 2 * x_offset, 2 * y_offset])
			positions.append([2, 0 + 2 * x_offset, 4 * y_offset])
			positions.append([2, 0 + 4 * x_offset, 2 * y_offset])

			# Create level 3
			positions.append([3, x_offset + 0 * x_offset, y_offset + 0 * y_offset])
			positions.append([3, x_offset + 0 * x_offset, y_offset + 2 * y_offset])
			positions.append([3, x_offset + 2 * x_offset, y_offset + 0 * y_offset])
			positions.append([3, x_offset + 2 * x_offset, y_offset + 2 * y_offset])

		elif ((num_chips == 21) and (utils.argv.num_levels == 2)):
			# Create level 1
			positions.append([1, 0 + 0 * x_offset, 0 + 2 * y_offset])
			positions.append([1, 0 + 0 * x_offset, 0 + 4 * y_offset])

			positions.append([1, 0 + 2 * x_offset, 0 + 0 * y_offset])
			positions.append([1, 0 + 2 * x_offset, 0 + 2 * y_offset])
			positions.append([1, 0 + 2 * x_offset, 0 + 4 * y_offset])
			positions.append([1, 0 + 2 * x_offset, 0 + 6 * y_offset])

			positions.append([1, 0 + 4 * x_offset, 0 + 0 * y_offset])
			positions.append([1, 0 + 4 * x_offset, 0 + 2 * y_offset])
			positions.append([1, 0 + 4 * x_offset, 0 + 4 * y_offset])
			positions.append([1, 0 + 4 * x_offset, 0 + 6 * y_offset])

			positions.append([1, 0 + 6 * x_offset, 0 + 2 * y_offset])
			positions.append([1, 0 + 6 * x_offset, 0 + 4 * y_offset])

			# Create level 2
			positions.append([2, x_offset + 0 * x_offset, y_offset + 0 * y_offset])
			positions.append([2, x_offset + 0 * x_offset, y_offset + 2 * y_offset])
			positions.append([2, x_offset + 0 * x_offset, y_offset + 4 * y_offset])
			positions.append([2, x_offset + 2 * x_offset, y_offset + 0 * y_offset])
			positions.append([2, x_offset + 2 * x_offset, y_offset + 2 * y_offset])
			positions.append([2, x_offset + 2 * x_offset, y_offset + 4 * y_offset])
			positions.append([2, x_offset + 4 * x_offset, y_offset + 0 * y_offset])
			positions.append([2, x_offset + 4 * x_offset, y_offset + 2 * y_offset])
			positions.append([2, x_offset + 4 * x_offset, y_offset + 4 * y_offset])

		elif ((num_chips == 21) and (utils.argv.num_levels == 3)):

			# Create level 1
			positions.append([1, 0 + 0 * x_offset, 0 + 0 * y_offset])
			positions.append([1, 0 + 0 * x_offset, 0 + 2 * y_offset])
			positions.append([1, 0 + 0 * x_offset, 0 + 4 * y_offset])
			positions.append([1, 0 + 2 * x_offset, 0 + 0 * y_offset])
			positions.append([1, 0 + 2 * x_offset, 0 + 2 * y_offset])
			positions.append([1, 0 + 2 * x_offset, 0 + 4 * y_offset])
			positions.append([1, 0 + 4 * x_offset, 0 + 0 * y_offset])
			positions.append([1, 0 + 4 * x_offset, 0 + 2 * y_offset])
			positions.append([1, 0 + 4 * x_offset, 0 + 4 * y_offset])

			# Create level 2
			positions.append([2, x_offset + 0 * x_offset, y_offset + 0 * y_offset])
			positions.append([2, x_offset + 2 * x_offset, y_offset + 0 * y_offset])
			positions.append([2, x_offset + 0 * x_offset, y_offset + 2 * y_offset])
			positions.append([2, x_offset + 2 * x_offset, y_offset + 2 * y_offset])

			# Create level 3
			positions.append([3, 0 + 0 * x_offset, 0 + 0 * y_offset])
			positions.append([3, 0 + 0 * x_offset, 0 + 2 * y_offset])
			positions.append([3, 0 + 0 * x_offset, 0 + 4 * y_offset])
			positions.append([3, 0 + 2 * x_offset, 0 + 0 * y_offset])
			# positions.append([3, 0 + 2 * x_offset, 0 + 2 * y_offset])
			positions.append([3, 0 + 2 * x_offset, 0 + 4 * y_offset])
			positions.append([3, 0 + 4 * x_offset, 0 + 0 * y_offset])
			positions.append([3, 0 + 4 * x_offset, 0 + 2 * y_offset])
			positions.append([3, 0 + 4 * x_offset, 0 + 4 * y_offset])


		elif (utils.argv.num_levels == 2):

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
			# Create level 1
			for x in xrange(0, num_chips):
				for y in xrange(0, num_chips):
					positions.append([1, x * (2 * utils.argv.chip.x_dimension - 2 * x_overlap),
									  y * (2 * utils.argv.chip.y_dimension - 2 * y_overlap)])

			# Create level 2
			for x in xrange(0, num_chips):
				for y in xrange(0, num_chips):
					positions.append([2, utils.argv.chip.x_dimension - x_overlap + x * (
							2 * utils.argv.chip.x_dimension - 2 * x_overlap),
									  utils.argv.chip.y_dimension - y_overlap + y * (
											  2 * utils.argv.chip.y_dimension - 2 * y_overlap)])

			while (len(positions) > num_chips):
				max_x = max([x for [l, x, y] in positions])
				max_y = max([y for [l, x, y] in positions])
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

		else:
			utils.abort(
				"Error: Cannot compute a checkerboard layout with " + str(utils.argv.num_levels) + " levels and " + str(
					num_chips) + " chips")

		return Layout(utils.argv.chip, positions, utils.argv.medium, utils.argv.overlap)