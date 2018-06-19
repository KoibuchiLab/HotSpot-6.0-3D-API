#!/usr/bin/python

import sys
import random
from mpi4py import MPI
import copy

import utils
from layout import *
from power_optimizer import *
#from numba import jit


# from scipy.optimize import basinhopping
# from scipy.optimize import fmin_slsqp

FLOATING_POINT_EPSILON = 0.000001

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
	layout_scheme = utils.argv.layout_scheme.split(":")[0]

	if (layout_scheme == "stacked"):
		solution = optimize_layout_stacked()
	elif (layout_scheme == "rectilinear_straight"):
		solution = optimize_layout_rectilinear("straight")
	elif (layout_scheme == "rectilinear_diagonal"):
		solution = optimize_layout_rectilinear("diagonal")
	#elif (layout_scheme == "carbon"):
	#	solution = optimize_layout_carbon()
	elif (layout_scheme == "checkerboard"):
		solution = optimize_layout_checkerboard()
	elif (layout_scheme == "cradle"):
		solution = optimize_layout_cradle()
	elif (layout_scheme == "double_helix"):
		solution = optimize_layout_double_helix()
	elif (layout_scheme == "bridge"):
		solution = optimize_layout_bridge()
	elif (layout_scheme == "plot"):
		solution = plot_layout()
	elif (layout_scheme == "linear_random_greedy"):
		solution = optimize_layout_linear_random_greedy()
	elif (layout_scheme == "random_greedy"):
		if (utils.argv.mpi):
			solution = optimize_layout_random_greedy_mpi()
		# print "!!!!MPI!!!!!!!!!"
		else:
			solution = optimize_layout_random_greedy()
	# print "$$$$$$$$$$$regular$$$$$$$$$$"
	else:
		utils.abort("Layout scheme '" + utils.argv.layout_scheme + "' is not supported")

	return solution


"""plot layouts"""
def plot_layout():
	if (len(utils.argv.layout_scheme.split(":")) == 2):
		inputfile = str(utils.argv.layout_scheme.split(":")[1])
	f = open(inputfile, "r")
	positions = f.read()
	f.close()
	import ast
	positions = ast.literal_eval(positions)
	layout = LayoutBuilder.plot_custom_layout(positions)

	result = find_maximum_power_budget(layout)

	if result == None:
		return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]


	#return [layout, -1, -1]

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

	# layout.draw_in_3D(None, True);

	result = find_maximum_power_budget(layout)
	if (result == None):
		return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]


"""Linear random greedy layout optimization"""


def optimize_layout_linear_random_greedy():
	# Create an initial layout
	layout = Layout(utils.argv.chip, [[1, 0.0, 0.0]], utils.argv.medium, utils.argv.overlap,[])

	max_num_random_trials = 5  # TODO: Don't hardcode this
	while (layout.get_num_chips() != utils.argv.num_chips):
		utils.info(1, "* Generating " + str(max_num_random_trials) + " candidate positions for chip #" + str(
			1 + layout.get_num_chips()) + " in the layout")
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
			# print layout.get_chip_positions()
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


""" Helper function
 	Returns [power_distribution, temperature]"""


def evaluate_candidate(args):
	[layout, candidate] = args
	utils.info(1, "  - Evaluating candidate " + str(candidate))
	#print 'layout recieved ',layout
	#print '\ncandidates ', candidate
	dummy_layout = Layout(layout.get_chip(), layout.get_chip_positions(), layout.get_medium(), layout.get_overlap(), layout.get_inductor_properties())
	#print 'layout chips ', dummy_layout.get_chip_positions(),'\n'
	#print 'dummy layout is ',dummy_layout
	for chip in candidate:
		#print "HERE"
		try:
			dummy_layout.add_new_chip(chip)
		except:
			#print 'chip is ',chip
			#print 'layout chips ', dummy_layout.get_chip_positions()
			utils.abort("Add error in evaluate candidates")
	if (dummy_layout.get_diameter() > utils.argv.diameter):
		utils.abort("Layout diameter is too big (this should never happen here!)")

	return [dummy_layout, find_maximum_power_budget(dummy_layout)]


""" Function that returns a list of chip candidates"""

#@jit
def generate_candidates(layout, candidate_random_trials, num_neighbor_candidates, max_num_neighbor_candidate_attempts):
	utils.info(2, "* Generating " + str(num_neighbor_candidates) + " candidate positions for chip #" + str(
		1 + layout.get_num_chips()) + " in the layout")
	num_attempts = 0
	while ((len(candidate_random_trials) < num_neighbor_candidates) and (
			num_attempts < max_num_neighbor_candidate_attempts)):
		num_attempts += 1
		random_chip = utils.pick_random_element(range(0, layout.get_num_chips()))
		if (layout.get_longest_shortest_path_from_chip(random_chip) >= utils.argv.diameter):
			# utils.info(2, "Ooops, chip " + str(random_chip) + " won't work for the diameter");
			continue
		result = layout.get_random_feasible_neighbor_position(random_chip)
		if result == None:
			continue

		[picked_level, picked_x, picked_y] = result
		utils.info(1, "Candidate random neighbor of chip " + str(random_chip) + " : " + str(
			[picked_level, picked_x, picked_y]))
		candidate_random_trials.append([picked_level, picked_x, picked_y])

	return candidate_random_trials

