#!/usr/bin/python

import math
import random
import os
import sys
import itertools


import argparse
from argparse import RawTextHelpFormatter

from math import sqrt

import numpy as np

#from scipy.optimize import basinhopping
#from scipy.optimize import fmin_slsqp

from layout import Chip
from layout import Layout

import utils


class PowerOptimizer(object):

        def __init__(self):
		pass


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
		if (utils.argv.verbose == 0):
			sys.stderr.write(".")
		utils.info(1, "       Temperature minimization trial for total power " + str(total_power_budget))

		[temperature, power_distribution] = minimize_temperature(layout, total_power_budget, optimization_method, num_iterations)
		if ((min_temperature == -1) or (temperature < min_temperature)):
			min_temperature = temperature
			best_power_distribution = power_distribution
			utils.info(1, "          New lowest temperature: T= " + str(min_temperature))
	
        
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
		utils.abort("Error: Unknown optimization method '" + optimization_method)


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
	utils.info(1, "\t\tRandom start: " + str(random_start))

	# Compute the temperature
	temperature =  Layout.compute_layout_temperature(layout, random_start)

	return [temperature, random_start]


"""Temperature minimizer using gradient descent"""

def minimize_temperature_gradient(layout, total_power_budget, num_iterations):

        # Generate a valid random start
	random_start = generate_random_power_distribution(layout, total_power_budget)
	utils.info(2, "\tGenerated a random start: " + str(random_start))

        result = fmin_slsqp(Layout.compute_layout_temperature, random_start, args=(layout,), full_output=True, iter=num_iterations, iprint=0)

        return [result[1], result[0]]

"""Temperature minimizer using neighbor search"""

def minimize_temperature_neighbor(layout, total_power_budget, num_iterations):

        # Generate a valid random start
	random_start = generate_random_power_distribution(layout, total_power_budget)

        best_distribution = random_start
        best_temperature = Layout.compute_layout_temperature(layout, random_start)
	utils.info(2, "\tGenerated a random start: " + str(best_distribution) + " (temperature = " + str(best_temperature) + ")")
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
                    utils.info(2, "\tNeighbor " + str(candidate) + " has temperature " + str(temperature))
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
	utils.info(2, "\tGenerated a random start: " + str(random_start))

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

""" Function to take a continuous power distribution and make it feasible by rounding up
    power specs to available discrete DFVS power levels. (doing some "clever" optimization
    to try to regain some of the lost power due to rounding off)
"""

def make_power_distribution_feasible(layout, power_distribution, initial_temperature):

        new_temperature = initial_temperature

        utils.info(1, "Continuous solution: Total= " + str(sum(power_distribution)) + "; Distribution= " + str(power_distribution))

        power_levels = layout.get_chip().get_power_levels()


        lower_bound = []
        for x in power_distribution:
            for i in xrange(len(power_levels)-1, -1, -1):
                if (power_levels[i] <= x):
                    lower_bound.append(i)
                    break

        utils.info(1, "Conservative feasible power distribution: " + str([power_levels[i] for i in lower_bound]))

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
                    if (temperature <= utils.argv.max_allowed_temperature):
                        lower_bound = tentative_new_bound[:]
                        new_temperature = temperature
                        was_able_to_increase = True
                        utils.info(1, "Improved feasible power distribution: " + str([power_levels[i] for i in lower_bound])
)
                        break
            if (not was_able_to_increase):
                break


        return ([power_levels[x] for x in lower_bound], new_temperature)



"""Top-level function to Search for the maximum power"""

