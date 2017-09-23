#!/usr/bin/python

import math
import random
import os
import sys
import subprocess
import itertools

from layout import Chip
from layout import Layout

import argparse
from argparse import RawTextHelpFormatter

from math import sqrt

import numpy as np

from scipy.optimize import basinhopping
from scipy.optimize import fmin_slsqp


##############################################################################################
### POWER DISTRIBUTION OPTIMIZATION (FOR A GIVEN LAYOUT and POWER BUDGET) 
##############################################################################################

"""Helper function to generate a decent random starting power distribution for searching"""
def generate_random_power_distribution(layout, total_power_budget):
	# Generate a valid random start
	power_distribution = []
	for i in range(0, layout.get_num_chips()):
		power_distribution.append(layout.get_chip().get_power_levels()[-1])

	while (True):
		extra = sum(power_distribution) - total_power_budget
		if (extra <= 0):
			break
		# pick a victim
		victim = random.randint(0, layout.get_num_chips() - 1)
		# decrease the victim by something that makes sense
		reduction = random.uniform(0, min(extra, power_distribution[victim] - layout.get_chip().get_power_levels()[0]))
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
	temperature =  Layout.compute_layout_temperature(layout, uniform_distribution)

	return [temperature, uniform_distribution]


"""Temperature minimizer using a simple random CONTINUOUS search"""
def minimize_temperature_random_continuous(layout, total_power_budget, num_iterations):
	
	# Generate a valid random start
	random_start = generate_random_power_distribution(layout, total_power_budget)
	if (argv.verbose > 1):
		sys.stderr.write("\t\tRandom start: " + str(random_start) + "\n")

	# Compute the temperature
	temperature =  Layout.compute_layout_temperature(layout, random_start)

	return [temperature, random_start]


"""Temperature minimizer using gradient descent"""
def minimize_temperature_gradient(layout, total_power_budget, num_iterations):

        # Generate a valid random start
	random_start = generate_random_power_distribution(layout, total_power_budget)
	if (argv.verbose > 1):
		sys.stderr.write("\tGenerated a random start: " + str(random_start) + "\n")

        result = fmin_slsqp(Layout.compute_layout_temperature, random_start, args=(layout,), full_output=True, iter=num_iterations, iprint=0)

        return [result[1], result[0]]

"""Temperature minimizer using neighbor search"""
def minimize_temperature_neighbor(layout, total_power_budget, num_iterations):

        # Generate a valid random start
	random_start = generate_random_power_distribution(layout, total_power_budget)

        best_distribution = random_start
        best_temperature = Layout.compute_layout_temperature(layout, random_start)
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
                if (max(candidate) > max(layout.get_chip().get_power_levels())) or (min(best_distribution) < min(layout.get_chip().get_power_levels())):
                    continue
	        temperature =  Layout.compute_layout_temperature(layout, candidate)
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
		bounds = bounds + ((layout.get_chip().get_power_levels()[0], layout.get_chip().get_power_levels()[-1]),)

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

	return Layout.compute_layout_temperature(layout, x)


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
        temperature = Layout.compute_layout_temperature(layout, [layout.get_chip().get_power_levels()[0]] * layout.get_num_chips())
        if (temperature > argv.max_allowed_temperature):
                sys.stderr.write("Even setting all chips to minimum power gives a temperature of " + str(temperature) +", which is above the maximum allowed temperature of " + str(argv.max_allowed_temperature) + "\n")
                return None

	# No search because the maximum power possible is already below temperature?
        temperature = Layout.compute_layout_temperature(layout, [layout.get_chip().get_power_levels()[-1]] * layout.get_num_chips())
        if (temperature <= argv.max_allowed_temperature):
		if (argv.verbose > 1):
			sys.stderr.write("We can set all chips to the max power level!\n")
                return [[layout.get_chip().get_power_levels()[-1]] * layout.get_num_chips(), temperature]

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
		power_levels = layout.get_chip().get_power_levels()
		best_power_level = None
		best_distribution_temperature = None
		for level in power_levels:
			temperature = Layout.compute_layout_temperature(layout, [level] * layout.get_num_chips())
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

       power_levels = layout.get_chip().get_power_levels()

       best_distribution = None
       best_distribution_temperature = None
       for distribution in itertools.permutations(power_levels,layout.get_num_chips()):
           temperature =  Layout.compute_layout_temperature(layout, distribution)
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
       power_levels = layout.get_chip().get_power_levels()
       distribution = layout.get_chip().get_power_levels()[0] * layout.get_num_chips(); 
       best_distribution = None
       best_distribution_temperature = None
           
       for trial in xrange(0, argv.power_distribution_optimization_num_trials):
           if (argv.verbose > 1):
               sys.stderr.write("Trial #"+str(trial)+"\n")
           distribution = []
           for i in xrange(0, layout.get_num_chips()):
               distribution.append(pick_random_element(power_levels))
           temperature =  Layout.compute_layout_temperature(layout, distribution)
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
       power_levels = layout.get_chip().get_power_levels()
       
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
               temperature =  Layout.compute_layout_temperature(layout, candidate)
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
       power_levels = layout.get_chip().get_power_levels()
       
       best_best_distribution = None
       best_best_distribution_temperature = None

       for trial in xrange(0, argv.power_distribution_optimization_num_trials):

           if (argv.verbose > 1):
               sys.stderr.write("Trial #"+str(trial)+"\n")

	   # Initialize the best distribution (that we're looking for)
           best_distribution_index = [0] * layout.get_num_chips() 
           best_distribution = [power_levels[x] for x in best_distribution_index]
      	   best_temperature =  Layout.compute_layout_temperature(layout, best_distribution)
               
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
               		temperature =  Layout.compute_layout_temperature(layout, candidate)
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
               best_distribution_temperature = Layout.compute_layout_temperature(layout, best_distribution)
               if (argv.verbose > 1):
                    sys.stderr.write("New temperature = " + str(best_distribution_temperature) + "\n")
           
               if (best_best_distribution == None) or (sum(best_distribution) > sum(best_best_distribution)):
                    best_best_distribution = list(best_distribution)
                    best_best_distribution_temperature = best_distribution_temperature

       return [best_distribution, best_distribution_temperature]