"""
	Add candidates in cradles
	Returns list containing the positions of the 3 cradle chips
"""

def add_cradle(layout): ###TODO: could probably hard code num_chips_to_add to 3
	utils.info(2,"Adding by cradles")
	overlap = utils.argv.overlap
	chipx_dim = utils.argv.chip.x_dimension
	chipy_dim = utils.argv.chip.y_dimension
	any_shape = False
	overlap_shape = utils.argv.constrained_overlap_geometry
	#print 'global overlap ',utils.argv.constrained_overlap_geometry
	#if not('strip' in utils.argv.constrained_overlap_geometry) or not('square' in utils.argv.constrained_overlap_geometry): ###TODO: ok to set globally?
	if (overlap_shape is None) or ('any' in overlap_shape): ###TODO: ok to set globally?
	#if (utils.argv.constrained_overlap_geometry is None) or ('any' in utils.argv.constrained_overlap_geometry): ###TODO: ok to set globally?
		overlap_shape = random.choice(['square','strip'])
		#print "HERE!!!"
		#utils.argv.constrained_overlap_geometry = random.choice(['square','strip'])
		#any_shape = True
		#overlape_shape = random.choice(['square','strip'])
		utils.info(1,"shape parameter not specified, randomly chose shape parameter = "+str(utils.argv.constrained_overlap_geometry))
	#overlape_shape = utils.argv.constrained_overlap_geometry
	#tmp_layout = copy.copy(layout)
	tmp_layout = Layout(layout.get_chip(), layout.get_chip_positions(), layout.get_medium(), layout.get_overlap(), layout.get_inductor_properties())
	random_chip = utils.pick_random_element(range(0, tmp_layout.get_num_chips()))
	#random_chip = 1
	result = tmp_layout.get_random_feasible_neighbor_position(random_chip)
	#print 'overlap shape is ', overlap_shape
	if result == None:
		#utils.argv.constrained_overlap_geometry = 'any'
		utils.info(1, "Could not find a place to add the first cradle chip")
		return None
		#continue
	try:
		tmp_layout.add_new_chip(result)
		#print "add cradle 1"
	except:
		return None
		#print 'PROBLEM chip 1'

	if 'strip' in overlap_shape:
		if result[0]<2:
			utils.info(1, "chip 2 of cradle will be below level 1")
			#utils.argv.constrained_overlap_geometry = 'any'
			return None
				#continue
		if tmp_layout.get_diameter() + 2 > utils.argv.diameter:
			utils.info(1,"Adding cradle exceeds diameter constraint")
			#utils.argv.constrained_overlap_geometry = 'any'
			return None
			#continue #adding a cradle will exceed diameter constraint
		cradle_chip1 = tmp_layout.get_chip_positions()[-1]
		cradle_chip2 = tmp_layout.get_random_feasible_neighbor_position(len(tmp_layout.get_chip_positions())-1)
		if cradle_chip2 is None:
			print "This is a problem, strip"
			return None
		cradle_chip2[0] = cradle_chip1[0]-1
		if cradle_chip1[1] == cradle_chip2[1]: # add vertically
			if cradle_chip1[2] < cradle_chip2[2]: #add above
				chip3_level = cradle_chip1[0]
				chip3_x = cradle_chip2[1]
				chip3_y = cradle_chip2[2]+(1-overlap)*chipy_dim
			else: # add below
				chip3_level = cradle_chip1[0]
				chip3_x = cradle_chip2[1]
				chip3_y = cradle_chip2[2]-(1-overlap)*chipy_dim
		else: # add horizontally
			if cradle_chip1[1] < cradle_chip2[1]: #add right
				chip3_level = cradle_chip1[0]
				chip3_x = cradle_chip2[1]+(1-overlap)*chipx_dim
				chip3_y = cradle_chip2[2]
			else: # add left
				chip3_level = cradle_chip1[0]
				chip3_x = cradle_chip2[1]-(1-overlap)*chipx_dim
				chip3_y = cradle_chip2[2]

		cradle_chip3 = [chip3_level, chip3_x, chip3_y]
		#print "STRIP"
		second_cradle_chip = cradle_chip2
		third_cradle_chip = cradle_chip3
		#candidate_list = tmp_layout.get_chip_positions()[-3:]

	elif 'square' in overlap_shape:
		#print "\n\n\n\nNO\n\n\n\n\n"
		attached_at = utils.pick_random_element([1,2])
		if tmp_layout.get_diameter() + 2 > utils.argv.diameter:
			if tmp_layout.get_diameter() + 1 > utils.argv.diameter:
				utils.info(1, "Adding cradle by the middle chip still exceeds diameter constraint")
				#utils.argv.constrained_overlap_geometry = 'any'
				return None
				#continu1
			attached_at = 2
		inductor = tmp_layout.get_inductor_properties()[-1]
		if attached_at == 2: #adding at middle of cradle, cradle chip 2
			if tmp_layout.get_num_levels() + 1 > utils.argv.num_levels:
				utils.info(1,"Adding cradle by middle exceeds level constraint")
				#utils.argv.constrained_overlap_geometry = 'any'
				return None
				#continue
			cradle_chip2 = tmp_layout.get_chip_positions()[-1]
			#print 'num chips in layout is ', len(tmp_layout.get_chip_positions())
			chip1_level = chip3_level = cradle_chip2[0]+1
			if (cradle_chip2[1]==inductor[1] and cradle_chip2[2]==inductor[2]) or (cradle_chip2[1]!=inductor[1] and cradle_chip2[2]!=inductor[2]): #add top left, bottom right
				chip1_x = cradle_chip2[1]-chipx_dim*(1-sqrt(overlap))
				chip1_y = cradle_chip2[2]+chipy_dim*(1-sqrt(overlap))
				chip3_x = cradle_chip2[1]+chipx_dim*(1-sqrt(overlap))
				chip3_y = cradle_chip2[2]-chipy_dim*(1-sqrt(overlap))
			else: # add bottom left, top right
				chip1_x = cradle_chip2[1]+chipx_dim*(1-sqrt(overlap))
				chip1_y = cradle_chip2[2]+chipy_dim*(1-sqrt(overlap))
				chip3_x = cradle_chip2[1]-chipx_dim*(1-sqrt(overlap))
				chip3_y = cradle_chip2[2]-chipy_dim*(1-sqrt(overlap))
			cradle_chip1 = [chip1_level, chip1_x, chip1_y]
			cradle_chip3 = [chip3_level, chip3_x, chip3_y]
			#tmp_layout.add_new_chip(cradle_chip1)
			#tmp_layout.add_new_chip(cradle_chip3)
			#print "MIDDLE"
			second_cradle_chip = cradle_chip1
			third_cradle_chip = cradle_chip3

		else: #adding at side, cradle chip 1
			if tmp_layout.get_num_levels() < 2: ###TODO: check that this works
				utils.info(1,"Adding cradle by side will put cradle chip2 below level 1")
				#utils.argv.constrained_overlap_geometry = 'any'
				return None
				#continue
			cradle_chip1 = tmp_layout.get_chip_positions()[-1]
			cradle_chip2 = tmp_layout.get_random_feasible_neighbor_position(len(tmp_layout.get_chip_positions())-1)
			if cradle_chip2 is None:
				#print "This is a problem"
				return None
			cradle_chip2[0] = cradle_chip1[0]-1
			if cradle_chip2[1] < cradle_chip1[1]:
				#left
				if cradle_chip2[2] < cradle_chip1[2]:
					#bottom
					chip3_x = cradle_chip2[1] - chipx_dim*(1-sqrt(overlap))
					chip3_y = cradle_chip2[2] - chipy_dim*(1-sqrt(overlap))
				else:
					#top
					chip3_x = cradle_chip2[1] - chipx_dim*(1-sqrt(overlap))
					chip3_y = cradle_chip2[2] + chipy_dim*(1-sqrt(overlap))
			else:
				#right
				if cradle_chip2[2] < cradle_chip1[2]:
					#bottom
					chip3_x = cradle_chip2[1] + chipx_dim*(1-sqrt(overlap))
					chip3_y = cradle_chip2[2] - chipy_dim*(1-sqrt(overlap))
				else:
					#top
					chip3_x = cradle_chip2[1] + chipx_dim*(1-sqrt(overlap))
					chip3_y = cradle_chip2[2] + chipy_dim*(1-sqrt(overlap))
			cradle_chip3 = [cradle_chip1[0], chip3_x, chip3_y]
			#tmp_layout.add_new_chip(cradle_chip2)
			#tmp_layout.add_new_chip(cradle_chip3)
			second_cradle_chip = cradle_chip2
			third_cradle_chip = cradle_chip3
			#print "SIDE"
	#if (tmp_layout.can_new_chip_fit(third_cradle_chip)):
	#	print "third chip cant fit\nreturn"
	#	return
	if not tmp_layout.can_new_chip_fit(second_cradle_chip):
		#print 'cant add second chip'
		utils.info(0,"Second Chip Cant Fit")
		return None
	tmp_layout.add_new_chip(second_cradle_chip)
	if not tmp_layout.can_new_chip_fit(third_cradle_chip):
		#print 'cant add third chip'
		utils.info(0,"Third Chip Cant Fit")
		return None
	tmp_layout.add_new_chip(third_cradle_chip)

	if len(tmp_layout.get_chip_positions())%3!=0:
		#tmp_layout.draw_in_3D(None, True)
		utils.info(0,"Did not find all 3 cradle chip positions, returning None")
		return None
	candidate_list = tmp_layout.get_chip_positions()[-3:]

	return candidate_list