def find_maximum_power_budget(layout):

	# No search because the user specified a fixed power budget?
	if (utils.argv.power_budget):
		[temperature, power_distribution] = optimize_power_distribution(layout, utils.argv.power_budget, utils.argv.powerdistopt, utils.argv.power_distribution_optimization_num_trials, utils.argv.power_distribution_optimization_num_iterations)
                [power_distribution, temperature] = make_power_distribution_feasible(layout, power_distribution, temperature)
		return [power_distribution, temperature]

	# No search because the maximum power possible is already below temperature?
        utils.info(1,"Checking if the maximum power is cool enough")
        temperature = Layout.compute_layout_temperature(layout, [layout.get_chip().get_power_levels()[-1]] * layout.get_num_chips())
        if (temperature <= utils.argv.max_allowed_temperature):
		#utils.info(2, "We can set all chips to the max power level!")
                return [[layout.get_chip().get_power_levels()[-1]] * layout.get_num_chips(), temperature]


	# No search because the minimum power possible is already above temperature?
        utils.info(1,"Checking if the minimum power is already too hot")
        temperature = Layout.compute_layout_temperature(layout, [layout.get_chip().get_power_levels()[0]] * layout.get_num_chips())
        if (temperature > utils.argv.max_allowed_temperature):
                sys.stderr.write("Even setting all chips to minimum power gives a temperature of " + str(temperature) +", which is above the maximum allowed temperature of " + str(utils.argv.max_allowed_temperature) + "\n")
                return None

		# DISCRETE?
        if is_power_optimization_method_discrete(utils.argv.powerdistopt): 
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
        if (utils.argv.powerdistopt == "exhaustive_discrete"):
		return find_maximum_power_budget_discrete_exhaustive(layout)
	elif (utils.argv.powerdistopt == "random_discrete"):
		return find_maximum_power_budget_discrete_random(layout)
	elif (utils.argv.powerdistopt == "greedy_random_discrete"):
		return find_maximum_power_budget_discrete_greedy_random(layout)
	elif (utils.argv.powerdistopt == "greedy_not_so_random_discrete"):
		return find_maximum_power_budget_discrete_greedy_not_so_random(layout)
	elif(utils.argv.powerdistopt == "uniform_discrete"):
		return find_maximum_power_budget_discrete_uniform(layout)
	else:
		utils.abort("Unknown discrete power budget maximization method " + utils.argv.powerdistopt)

""" Discrete uniform search
"""

def find_maximum_power_budget_discrete_uniform(layout):
		power_levels = layout.get_chip().get_power_levels()
		best_power_level = None
		guess_temperature = None
		lower_bound = 0
		upper_bound = len(power_levels) - 1
		guess_index = -1
		while (lower_bound != upper_bound): 
			#print "l=", lower_bound, "u=", upper_bound
			if (guess_index == (upper_bound + lower_bound) / 2):
				break
			guess_index = (upper_bound + lower_bound) / 2
			#print "Trying guess ", guess_index
			temperature = Layout.compute_layout_temperature(layout, [power_levels[guess_index]] * layout.get_num_chips())
			#print "temperature = ", temperature
			if (temperature > utils.argv.max_allowed_temperature): 
				upper_bound = guess_index
			else: 	
                                guess_temperature = temperature
				lower_bound = guess_index


		#print "PICKED index ", guess_index
		best_power_level = power_levels[guess_index]

#		for level in power_levels:
			#temperature = Layout.compute_layout_temperature(layout, [level] * layout.get_num_chips())
			#utils.info(2, "With power level " + str(level) + " for all chips: temperature = " + str(temperature));
			#if (temperature<=utils.argv.max_allowed_temperature):
				#best_power_level = level
				#best_distribution_temperature = temperature
			#else:
				#break
				
		return [[best_power_level] * layout.get_num_chips(), guess_temperature]


""" Discrete exhaustive search 
"""

def find_maximum_power_budget_discrete_exhaustive(layout):

       power_levels = layout.get_chip().get_power_levels()

       best_distribution = None
       best_distribution_temperature = None
       for distribution in itertools.permutations(power_levels,layout.get_num_chips()):
           temperature =  Layout.compute_layout_temperature(layout, distribution)
           if (temperature <= utils.argv.max_allowed_temperature):
               if (best_distribution == None) or (sum(best_distribution) < sum(distribution)):
                   best_distribution = distribution
                   best_distribution_temperature = temperature
                   utils.info(2, "Better distribution: Total=" + str(sum(best_distribution)) + "; Distribution=" + str(best_distribution) + "; Temperature= " + str(best_distribution_temperature))
           
       return [best_distribution, best_distribution_temperature]

""" Discrete random search 
"""

def find_maximum_power_budget_discrete_random(layout):
       power_levels = layout.get_chip().get_power_levels()
       distribution = layout.get_chip().get_power_levels()[0] * layout.get_num_chips(); 
       best_distribution = None
       best_distribution_temperature = None
           
       for trial in xrange(0, utils.argv.power_distribution_optimization_num_trials):
           utils.info(2, "Trial #"+str(trial))
           distribution = []
           for i in xrange(0, layout.get_num_chips()):
               distribution.append(utils.pick_random_element(power_levels))
           temperature =  Layout.compute_layout_temperature(layout, distribution)
           if (temperature <= utils.argv.max_allowed_temperature):
               if (best_distribution == None) or (sum(best_distribution) < sum(distribution)):
                   best_distribution = distribution
                   best_distribution_temperature = temperature
                   utils.info(2, "Better Random Trial: Total=" + str(sum(best_distribution)) + "; Distribution=" + str(best_distribution) + "; Temperature= " + str(temperature))

       return [best_distribution, best_distribution_temperature]


