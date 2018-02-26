#!/usr/bin/python

import sys
import random
from mpi4py import MPI

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
	elif (layout_scheme == "checkerboard"):
		solution = optimize_layout_checkerboard()
	elif (layout_scheme == "craddle"):
		solution = optimize_layout_craddle()
	elif (layout_scheme == "bridge"):
		solution = optimize_layout_bridge()
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
	layout = Layout(utils.argv.chip, [[1, 0.0, 0.0]], utils.argv.medium, utils.argv.overlap)

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
	dummy_layout = Layout(layout.get_chip(), layout.get_chip_positions(), layout.get_medium(), layout.get_overlap(), layout.get_inductor_properties())
	for chip in candidate:
		#print "HERE"
		dummy_layout.add_new_chip(chip)
	if (dummy_layout.get_diameter() > utils.argv.diameter):
		utils.abort("Layout diameter is too big (this should never happen here!)")

	return [dummy_layout, find_maximum_power_budget(dummy_layout)]


""" Function that returns a list of chip candidates"""

#@jit
def generate_candidates(layout, candidate_random_trials, num_neighbor_candidates, max_num_neighbor_candidate_attempts):
	utils.info(1, "* Generating " + str(num_neighbor_candidates) + " candidate positions for chip #" + str(
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

""" Function that returns a list of list of candidates """

#@jit
def generate_multi_candidates(layout, candidate_random_trials, num_neighbor_candidates, max_num_neighbor_candidate_attempts, num_chips_to_add, add_scheme):

	if 'craddle' in add_scheme:
		num_attempts = 0
		overlap = utils.argv.overlap
		chipx_dim = utils.argv.chip.x_dimension
		chipy_dim = utils.argv.chip.y_dimension
		overlape_shape = utils.argv.constrained_overlap_geometry
		if (overlape_shape is None) or ('any' in overlape_shape):
			utils.argv.constrained_overlap_geometry = overlape_shape = random.choice(['square','strip'])
			utils.info(3,"shape parameter not specified, randomly chose shape parameter = "+str(overlape_shape))
		while ((len(candidate_random_trials) < num_neighbor_candidates) and (num_attempts < max_num_neighbor_candidate_attempts)):
			num_attempts += 1
			add_attempts = 0
			#print 'overlap shape ',overlape_shape
			"""
			check geometry
			if geometry is any, randomly pick if added craddle is going to be be straight, or diagonal
			check level - level and (level - 1)
			if straight, check diameter + 3(from added craddle) is allowed
			randomly pick if craddle going to be added from middle or side
			check diameter if craddle can be added form side or middle
			get first craddle chip
			get new_inductor property
			
			for middle
			if (Cx==Ix and Cy==Iy) or (Cx!=Ix and Cy!=Iy):
				add top left, bottom right
			else:
				add bottom left, top right
				
			for side square
			connect first side chip
			then find random feasible neighbor for first side chip and then add craddle from there
			"""

			tmp_layout = Layout(layout.get_chip(), layout.get_chip_positions(), layout.get_medium(), layout.get_overlap(), layout.get_inductor_properties())

			random_chip = utils.pick_random_element(range(0, tmp_layout.get_num_chips()))
			#random_chip = 2
			#overlap = utils.argv.overlap
			#chipx_dim = utils.argv.chip.x_dimension
			#chipy_dim = utils.argv.chip.y_dimension
			#overlape_shape = utils.argv.constrained_overlap_geometry

			#print 'random chip is ', random_chip
			#print 'len candidate random trial ',len(candidate_random_trials)
			#if random_chip == 0:
			#	print "!!!!!!!!!!!!!!!!!!"

			#if (overlape_shape is None) or ('any' in overlape_shape):
			#	overlape_shape = random.choice(['square','strip'])

			result = tmp_layout.get_random_feasible_neighbor_position(random_chip)
			if result == None:
				#print "HERE"
				continue
			# if constrained geometry is strip, can only add craddle by ends
			#di = tmp_layout.get_diameter()
			#print 'diameter is ', di
			tmp_layout.add_new_chip(result)
			#di = tmp_layout.get_diameter()
			#print 'diameter is NOW ', di
			#print 'added 1st'

			if 'strip' in overlape_shape:
				#print "Attempting to add craddles in strip configuration"
				if result[0]<2:
					utils.info(1, "chip 2 of craddle will be below level 1")
					continue
				if tmp_layout.get_diameter() + 2 > utils.argv.diameter:
					utils.info(3,"Adding craddle exceeds diameter constraint")
					continue #adding a craddle will exceed diameter constraint
				craddle_chip1 = tmp_layout.get_chip_positions()[-1]
				#print 'craddle chip 1 is ', craddle_chip1
				craddle_chip2 = tmp_layout.get_random_feasible_neighbor_position(len(tmp_layout.get_chip_positions())-1)
				craddle_chip2[0] = craddle_chip1[0]-1
				#print 'chip 1 is ', craddle_chip1,'\nchip 2 is ', craddle_chip2
				if craddle_chip1[1] == craddle_chip2[1]: # add vertically
					if craddle_chip1[2] < craddle_chip2[2]: #add above
						chip3_level = craddle_chip1[0]
						chip3_x = craddle_chip2[1]
						chip3_y = craddle_chip2[2]+(1-overlap)*chipy_dim
					else: # add below
						chip3_level = craddle_chip1[0]
						chip3_x = craddle_chip2[1]
						chip3_y = craddle_chip2[2]-(1-overlap)*chipy_dim
				else: # add horizontally
					if craddle_chip1[1] < craddle_chip2[1]: #add right
						#print "ADD right"
						chip3_level = craddle_chip1[0]
						chip3_x = craddle_chip2[1]+(1-overlap)*chipx_dim
						chip3_y = craddle_chip2[2]
					else: # add left
						#print "ADD LEFT"
						chip3_level = craddle_chip1[0]
						chip3_x = craddle_chip2[1]-(1-overlap)*chipx_dim
						chip3_y = craddle_chip2[2]

				craddle_chip3 = [chip3_level, chip3_x, chip3_y]

				#print 'chip 1 is ', craddle_chip1,'\nchip 2 is ', craddle_chip2,'\nchip 3 is ', craddle_chip3,'\n'
				tmp_layout.add_new_chip(craddle_chip2)
				#print 'added 2nd'
				tmp_layout.add_new_chip(craddle_chip3)
				#print 'added 3rd'
				candidate_list = tmp_layout.get_chip_positions()[-3:]
				#candidate_random_trials.append(candidate_list)

			elif 'square' in overlape_shape:
				#print "Attempting to add craddles in square configuration"
				attached_at = utils.pick_random_element([1,2])
				#attached_at = 1
				if tmp_layout.get_diameter() + 2 > utils.argv.diameter:
					if tmp_layout.get_diameter() + 1 > utils.argv.diameter:
						utils.info(0, "Adding craddle by the middle chip still exceeds diameter constraint")
						continue
					attached_at = 2
				#print 'ATTACHED AT CHIP ',attached_at
				inductor = tmp_layout.get_inductor_properties()[-1]
				if attached_at == 2: #adding at middle of craddle, craddle chip 2
					if tmp_layout.get_num_levels() + 1 > utils.argv.num_levels:
						utils.info(0,"Adding craddle by middle exceeds level constraint")
						continue
					craddle_chip2 = tmp_layout.get_chip_positions()[-1]
					chip1_level = chip3_level = craddle_chip2[0]+1
					#print'chip x ',craddle_chip2[1],'\nindu x',inductor[1],'\nchip y ',craddle_chip2[2],'\nindu y',inductor[2],'\nchip1 l ', chip1_level,'\nchip3 l ',chip3_level
					#tmp_layout.draw_in_3D(None, True)
					if (craddle_chip2[1]==inductor[1] and craddle_chip2[2]==inductor[2]) or (craddle_chip2[1]!=inductor[1] and craddle_chip2[2]!=inductor[2]): #add top left, bottom right
						chip1_x = craddle_chip2[1]-chipx_dim*(1-sqrt(overlap))
						chip1_y = craddle_chip2[2]+chipy_dim*(1-sqrt(overlap))
						chip3_x = craddle_chip2[1]+chipx_dim*(1-sqrt(overlap))
						chip3_y = craddle_chip2[2]-chipy_dim*(1-sqrt(overlap))
						#print "top left, bottom right"
					else: # add bottom left, top right
						chip1_x = craddle_chip2[1]+chipx_dim*(1-sqrt(overlap))
						chip1_y = craddle_chip2[2]+chipy_dim*(1-sqrt(overlap))
						chip3_x = craddle_chip2[1]-chipx_dim*(1-sqrt(overlap))
						chip3_y = craddle_chip2[2]-chipy_dim*(1-sqrt(overlap))
						#print "bottom left, top right"
					craddle_chip1 = [chip1_level, chip1_x, chip1_y]
					craddle_chip3 = [chip3_level, chip3_x, chip3_y]
					tmp_layout.add_new_chip(craddle_chip1)
					#print 'add chip 1 ', craddle_chip1
					tmp_layout.add_new_chip(craddle_chip3)
					#print 'add chip 2 ', craddle_chip3
					#print "ADDED by Middle"

				else: #adding at side, craddle chip 1
					if tmp_layout.get_num_levels() < 2:
						utils.info(0,"Adding craddle by side will put craddle chip2 below level 1")
						continue
					#print "Add by side"
					craddle_chip1 = tmp_layout.get_chip_positions()[-1]
					#print 'craddle chip 1 is ', craddle_chip1
					craddle_chip2 = tmp_layout.get_random_feasible_neighbor_position(len(tmp_layout.get_chip_positions())-1)
					craddle_chip2[0] = craddle_chip1[0]-1
					#craddle_chip2 = tmp_layout.get_random_feasible_neighbor_position()
					if craddle_chip2[1] < craddle_chip1[1]:
						#left
						if craddle_chip2[2] < craddle_chip1[2]:
							#bottom
							chip3_x = craddle_chip2[1] - chipx_dim*(1-sqrt(overlap))
							chip3_y = craddle_chip2[2] - chipy_dim*(1-sqrt(overlap))
						else:
							#top
							chip3_x = craddle_chip2[1] - chipx_dim*(1-sqrt(overlap))
							chip3_y = craddle_chip2[2] + chipy_dim*(1-sqrt(overlap))
					else:
						#right
						if craddle_chip2[2] < craddle_chip1[2]:
							#bottom
							chip3_x = craddle_chip2[1] + chipx_dim*(1-sqrt(overlap))
							chip3_y = craddle_chip2[2] - chipy_dim*(1-sqrt(overlap))
						else:
							#top
							chip3_x = craddle_chip2[1] + chipx_dim*(1-sqrt(overlap))
							chip3_y = craddle_chip2[2] + chipy_dim*(1-sqrt(overlap))
					craddle_chip3 = [craddle_chip1[0], chip3_x, chip3_y]
					tmp_layout.add_new_chip(craddle_chip2)
					#print 'added 2nd'
					tmp_layout.add_new_chip(craddle_chip3)
					#print "Added by side"
					#tmp_layout.draw_in_3D(None, True)
					#utils.abort("implementing adding in craddles")

				#tmp_layout.draw_in_3D(None, True)
				#print "SQUARE"
				#if adding to middle
					#if result[0]
				#tmp_layout.draw_in_3D(None, True)
				candidate_list = tmp_layout.get_chip_positions()[-num_chips_to_add:]
			#utils.info(1, str(num_chips_to_add) + " Candidate random chips are " + str(candidate_list))
			candidate_random_trials.append(candidate_list)
		if len(candidate_random_trials) != num_neighbor_candidates:
			utils.abort("Only "+str(len(candidate_random_trials))+" of "+str(num_neighbor_candidates)+" were found")

		#utils.abort("implementing adding in craddles")

	else:
		utils.info(1, "* Generating " + str(num_neighbor_candidates) + " candidate positions for chip #" + str(
			1 + layout.get_num_chips()) + " in the layout")
		num_attempts = 0
		while ((len(candidate_random_trials) < num_neighbor_candidates) and (num_attempts < max_num_neighbor_candidate_attempts)):
			num_attempts += 1
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
				if result != None:
					new_chips += 1
					tmp_layout.add_new_chip(result)

			if new_chips<num_chips_to_add:
				utils.abort("Could not find any more feasible neighbors after "+str(add_attempts)+" attempts")
			candidate_list = tmp_layout.get_chip_positions()[-num_chips_to_add:]
			#utils.info(1, str(num_chips_to_add) + " Candidate random chips are " + str(candidate_list))
			candidate_random_trials.append(candidate_list)
		if len(candidate_random_trials) != num_neighbor_candidates:
			utils.abort("Only "+str(len(candidate_random_trials))+" of "+str(num_neighbor_candidates)+" were found")
	return candidate_random_trials

#@jit
def pick_candidates(layout, results, candidate_random_trials):
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
					if (num_edges > picked_candidate_num_edges):  # LL* inductors?
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

"""Random greedy layout optimization"""


def optimize_layout_random_greedy():
	layout = LayoutBuilder.compute_craddle_layout(3)

	num_neighbor_candidates = 10  # Default value
	max_num_neighbor_candidate_attempts = 1000  # default value
	num_chips_to_add = 1 # Default value
	add_scheme = None
	print utils.argv.layout_scheme
	if (len(utils.argv.layout_scheme.split(":")) == 2):
		num_neighbor_candidates = int(utils.argv.layout_scheme.split(":")[1])

	if (len(utils.argv.layout_scheme.split(":")) == 3):
		num_neighbor_candidates = int(utils.argv.layout_scheme.split(":")[1])
		max_num_neighbor_candidate_attempts = int(utils.argv.layout_scheme.split(":")[2])

	if (len(utils.argv.layout_scheme.split(":")) == 4):
		num_neighbor_candidates = int(utils.argv.layout_scheme.split(":")[1])
		max_num_neighbor_candidate_attempts = int(utils.argv.layout_scheme.split(":")[2])
		num_chips_to_add  = int(utils.argv.layout_scheme.split(":")[3])
	"""
	if (len(utils.argv.layout_scheme.split(":")) == 5):
		num_neighbor_candidates = int(utils.argv.layout_scheme.split(":")[1])
		max_num_neighbor_candidate_attempts = int(utils.argv.layout_scheme.split(":")[2])
		num_chips_to_add  = int(utils.argv.layout_scheme.split(":")[3])
		#add_scheme = int(utils.argv.layout_scheme.split(":")[3]
	"""

	results = []
	picked_index = 0

	while (layout.get_num_chips() != utils.argv.num_chips):

		###############################################
		### Create Candidates
		###############################################

		utils.info(2, "* Generating " + str(num_neighbor_candidates) + " candidate positions for chip #" + str(1 + layout.get_num_chips()) + " in the layout")
		if num_chips_to_add > utils.argv.num_chips - layout.get_num_chips(): #preprocessing
			num_chips_to_add = utils.argv.num_chips - layout.get_num_chips()
			utils.info(2, "Warning num_chips_to_add too great\nCandidates will be generated in "+str(num_chips_to_add)+"'s")
		candidate_random_trials = generate_multi_candidates(layout, [], num_neighbor_candidates, max_num_neighbor_candidate_attempts,num_chips_to_add)

		list_of_args = []
		for index in xrange(0, len(candidate_random_trials)):
			list_of_args.append([layout, candidate_random_trials[index]])
		results = map(evaluate_candidate, list_of_args)

		#print "RESULTS = ", results

		###############################################
		### Pick the best candidate
		################################################

		picked_candidate, picked_index = pick_candidates(layout, results, candidate_random_trials)
		#utils.abort("candidate random trial is \n"+str(candidate_random_trials))

		# Add the candidate
		if picked_candidate == None:
			utils.abort("Could not find a candidate that met the temperature constraint")

		utils.info(1, "Picked candidate: " + str(picked_candidate))
		for chip in picked_candidate: #LL* should we just make a deep copy form results[picked_index][0]???
			layout.add_new_chip(chip)
	#print "---> ", layout.get_num_chips(), utils.argv.num_chips

	# Do the final evaluation (which was already be done, but whatever)
	# result = find_maximum_power_budget(layout)
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
		layout = LayoutBuilder.compute_craddle_layout(3)

		num_neighbor_candidates = 20  # Default value
		max_num_neighbor_candidate_attempts = 1000  # default value
		num_chips_to_add = 1 # Default value
		add_scheme = None


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
			### - implement add craddles
			###		- find feasible craddle function, in layout
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
			picked_candidate, picked_index = pick_candidates(layout, results, candidate_random_trials)


			if picked_candidate == None:
				send_stop_signals(worker_list, comm)
				utils.abort("Could not find a candidate that met the temperature constraint")

			utils.info(1, "Picked candidate: " + str(picked_candidate))
			for chip in picked_candidate: #LL* should we just make a deep copy form results[picked_index][0]???
				layout.add_new_chip(chip)
		# Do the final evaluation (which was already be done, but whatever)
		# result = find_maximum_power_budget(layout)
		# saved_result = results[picked_index]
		# print '\n\result is ',result,'\nsaved_result is ',saved_result
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


"""Cradle layout optimization"""


def optimize_layout_craddle():
	if (utils.argv.verbose == 0):
		sys.stderr.write("o")
	utils.info(1, "Constructing a craddle layout")

	layout = LayoutBuilder.compute_craddle_layout(utils.argv.num_chips)

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