"""
	Add multiple candidates as specified by num_chips_to_add arg
	returns lists containing positions of the multiple chips to add
"""
def add_multi_chip(layout, max_num_neighbor_candidate_attempts, num_chips_to_add):
	utils.info(2,"Adding chips in multiples of "+str(num_chips_to_add))
	new_chips = 0
	add_attempts = 0
	tmp_layout = Layout(layout.get_chip(), layout.get_chip_positions(), layout.get_medium(), layout.get_overlap(), layout.get_inductor_properties())
	while new_chips<num_chips_to_add and add_attempts < max_num_neighbor_candidate_attempts:
		add_attempts += 1
		random_chip = utils.pick_random_element(range(0, tmp_layout.get_num_chips()))
		if (tmp_layout.get_longest_shortest_path_from_chip(random_chip) >= utils.argv.diameter):
			# utils.info(2, "Ooops, chip " + str(random_chip) + " won't work for the diameter");
			continue
		result = tmp_layout.get_random_feasible_neighbor_position(random_chip)
		#if result != None:
		#print 'random chip = ',random_chip,' positions len =',len(layout.get_chip_positions()) #TODO: look into and add cmd arg
		if result != None:
			if utils.argv.carbon and not tmp_layout.enforce_carbon_structure(tmp_layout.get_chip_positions()[random_chip], result):
				continue
			new_chips += 1
			try:
				tmp_layout.add_new_chip(result)
			except:
				continue

	if new_chips<num_chips_to_add:
		utils.abort("Could not find any more feasible neighbors after "+str(add_attempts)+" attempts")
	candidate_list = tmp_layout.get_chip_positions()[-num_chips_to_add:]
	return candidate_list