""" Discrete greedy random search 
"""

def find_maximum_power_budget_discrete_greedy_random(layout):
       power_levels = layout.get_chip().get_power_levels()
       
       best_best_distribution = None
       best_best_distribution_temperature = None

       for trial in xrange(0, utils.argv.power_distribution_optimization_num_trials):

           utils.info(2, "Trial #"+str(trial))

	   # Initialize the best distribution (that we're looking for)
           best_distribution_index = [0] * layout.get_num_chips() 
           best_distribution = [power_levels[x] for x in best_distribution_index]
               
           while (True):
               # pick one non-max chip
               while (True):
	           picked = utils.pick_random_element(range(0, layout.get_num_chips()))
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
               if (temperature > utils.argv.max_allowed_temperature):
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

       for trial in xrange(0, utils.argv.power_distribution_optimization_num_trials):

           utils.info(2, "Trial #" + str(trial))

	   # Initialize the best distribution (that we're looking for)
           best_distribution_index = [0] * layout.get_num_chips() 
           best_distribution = [power_levels[x] for x in best_distribution_index]
      	   best_temperature =  Layout.compute_layout_temperature(layout, best_distribution)
               
           while (True):
	       # Evaluate all possible increases
	       pay_off = []
               utils.info(2, "Looking at all neighbors...")
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
			if (temperature > utils.argv.max_allowed_temperature):
				pay_off.append(-1.0)
			else:
				temperature_increase = temperature - best_temperature
				pay_off.append(power_increase / temperature_increase)

	       # If all negative, we're done
	       if (max(pay_off) < 0.0):
	            break

	       # Pick the best payoff 
               utils.info(2, "Neighbor payoffs: " + str(pay_off))
	       picked = pay_off.index(max(pay_off))
		

               utils.info(2, "Picking neighbor #" + str(picked))

               # Otherwise, great
               best_distribution_index[picked] +=1 
               best_distribution = [power_levels[x] for x in candidate_index]
               best_distribution_temperature = Layout.compute_layout_temperature(layout, best_distribution)
               utils.info(2, "New temperature = " + str(best_distribution_temperature))
           
               if (best_best_distribution == None) or (sum(best_distribution) > sum(best_best_distribution)):
                    best_best_distribution = list(best_distribution)
                    best_best_distribution_temperature = best_distribution_temperature

       return [best_distribution, best_distribution_temperature]



""" Top-level function for continuous power optimization
"""

def find_maximum_power_budget_continuous(layout):

	max_possible_power = utils.argv.num_chips * utils.argv.chip.get_power_levels()[-1]

	power_attempt = max_possible_power
	next_step_magnitude = (power_attempt - utils.argv.num_chips * utils.argv.chip.get_power_levels()[0]) 
	next_step_direction = -1

	last_valid_solution = None

        utils.info(1, "New binary search for maximizing the power")

	while (True):
		if (utils.argv.verbose == 0):
			sys.stderr.write("x")
		utils.info(1, "    New binary search step (trying power = " + str(power_attempt) + " Watts)")

		[temperature, power_distribution] = optimize_power_distribution(layout, power_attempt, utils.argv.powerdistopt, utils.argv.power_distribution_optimization_num_trials, utils.argv.power_distribution_optimization_num_iterations)
		# pick new direction?
		if (temperature < utils.argv.max_allowed_temperature):
			next_step_direction = +1
		else:
			next_step_direction = -1

		# is it a valid solution? (let's record it just in case the optimization process is chaotic)
		if (temperature < utils.argv.max_allowed_temperature):
			last_valid_solution = [power_distribution, temperature]

		# decrease step size
		next_step_magnitude /= 2.0

		if (next_step_magnitude < utils.argv.power_binarysearch_epsilon):
			break

		if ((temperature < utils.argv.max_allowed_temperature) and (power_attempt == max_possible_power)):
			break

		# compute the next power attempt
		power_attempt += next_step_direction * next_step_magnitude

		
	return last_valid_solution
	