""" Top-level function for continuous power optimization
"""
def find_maximum_power_budget_continuous(layout):

	max_possible_power = argv.num_chips * argv.chip.get_power_levels()[-1]

	power_attempt = max_possible_power
	next_step_magnitude = (power_attempt - argv.num_chips * argv.chip.get_power_levels()[0]) 
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

        if (argv.num_levels < argv.num_chips):
		abort("Not enough levels to build a stacked layout with " + \
                         str(argv.num_chips) + " chips")
            
        for level in xrange(1, argv.num_chips+1):
            positions.append([level, 0.0, 0.0])

	return Layout(argv.chip, positions, argv.medium, argv.overlap)


"""Function to compute a straight linear layout"""
def compute_rectilinear_straight_layout():

	positions = []

	current_level = 1
	level_direction = 1
	current_x_position = 0.0
	current_y_position = 0.0
	for i in xrange(0, argv.num_chips):
		positions.append([current_level, current_x_position, current_y_position])
		current_level += level_direction
		if (current_level > argv.num_levels):
			current_level = argv.num_levels - 1
			level_direction = -1
		if (current_level < 1):
			current_level = 2
			level_direction = 1
		current_x_position += argv.chip.x_dimension * (1 - argv.overlap)
		
	return Layout(argv.chip, positions, argv.medium, argv.overlap)

	
"""Function to compute a diagonal linear layout"""
def compute_rectilinear_diagonal_layout():

	positions = []

	current_level = 1
	level_direction = 1
	current_x_position = 0.0
	current_y_position = 0.0
	for i in xrange(0, argv.num_chips):
		positions.append([current_level, current_x_position, current_y_position])
		current_level += level_direction
		if (current_level > argv.num_levels):
			current_level = argv.num_levels - 1
			level_direction = -1
		if (current_level < 1):
			current_level = 2
			level_direction = 1
		current_x_position += argv.chip.x_dimension * (1 - sqrt(argv.overlap))
		current_y_position += argv.chip.y_dimension * (1 - sqrt(argv.overlap))
		
	return Layout(argv.chip, positions, argv.medium, argv.overlap)