""" Function that returns a list of list of candidates """

#@jit
def generate_multi_candidates(layout, candidate_random_trials, num_neighbor_candidates, max_num_neighbor_candidate_attempts, num_chips_to_add, add_scheme):
	utils.info(3,"generating multi candidates")
	num_attempts = 0
	while ((len(candidate_random_trials) < num_neighbor_candidates) and (num_attempts < max_num_neighbor_candidate_attempts)):
		num_attempts += 1
		if (add_scheme is not None) and ('cradle' in add_scheme) and (utils.argv.num_chips%3 == 0):  ###TODO: if remaining chips to add not a multiple of 3 call add_multi_chip() instead of add_cradle()

			candidate_list = add_cradle(layout)

			if candidate_list is None:
				continue
			elif len(candidate_list)<3:
				continue
		else:
			candidate_list = add_multi_chip(layout, max_num_neighbor_candidate_attempts, num_chips_to_add)
			if candidate_list == None:
				continue
		#layout.draw_in_3D(None,True)
		#for candidtates in candidate_list:
			#print 'there are that many chips --> ',len(layout.get_chip_positions())
		#	if layout.get_chip_positions()[-1] == candidtates:
		#		print "\n\n\n\n\n\n\nWTF\n\n\n\n\n"
		candidate_random_trials.append(candidate_list)

	if len(candidate_random_trials) != num_neighbor_candidates:
			utils.info(0, "Ran out of trials\nOnly "+str(len(candidate_random_trials))+" of "+str(num_neighbor_candidates)+" were found")
	return candidate_random_trials

"""Original pick_candidate"""
"""
#@jit
def pick_candidates(results, candidate_random_trials):
	#print 'results is ', results
	#print 'candidate random trials is ', candidate_random_trials
	picked_candidate_temperature = -1
	picked_candidate_power = -1
	picked_candidate_ASPL = -1.0
	picked_candidate_num_edges = -1
	index_of_result = None

	picked_candidate = None
	for index in xrange(0, len(candidate_random_trials)):
		candidate = candidate_random_trials[index];
		result = results[index]
		#print 'candidate is ', candidate
		if (result != None):
			[tmp_layout, [power_distribution, temperature]] = result
			power = sum(power_distribution)
			ASPL = tmp_layout.get_ASPL()
			num_edges = tmp_layout.get_num_edges()
			utils.info(2, "    - power=" + str(power) + " temp=" + str(temperature) + " ASPL=" + str(ASPL) + " edges=" + str(num_edges))

			new_pick = False
			if (picked_candidate == None):
				utils.info(2, "    ** INITIAL PICK **")
				new_pick = True
			else:
				# this is where we implement candidate selection
				if (power > picked_candidate_power):
					utils.info(2, "    ** PICKED DUE TO BETTER POWER **")
					new_pick = True
				elif (power == picked_candidate_power):
					if (num_edges > picked_candidate_num_edges):
						utils.info(2, "    ** PICKED DUE TO BETTER EDGES **")
						new_pick = True
					elif (num_edges == picked_candidate_num_edges) and (ASPL < picked_candidate_ASPL):
						utils.info(2, "    ** PICKED DUE TO BETTER ASPL **")
						new_pick = True
					elif (num_edges == picked_candidate_num_edges) and (ASPL == picked_candidate_ASPL) and (temperature < picked_candidate_temperature):
						utils.info(2, "    ** PICKED DUE TO BETTER TEMPERATURE **")
						new_pick = True

			if new_pick:
				picked_candidate = candidate
				picked_candidate_power = power
				picked_candidate_temperature = temperature
				picked_candidate_ASPL = ASPL
				picked_candidate_num_edges = num_edges
				index_of_result = index

	return [picked_candidate, index_of_result]
"""

""" pick_candidates"""

