#!/usr/bin/python

#import math
#import random
import os
import sys
#import itertools
#
#
import argparse
from argparse import RawTextHelpFormatter

import utils
from layout import *


#
#from math import sqrt
#
#import numpy as np
#
#from scipy.optimize import basinhopping
#from scipy.optimize import fmin_slsqp
#
from layout import Chip
from layout_optimizer import LayoutOptimizer
from layout_optimizer import optimize_layout
#from layout import Layout
#



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

  - random_greedy[:num_neighbor_candidates[:max_num_neighbor_candidate_attempts]]:
	a greedy randomized search that incrementally adds chips
        to a starting layout. Each iteration, it tries to come up with
        <num_neighbor_candidates> candidates, and then picks the best one.
        It gives up if at an iteration, it cannot come up with the required
        number of candidates after <max_num_neighbor_candidate_attempts> attempts

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
                            required=True, help='options: "e5-2667v4", "phi7250", "base2"')

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

	parser.add_argument('--constrained_overlap_geometry', '-C', action='store_true',
                            required=False,
                            dest='constrained_overlap_geometry',
                            help='Force chip overlap area to be a string or a rectangle with same aspect ratio as the chip')

	parser.add_argument('--power_budget', '-p', action='store',
		            type=float, required=False,
                            dest='power_budget', metavar='<total power>',
                            help='the power of the whole system (precludes the search for the maximum power)')

	parser.add_argument('--power_binarysearch_epsilon', '-b', action='store',
		            type=float, required=False, default=10,
                            dest='power_binarysearch_epsilon', metavar='<threshold in Watts>',
                            help='the step size, in Watts, at which the binary search for the maximum\npower budget stops (default = 0.1)')

	parser.add_argument('--max_allowed_temperature', '-a', action='store',
		            type=float, required=False, default=58,
                            dest='max_allowed_temperature', metavar='<temperature in Celsius>',
                            help='the maximum allowed temperature for the layout (default: 58)')

	parser.add_argument('--grid_size', '-g', action='store',
		            type=int, required=False, default=2048,
                            dest='grid_size', metavar='<Hotspot temperature map size>',
                            help='the grid size used by Hotspot (larger means more RAM and more CPU; default: 2048)')

	parser.add_argument('--verbose', '-v', action='store',
                            type=int, required=False, default=0,
                            dest='verbose', metavar='<integer verbosity level>',
                            help='verbosity level for debugging/curiosity')
	parser.add_argument('--mpi', '-M', action='store_true',
                            required=False,
                            dest='mpi',
                            help='implements MPI version of Layout algorithm')
	parser.add_argument('--test', '-z', action='store_true',
                            required=False,
                            dest='test',
                            help='real, calls hotspot_LL.py. test, calls fake_hotspot_LL.py')

#	parser.add_argument('--draw_in_octave', '-D', action='store',
#                            required=False,
#                            dest='draw_in_octave', metavar='<PDF file path>',
#                            help='generates a PDF of the topology using octave')

	parser.add_argument('--export_to_PDF', '-e', action='store',
                            required=False,
                            dest='export_to_PDF', metavar='<PDF file path>',
                            help='Saves a PDF of the final layout viewed from above')

	parser.add_argument('--show_in_3D', '-s', action='store_true',
                            required=False,
                            dest='show_in_3D',
                            help='opens up an interactive matplotlib visualization')



	return parser.parse_args()