"""Function to compute a checkerboard layout"""
def compute_checkerboard_layout():

	positions = []

        if (argv.num_levels != 2):
		abort("A checkerboard layout can only be built for 2 levels")
        if (argv.overlap > 0.25):
		abort("A checkerboard layout can only be built with overlap <= 0.25")
            
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
	alpha = sqrt(argv.overlap)
        x_overlap = alpha * argv.chip.x_dimension
        y_overlap = alpha * argv.chip.y_dimension

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

	return Layout(argv.chip, positions, argv.medium, argv.overlap)


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
	
			
"""Helper function that returns a randomly placed rectangle that overlaps
   with another rectangle by a fixed amount, avoiding all negative coordinates
	- rectangle1_bottom_left = [x,y]: bottom left corner of the initial rectangle
	- rectangle_dimensions = [x,y]: size of the rectangle sides
	- overlap: the fraction of overlap
   returns:
	- [x,y]: bottom left corner of the new rectangle
"""
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

         # Consider all other symmetries

         # South-East
         new_picked_x = picked_x
         new_picked_y = (rectangle1_y  + dim_y) - picked_y - dim_y
	 if (new_picked_x >= 0) and (new_picked_y >= 0):
		candidates.append([new_picked_x, new_picked_y])
         
         # North-West
         new_picked_x = (rectangle1_x + dim_x) - picked_x - dim_x
         new_picked_y = picked_y
	 if (new_picked_x >= 0) and (new_picked_y >= 0):
		candidates.append([new_picked_x, new_picked_y])

         # South-West
         new_picked_x = (rectangle1_x + dim_x) - picked_x - dim_x
         new_picked_y = (rectangle1_y + dim_y) - picked_y - dim_y
	 if (new_picked_x >= 0) and (new_picked_y >= 0):
		candidates.append([new_picked_x, new_picked_y])

	 # At this point, we just pick one of the candidates at random
 	 return pick_random_element(candidates)	



"""Linear random greedy layout optimization"""
def optimize_layout_linear_random_greedy():

	# Create an initial layout
	layout = Layout(argv.chip, [[1, 0.0, 0.0]], argv.medium, argv.overlap)

	
	max_num_random_trials = 5  # TODO: Don't hardcode this
	while (layout.get_num_chips() != argv.num_chips):
                if (argv.verbose > 0):
                        sys.stderr.write("* Generating " + str(max_num_random_trials) + " candidate positions for chip #" + str(1 + layout.get_num_chips()) + " in the layout\n")
		num_random_trials = 0
                candidate_random_trials = []
		while (len(candidate_random_trials) < max_num_random_trials):
			last_chip_position = layout.get_chip_positions()[-1]

			# Pick a random location relative to the last chip

			# pick a random level
			possible_levels = []
			if (last_chip_position[0] == 1):
				possible_levels = [2]
			elif (last_chip_position[0] == argv.num_levels):
				possible_levels = [argv.num_levels - 1]
			else:
				possible_levels = [last_chip_position[0]-1, last_chip_position[0]+1]

			picked_level = pick_random_element(possible_levels)

                        # pick a random coordinates
			[picked_x, picked_y] = get_random_overlapping_rectangle([last_chip_position[1], last_chip_position[2]], [layout.get_chip().x_dimension, layout.get_chip().y_dimension], argv.overlap)

                        # Check that the chip can fit
                        if (not layout.can_new_chip_fit([picked_level, picked_x, picked_y])):
                            continue

                        candidate_random_trials.append([picked_level, picked_x, picked_y])

                # Pick a candidate
                max_power = -1
                picked_candidate = None
                for candidate in candidate_random_trials:
                        layout.add_new_chip(candidate) 
                        print layout.get_chip_positions()
                        if (argv.verbose > 0):
                                sys.stderr.write("- Evaluating candidate " + str(candidate) + "\n")
                        result = find_maximum_power_budget(layout) 
                        if (result != None):
                            [power_distribution, temperature] = result
                            if (sum(power_distribution) > max_power):
                                picked_candidate = candidate
                        layout.remove_chip(layout.get_num_chips() - 1)
                        
                # Add the candidate 
                if (argv.verbose > 0):
                        sys.stderr.write("Picked candidate: " + str(candidate) + "\n")
                layout.add_new_chip(picked_candidate) 
                        

        # Do the final evaluation (which was already be done, but whatever)
        result = find_maximum_power_budget(layout) 
        if (result == None):
            return None

        [power_distribution, temperature] = result

	return [layout, power_distribution, temperature]