#@jit
def pick_candidates(results, candidate_random_trials):
	picked_candidate_temperature = -1
	picked_candidate_power = -1
	picked_candidate_ASPL = -1.0
	picked_candidate_num_edges = -1
	picked_candidate_diameter = -1
	index_of_result = None
	temp_limit = utils.argv.max_allowed_temperature
	alpha_threshold = utils.argv.alpha_temp
	picked_by = utils.argv.pick_criteria
	picked_candidate = None
	for index in xrange(0, len(candidate_random_trials)):
		candidate = candidate_random_trials[index];
		result = results[index]
		#print 'candidate is ', candidate
		#print 'result is ', result
		if not(None in result) or (None in results):
			[tmp_layout, [power_distribution, temperature]] = result
			power = sum(power_distribution)
			ASPL = tmp_layout.get_ASPL()
			num_edges = tmp_layout.get_num_edges()
			diameter = tmp_layout.get_diameter()
			utils.info(2, "    - power=" + str(power) + " temp=" + str(temperature) + " ASPL=" + str(ASPL) + " edges=" + str(num_edges))

			new_pick = False
			if (picked_candidate == None):
				utils.info(2, "    ** INITIAL PICK **")
				new_pick = True
			else:
				if utils.argv.pick_criteria is not None:
					if alpha_threshold is not None:
						if (picked_candidate_temperature < temp_limit*alpha_threshold) and (temperature<temp_limit*alpha_threshold):
							utils.info(2, "    ** PICKED DUE TO BETTER TEMPURATURE **")
							if diameter<picked_candidate_diameter:
								utils.info(2, "    ** PICKED DUE TO BETTER DIAMETER **")
								new_pick = True
							elif (diameter == picked_candidate_diameter) and (ASPL < picked_candidate_ASPL):
								utils.info(2, "    ** PICKED DUE TO BETTER ASPL **")
								new_pick = True
						elif 'power' in picked_by:
							#utils.abort("pick on power")
							if (power > picked_candidate_power):
								utils.info(2, "    ** PICKED DUE TO BETTER POWER **")
								new_pick = True
							elif (picked_candidate_power == power) and (temperature < picked_candidate_temperature):
								utils.info(2, "    ** PICKED DUE TO BETTER Tempurature **")
								new_picked = True
						elif 'temp' in picked_by:
							#utils.abort("pick on temp")
							if (temperature < picked_candidate_temperature):
								utils.info(2, "    ** PICKED DUE TO BETTER TEMPURATURE **")
								new_pick = True
							elif (picked_candidate_temperature == temperature) and (power > picked_candidate_power):
								utils.info(2, "    ** PICKED DUE TO BETTER Tempurature **")
								new_picked = True
					else:
						if 'network' in picked_by:

							if diameter<picked_candidate_diameter:
								utils.info(2, "    ** PICKED DUE TO BETTER DIAMETER **")
								new_pick = True
							elif (diameter == picked_candidate_diameter) and (ASPL < picked_candidate_ASPL):
								utils.info(2, "    ** PICKED DUE TO BETTER ASPL **")
								new_pick = True
							elif (diameter == picked_candidate_diameter) and (ASPL == picked_candidate_ASPL) and  (num_edges > picked_candidate_num_edges):
								utils.info(2, "    ** PICKED DUE TO BETTER EDGES **")
								new_pick = True
							elif (power > picked_candidate_power):
								utils.info(2, "    ** PICKED DUE TO BETTER POWER **")
								new_pick = True
							elif (temperature < picked_candidate_temperature):
								utils.info(2, "    ** PICKED DUE TO BETTER TEMPURATURE **")
								new_pick = True
							"""
							if (num_edges > picked_candidate_num_edges):
								utils.info(2, "    ** PICKED DUE TO BETTER EDGES **")
								new_pick = True
							elif (diameter < picked_candidate_diameter) and (num_edges > picked_candidate_num_edges):
								utils.info(2, "    ** PICKED DUE TO BETTER DIAMETER **")
								new_pick = True
							elif (diameter == picked_candidate_diameter) and (ASPL < picked_candidate_ASPL):
								utils.info(2, "    ** PICKED DUE TO BETTER ASPL **")
								new_pick = True
							elif (diameter == picked_candidate_diameter) and (ASPL == picked_candidate_ASPL) and  (num_edges > picked_candidate_num_edges):
								utils.info(2, "    ** PICKED DUE TO BETTER EDGES **")
								new_pick = True
							elif (power > picked_candidate_power):
								utils.info(2, "    ** PICKED DUE TO BETTER POWER **")
								new_pick = True
							elif (temperature < picked_candidate_temperature):
								utils.info(2, "    ** PICKED DUE TO BETTER TEMPURATURE **")
								new_pick = True
							"""

						elif 'power' in picked_by:
							#utils.abort("pick on power")
							if (power > picked_candidate_power):
								utils.info(2, "    ** PICKED DUE TO BETTER POWER **")
								new_pick = True
							elif (picked_candidate_power == power) and diameter<picked_candidate_diameter:
								utils.info(2, "    ** PICKED DUE TO BETTER DIAMETER **")
								new_pick = True
							elif (diameter == picked_candidate_diameter) and (ASPL < picked_candidate_ASPL):
								utils.info(2, "    ** PICKED DUE TO BETTER ASPL **")
								new_pick = True
							elif (diameter == picked_candidate_diameter) and (ASPL == picked_candidate_ASPL) and  (num_edges > picked_candidate_num_edges):
								utils.info(2, "    ** PICKED DUE TO BETTER EDGES **")
								new_pick = True
							elif (picked_candidate_power == power) and (temperature < picked_candidate_temperature):
								utils.info(2, "    ** PICKED DUE TO BETTER Tempurature **")
								new_picked = True
						elif 'temp' in picked_by:
							#utils.abort("pick on temp")
							if (temperature < picked_candidate_temperature):
								utils.info(2, "    ** PICKED DUE TO BETTER TEMPURATURE **")
								new_pick = True
							elif (picked_candidate_temperature == temperature) and diameter<picked_candidate_diameter:
								utils.info(2, "    ** PICKED DUE TO BETTER DIAMETER **")
								new_pick = True
							elif (diameter == picked_candidate_diameter) and (ASPL < picked_candidate_ASPL):
								utils.info(2, "    ** PICKED DUE TO BETTER ASPL **")
								new_pick = True
							elif (diameter == picked_candidate_diameter) and (ASPL == picked_candidate_ASPL) and  (num_edges > picked_candidate_num_edges):
								utils.info(2, "    ** PICKED DUE TO BETTER EDGES **")
								new_pick = True
							elif (picked_candidate_temperature == temperature) and (power > picked_candidate_power):
								utils.info(2, "    ** PICKED DUE TO BETTER Tempurature **")
								new_picked = True

				else:
					if (power > picked_candidate_power):
						utils.info(2, "    ** PICKED DUE TO BETTER POWER **")
						new_pick = True
					elif (power == picked_candidate_power):
						if (num_edges > picked_candidate_num_edges):
							utils.info(2, "    ** PICKED DUE TO BETTER EDGES **")
							new_pick = True
						elif (num_edges == picked_candidate_num_edges) and (ASPL < picked_candidate_ASPL):
							utils.info(2, "    ** PICKED DUE TO BETTER ASPL **")
							new_pick = True
						elif (num_edges == picked_candidate_num_edges) and (ASPL == picked_candidate_ASPL) and (temperature < picked_candidate_temperature):
							utils.info(2, "    ** PICKED DUE TO BETTER TEMPERATURE **")
							new_pick = True

			if new_pick:
				picked_candidate = candidate
				picked_candidate_power = power
				picked_candidate_temperature = temperature
				picked_candidate_ASPL = ASPL
				picked_candidate_num_edges = num_edges
				picked_candidate_diameter = diameter
				index_of_result = index

	return [picked_candidate, index_of_result]