if __name__ == '__main__':

	# Parse command-line arguments
	argv = parse_arguments()

	utils.argv = argv

	if  not (argv.chip_name in ["e5-2667v4", "phi7250", "base2"]):
		utils.abort("Chip '" + argv.chip_name + "' not supported")
	else:
		argv.chip = Chip(argv.chip_name,  argv.power_benchmark)

	if (argv.num_chips < 1):
		utils.abort("The number of chips (--numchips, -n) should be >0")

	if (argv.layout_scheme == "stacked") or (argv.layout_scheme == "rectilinear_straight") or (argv.layout_scheme == "rectilinear_diagonal") or (argv.layout_scheme == "linear_random_greedy") or (argv.layout_scheme == "checkerboard"):
	    argv.diameter = argv.num_chips

	if (argv.diameter < 1):
		utils.abort("The diameter (--diameter, -d) should be >0")

	if (argv.diameter > argv.num_chips):
	    utils.abort("The diameter (--diameter, -d) should <= the number of chips")

	if (argv.num_levels < 2):
		utils.abort("The number of levels (--numlevels, -d) should be >1")

	if ((argv.overlap < 0.0) or (argv.overlap > 1.0)):
		utils.abort("The overlap (--overlap, -O) should be between 0.0 and 1.0")

	if (argv.power_distribution_optimization_num_iterations < 0):
		utils.abort("The number of iterations for power distribution optimization (--powerdistopt_num_iterations, -I) should be between > 0")

	if (argv.power_distribution_optimization_num_trials < 0):
		utils.abort("The number of trials for power distribution optimization (--powerdistopt_num_trials, -T) should be between > 0")

	if ((argv.medium != "water") and (argv.medium != "oil") and (argv.medium != "air")):
		utils.abort("Unsupported cooling medium '" + argv.medium + "'")

	if (argv.powerdistopt == "exhaustive_discrete") or (argv.powerdistopt == "uniform") or (argv.powerdistopt == "random") or (argv.powerdistopt == "random_discrete") or (argv.powerdistopt == "greedy_random_discrete") or (argv.powerdistopt == "greedy_not_so_random_discrete") or (argv.powerdistopt == "uniform_discrete"):
	        argv.power_distribution_optimization_num_iterations = 1

	if (argv.powerdistopt == "exhaustive_discrete") or (argv.powerdistopt == "uniform") or (argv.powerdistopt == "uniform_discrete"):
	        argv.power_distribution_optimization_num_trials = 1

	if argv.power_budget:
	    if (argv.powerdistopt == "exhaustive_discrete") or (argv.powerdistopt == "random_discrete") or (argv.powerdistopt == "greedy_random_discrete") or (argv.powerdistopt == "greedy_not_so_random_discrete") or (argv.powerdistopt == "uniform_discrete"):
	        utils.abort("Cannot use discrete power distribution optimization method with a fixed power budget")

	# Recompile cell.c with specified grid size
	os.system("gcc -Ofast cell.c -o cell -DGRID_SIZE=" + str(argv.grid_size))


	#LayoutBuilder.plot_custom_layout([[1, 0.04658333333342, 0.04658333333342], [2, 0.039, 0.04658333333342], [2, 0.054166666666839995, 0.04658333333342], [3, 0.06118531404603599, 0.04535603277612142], [2, 0.06844800401714311, 0.04608256902552676], [1, 0.07583789608876314, 0.04653082001026776], [2, 0.08181970413659798, 0.04356426838920758], [3, 0.0880624717912586, 0.046143335222079154], [2, 0.09517271435564352, 0.04509911904430141], [3, 0.04785194584383044, 0.044116426238186304], [3, 0.07466364380329842, 0.042613788179219056], [1, 0.060330541981455606, 0.04928266301122845], [1, 0.08902253255766641, 0.04441754033281321]])


	LayoutOptimizer()

	solution = optimize_layout()

	if (solution == None):
	    print "************* OPTIMIZATION FAILED ***********"
	    sys.exit(1)


	[layout, power_distribution, temperature] = solution

	print "----------- OPTIMIZATION RESULTS -----------------"
	print "Chip = ", layout.get_chip().name
	print "Chip frequencies and power levels = ", [(f, float("%.4f" % power)) for (f, power) in layout.get_chip().get_frequencies_and_power_levels()]
	print "Layout =", layout.get_chip_positions()
	print "Topology = ", layout.get_topology()
	print "Number of edges = ", len(layout.get_topology())
	print "Number of levels = ", int(layout.get_num_levels())
	print "Diameter = ", layout.get_diameter()
	print "ASPL = ", layout.get_ASPL()
	print "Power budget = ", float("%.4f" % sum(power_distribution))
	print "Power distribution =", [float("%.4f" % p) for p in power_distribution]
	frequency_distribution = []
	for p in power_distribution:
		for (freq, power) in argv.chip.get_frequencies_and_power_levels():
			if (abs(power - p) < 0.0001):
				frequency_distribution.append(freq)
	print "Frequency distribution =", frequency_distribution
	print "Temperature =", temperature

	if (argv.export_to_PDF):
		layout.draw_in_3D(utils.argv.export_to_PDF, False)

	if (argv.show_in_3D):
		layout.draw_in_3D(None, True)

	sys.exit(0)