"""Random greedy layout optimization"""
def optimize_layout_random_greedy():

	abort("optimize_layout_random_greedy() is not implemented yet")

	# Create an initial layout: TODO This could be anything
	layout = Layout(argv.chip, [[1, 0.0, 0.0]], argv.medium, argv.overlap)

	max_num_random_trials = 5 # TODO: Don't hardcode this
	while (layout.get_num_chips() != argv.num_chips):
                if (argv.verbose > 0):
                        sys.stderr.write("* Generating " + str(max_num_random_trials) + " candidate positions for chip #" + str(1 + layout.get_num_chips()) + " in the layout\n")
		num_random_trials = 0
                candidate_random_trials = []
		while (len(candidate_random_trials) < max_num_random_trials):

			# Pick a neighboring chip

			# TODO: Linear	
			#neighbor_of = layout.get_chip_positions()[-1]

			# Pick a random neighbor
			neighbor_of = random.uniform(0, layout.get_num_chips()-1)

			# Check whether adding a neighbor to that chip would be ok
                        # diameter-wise
			# TODO TODO TODO TODO TODO	

			# pick a random level
			possible_levels = []
			if (last_chip_position[0] == 1):
				possible_levels = [2]
			elif (last_chip_position[0] == argv.num_levels):
				possible_levels = [argv.num_levels - 1]
			else:
				possible_levels = [last_chip_position[0]-1, last_chip_position[0]+1]

			picked_level = pick_random_element(possible_levels)

                        # pick a random coordinates
			[picked_x, picked_y] = get_random_overlapping_rectangle([last_chip_position[1], last_chip_position[2]], [layout.get_chip().x_dimension, layout.get_chip().y_dimension], argv.overlap)

                        # Check that the chip can fit
                        if (not layout.can_new_chip_fit([picked_level, picked_x, picked_y])):
                            continue

                        candidate_random_trials.append([picked_level, picked_x, picked_y])

                # Pick a candidate
                max_power = -1
                picked_candidate = None
                for candidate in candidate_random_trials:
                        layout.add_new_chip(candidate) 
                        print layout.get_chip_positions()
                        if (argv.verbose > 0):
                                sys.stderr.write("- Evaluating candidate " + str(candidate) + "\n")
                        result = find_maximum_power_budget(layout) 
                        if (result != None):
                            [power_distribution, temperature] = result
                            if (sum(power_distribution) > max_power):
                                picked_candidate = candidate
                        layout.remove_chip(layout.get_num_chips() - 1)
                        
                # Add the candidate 
                if (argv.verbose > 0):
                        sys.stderr.write("Picked candidate: " + str(candidate) + "\n")
                layout.add_new_chip(picked_candidate) 

        # Do the final evaluation (which was already be done, but whatever)
        result = find_maximum_power_budget(layout) 
        if (result == None):
            return None

        [power_distribution, temperature] = result

	return [layout, power_distribution, temperature]



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

        power_levels = layout.get_chip().get_power_levels(argv.power_benchmark)


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
                    temperature = Layout.compute_layout_temperature(layout, tentative_power_distribution)
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

	parser.add_argument('--draw_in_octave', '-D', action='store_true', 
                            required=False, default=False,
                            dest='draw_in_octave', 
                            help='generates a PDF of the topology using octave')


	return parser.parse_args()


def abort(message):
	sys.stderr.write("Error: " + message + "\n")
	sys.exit(1)


# Parse command-line arguments
argv = parse_arguments()

if  not (argv.chip_name in ["e5-2667v4", "phi7250"]):
	abort("Chip '" + argv.chip_name + "' not supported")
else:
	argv.chip = Chip(argv.chip_name,  argv.power_benchmark)

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
    sys.exit(1)


[layout, power_distribution, temperature] = solution
    
print "----------- OPTIMIZATION RESULTS -----------------"
print "Chip = ", layout.get_chip().name
print "Chip power levels = ", layout.get_chip().get_power_levels()
print "Layout =", layout.get_chip_positions()
print "Topology = ", layout.get_topology()
print "Diameter = ", layout.get_diameter()
print "Power budget = ", sum(power_distribution)
print "Power distribution =", power_distribution
print "Temperature =", temperature

if (argv.draw_in_octave):
	layout.draw_in_octave()

sys.exit(0)


#############################################################################################
#############################################################################################