"""Random greedy layout optimization"""


def optimize_layout_random_greedy():
	layout = LayoutBuilder.compute_cradle_layout(3)

	num_neighbor_candidates = 10  # Default value
	max_num_neighbor_candidate_attempts = 1000  # default value
	num_chips_to_add = 1 # Default value
	add_scheme = None
	#print utils.argv.layout_scheme
	if (len(utils.argv.layout_scheme.split(":")) == 2):
		num_neighbor_candidates = int(utils.argv.layout_scheme.split(":")[1])

	if (len(utils.argv.layout_scheme.split(":")) == 3):
		num_neighbor_candidates = int(utils.argv.layout_scheme.split(":")[1])
		max_num_neighbor_candidate_attempts = int(utils.argv.layout_scheme.split(":")[2])
	"""
	if (len(utils.argv.layout_scheme.split(":")) == 4):
		num_neighbor_candidates = int(utils.argv.layout_scheme.split(":")[1])
		max_num_neighbor_candidate_attempts = int(utils.argv.layout_scheme.split(":")[2])
		num_chips_to_add  = int(utils.argv.layout_scheme.split(":")[3])
	"""
	if (len(utils.argv.layout_scheme.split(":")) == 4):
		num_neighbor_candidates = int(utils.argv.layout_scheme.split(":")[1])
		max_num_neighbor_candidate_attempts = int(utils.argv.layout_scheme.split(":")[2])
		try:
			num_chips_to_add = int(utils.argv.layout_scheme.split(":")[3])
			add_scheme = "multi"
		except:
			add_scheme = utils.argv.layout_scheme.split(":")[3]
			num_chips_to_add = 3

	results = []
	picked_index = 0
	if layout.get_num_chips() == utils.argv.num_chips:
		result = find_maximum_power_budget(layout)
		if result == None:
			return None
		[power_distribution, temperature] = result

		return [layout, power_distribution, temperature]

	while (layout.get_num_chips() != utils.argv.num_chips):

		###############################################
		### Create Candidates
		###############################################

		utils.info(2, "* Generating " + str(num_neighbor_candidates) + " candidate positions for chip #" + str(1 + layout.get_num_chips()) + " in the layout")
		if num_chips_to_add > utils.argv.num_chips - layout.get_num_chips(): #preprocessing
			num_chips_to_add = utils.argv.num_chips - layout.get_num_chips()
			utils.info(2, "Warning num_chips_to_add too great\nCandidates will be generated in "+str(num_chips_to_add)+"'s")
		candidate_random_trials = generate_multi_candidates(layout, [], num_neighbor_candidates, max_num_neighbor_candidate_attempts,num_chips_to_add,add_scheme)
		utils.info(3,"\n\nCandidates picked\n\n")
		list_of_args = []
		for index in xrange(0, len(candidate_random_trials)):
			#print 'layout to evaluate ',layout
			list_of_args.append([layout, candidate_random_trials[index]])
		results = map(evaluate_candidate, list_of_args)

		#print "RESULTS = ", results

		###############################################
		### Pick the best candidate
		################################################

		picked_candidate, picked_index = pick_candidates(results, candidate_random_trials)
		#utils.abort("candidate random trial is \n"+str(candidate_random_trials))

		# Add the candidate
		if picked_candidate == None:
			utils.abort("Could not find a candidate that met the temperature constraint")

		utils.info(1, "Picked candidate: " + str(picked_candidate))
		for chip in picked_candidate: ###TODO: should we just make a deep copy form results[picked_index][0]???
			try:
				layout.add_new_chip(chip)
			except:
				print 'ADD error'
	#print "---> ", layout.get_num_chips(), utils.argv.num_chips

	# Do the final evaluation (which was already be done, but whatever)
	# result = find_maximum_power_budget(layout)
	#print 'picked index is ',picked_index,' results len is ',results
	result = results[picked_index]
	#print 'resuts are ', result
	# print "RESULTS: ", result

	if (result == None):
		return None

	[power_distribution, temperature] = result[-1]

	return [layout, power_distribution, temperature]


"""stop workers"""


def send_stop_signals(worker_list, comm):
	utils.info(2, "Sending stop signal to all workers")
	#comm.bcast([0, 0, 0, 0, 1], root=0)
	#print "stop bcast"

	for k in range(0, len(worker_list)):
		stop_worker = [0, 0, 0, 0, 1]
		utils.info(2, "Sending stop signal to worker rank " + str(k))
		comm.send(stop_worker, dest=k + 1)


"""Random greedy layout optimization with MPI"""


def optimize_layout_random_greedy_mpi():
	##########################################
	###TODO: add check for --mpi flag
	###TODO: maybe run exp overlap vs ex time
	##########################################

	comm = MPI.COMM_WORLD
	rank = comm.Get_rank()
	size = comm.Get_size()
	if size<2:
		comm.bcast([0, 0, 0, 0, 1],root=0)
		utils.abort("Need to invoke with 'mpirun-np #' where # is int processes greater than 1")
	if rank == 0:
		layout = LayoutBuilder.compute_cradle_layout(3)

		num_neighbor_candidates = 20  # Default value
		max_num_neighbor_candidate_attempts = 1000  # default value
		num_chips_to_add = 1 # Default value
		add_scheme = ''


		if (len(utils.argv.layout_scheme.split(":")) == 2):
			num_neighbor_candidates = int(utils.argv.layout_scheme.split(":")[1]);

		if (len(utils.argv.layout_scheme.split(":")) == 3):
			num_neighbor_candidates = int(utils.argv.layout_scheme.split(":")[1]);
			max_num_neighbor_candidate_attempts = int(utils.argv.layout_scheme.split(":")[2]);

		if (len(utils.argv.layout_scheme.split(":")) == 4):
			num_neighbor_candidates = int(utils.argv.layout_scheme.split(":")[1])
			max_num_neighbor_candidate_attempts = int(utils.argv.layout_scheme.split(":")[2])
			try:
				num_chips_to_add = int(utils.argv.layout_scheme.split(":")[3])
				add_scheme = "multi"
			except:
				add_scheme = utils.argv.layout_scheme.split(":")[3]
				num_chips_to_add = 3
				#utils.abort("add scheme is "+str(add_scheme))

		results = []
		picked_index = 0
		while (layout.get_num_chips() != utils.argv.num_chips):

			###############################################
			### Create Candidates
			##########################################

			#candidate_random_trials = []
			#candidate_random_trials = generate_candidates(layout, candidate_random_trials, num_neighbor_candidates,
			utils.info(2, "* Generating " + str(num_neighbor_candidates) + " candidate positions for chip #" + str(1 + layout.get_num_chips()) + " in the layout")
			if num_chips_to_add > utils.argv.num_chips - layout.get_num_chips(): #preprocessing
				num_chips_to_add = utils.argv.num_chips - layout.get_num_chips()
				utils.info(2, "Warning num_chips_to_add too great\nCandidates will be generated in "+str(num_chips_to_add)+"'s")
			candidate_random_trials = generate_multi_candidates(layout, [], num_neighbor_candidates, max_num_neighbor_candidate_attempts,num_chips_to_add,add_scheme)

			###############################################
			### Evaluate all Candidates
			###############################################

			###############################################
			### TODO
			### - implement add cradles
			###		- find feasible cradle function, in layout
			### - look into merging this function with sequential version
			###############################################

			worker_list = [False] * (size - 1)
			results = [None] * len(candidate_random_trials)
			end = 0
			i = 0
			while None in results:
				if False in worker_list and end < 1:
					if i < len(candidate_random_trials):
						worker = worker_list.index(False)
						worker_list[worker] = True
						data_to_worker = [layout, candidate_random_trials[i], i, worker, end]
						# data_to_worker[layout, candidate, index in results list, index in worker list, worker stop variable]
						# print 'SENT layout is ', layout
						comm.send(data_to_worker, dest=worker + 1)
						i += 1
					else:
						end = 1  # when no more candidates and workers arent working, and alive
				else:
					data_from_worker = comm.recv(source=MPI.ANY_SOURCE)
					# data_from_worker[[[power_distribution, temperature]], index in results list, index in worker list]
					results[data_from_worker[1]] = data_from_worker[0]
					worker_list[data_from_worker[2]] = False

			# print "RESULTS = ", results

			# picked_candidate = pick_candidates(layout, results,candidate_random_trials)
			picked_candidate, picked_index = pick_candidates(results, candidate_random_trials)

			if picked_candidate == None:
				send_stop_signals(worker_list, comm)
				utils.abort("Could not find a candidate that met the temperature constraint")

			utils.info(1, "Picked candidate: " + str(picked_candidate))
			for chip in picked_candidate: ###TODO: should we just make a deep copy form results[picked_index][0]???
				#print "ADDING HERE "
				try:
					layout.add_new_chip(chip)
				except:
					send_stop_signals(worker_list, comm)
					utils.abort("Final add doesnt work")

		# Do the final evaluation (which was already be done, but whatever)
		# result = find_maximum_power_budget(layout)
		# saved_result = results[picked_index]
		# print '\n\result is ',result,'\nsaved_result is ',saved_result

		if not results:
			return None
		result = results[picked_index]
		if (result == None):
			return None

		[power_distribution, temperature] = result[-1]
		# print 'Random greedy layout optimization returning ',[layout, power_distribution, temperature]

		# send stop signal to all worker ranks
		send_stop_signals(worker_list, comm)
		# for k in range(0, len(worker_list)):
		#	stop_worker = [0, 0, 0, 0, 1]
		# comm.send(stop_worker,dest = k+1)
		#comm.Disconnect()

		return [layout, power_distribution, temperature]

	else:
		while True:
			data_from_master = comm.recv(source=0)
			# data_from_master[layout, candidate,index of restult, index of worker,stop worker variable]
			if data_from_master[4] > 0:
				#print '\n\n!!!!!!worker rank ', rank,' exiting layout is ', data_from_master[0]

				#comm.Disconnect()
				sys.exit(0)
			# print '>>>>>>>>EXIT val is',data_from_master[4], ' for rank ', rank
			# layout = data_from_master[0]
			# candidate = data_from_master[1]
			# result_index = data_from_master[2]
			# worker_index = data_from_master[3]

			powerdisNtemp = evaluate_candidate(data_from_master[:2])

			# data_to_master = [powerdisNtemp,result_index,worker_index]
			data_to_master = [powerdisNtemp, data_from_master[2], data_from_master[3]]
			# data_to_master[[power_distribution, temperature], candidate,index of restult, index of worker,stop worker variable]
			comm.send(data_to_master, dest=0)


"""Checkboard layout optimization"""


def optimize_layout_checkerboard():
	if (utils.argv.verbose == 0):
		sys.stderr.write("o")
	utils.info(1, "Constructing a checkerboard layout")

	layout = LayoutBuilder.compute_checkerboard_layout(utils.argv.num_chips)

	utils.info(1, "Finding the maximum Power Budget")
	result = find_maximum_power_budget(layout)

	if result == None:
		return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]

"""Carbon layout optimization"""


#def optimize_layout_carbon():

"""
	build first carbon
	until numlevel == diameter+1
		add to each level
	utils.info(1, "Constructing a carbon layout")

	layout = LayoutBuilder.compute_carbon_init_layout()

	num_chips = utils.argv.num_chips
	attempts = 1000
	new_chip = None
	for chip in range(1,num_chips):
		attempt = 1
		while attempt < attempts:
			attempt += 1
			tmp_chip = layout.get_random_feasible_neighbor_position(0)
			if tmp_chip is None:
				continue
			if layout.enforce_carbon_structure(layout.get_chip_positions()[0],tmp_chip):
				attempt = 1000
				new_chip = tmp_chip

		if new_chip is None:
			continue
		layout.add_new_chip(new_chip)
	#num_chips = num_chips - 1



	#utils.abort("\nUNDER CONSTRUCTION")
	utils.info(1, "Finding the maximum Power Budget")
	result = find_maximum_power_budget(layout)

	if result == None:
		return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]
"""

"""Cradle layout optimization"""


def optimize_layout_cradle():
	if (utils.argv.verbose == 0):
		sys.stderr.write("o")
	utils.info(1, "Constructing a cradle layout")

	layout = LayoutBuilder.compute_cradle_layout(utils.argv.num_chips)

	utils.info(1, "Finding the maximum Power Budget")
	result = find_maximum_power_budget(layout)

	if result == None:
		return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]

"""Double Helix layout optimization"""


def optimize_layout_double_helix():
	if (utils.argv.verbose == 0):
		sys.stderr.write("o")
	utils.info(1, "Constructing a double helix layout")

	layout = LayoutBuilder.compute_double_helix(utils.argv.num_chips)

	utils.info(1, "Finding the maximum Power Budget")
	result = find_maximum_power_budget(layout)

	if result == None:
		return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]


"""bridge layout optimization"""


def optimize_layout_bridge():
	if (utils.argv.verbose == 0):
		sys.stderr.write("o")
	utils.info(1, "Constructing a bridge layout")

	layout = LayoutBuilder.compute_bridge_layout(utils.argv.num_chips)

	utils.info(1, "Finding the maximum Power Budget")
	result = find_maximum_power_budget(layout)

	if result == None:
		return None

	[power_distribution, temperature] = result

	return [layout, power_distribution, temperature]
