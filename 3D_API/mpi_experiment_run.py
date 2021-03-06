#!/usr/bin/python

import os
import time
import subprocess

def load_ars(arg_dict):
	arguments = " "
	for x in arg_dict:
		#print x
		if x == "--mpi" and arg_dict[x] != None:
			arguments +=" "+str(x)
			print x
		elif x == "--test" and arg_dict[x] != None:
			arguments +=" "+str(x)
		elif arg_dict[x] != None:
			arguments +=" "+str(x)+" "+str(arg_dict[x])
	return arguments

medium = None #<cooling medium>, -m <cooling medium> "air", "oil", "water"
chip = None #<chip name>, -c <chip name> options: "e5-2667v4", "phi7250", "base2"
numchips = None #<# of chips>, -n <# of chips> the number of chips
diameter = None #<diameter>, -d <diameter> the network diameter (ignored for layouts with known/fixed diameter)
layout_scheme = None #<layout scheme>, -L <layout scheme> options: "checkerboard", "linear_random_greedy", "stacked",  "random_greedy"
numlevels = None #<# of levels>, -l <# of levels> the number of vertical levels
powerdistopt = None #<power distribution optimization method>, -t <power distribution optimization method> "uniform_discrete", "exhaustive_discrete", "random_discrete", "greedy_random_discrete", "greedy_not_so_random_discrete",  "uniform", "random", "gradient", "neighbor", "simulated_annealing_gradient"
powerdistopt_num_iterations = None #<# of iterations>, -I <# of iterations> number of iterations used for each power distribution optimization trial
powerdistopt_num_trials = None #<# of trials>, -T <# of trials> number of trials used for power distribution optimization
power_benchmark = None #<power benchmark>, -B <power benchmark> benchmark used to determine available chip power levels (default: overall_max)
overlap = None #<chip area overlap>, -O <chip area overlap> the fraction of chip area overlap fraction (default = 1/9)
power_budget = None #<total power>, -p <total power> the power of the whole system (precludes the search for the maximum power)
power_binarysearch_epsilon = None #<threshold in Watts>, -b <threshold in Watts>  the step size, in Watts, at which the binary search for the maximum power budget stops (default = 0.1)
max_allowed_temperature = None #<temperature in Celsius>, -a <temperature in Celsius> the maximum allowed temperature for the layout (default: 58)
grid_size = None #<Hotspot temperature map size>, -g <Hotspot temperature map size> the grid size used by Hotspot (larger means more RAM and more CPU; default: 2048)
verbose = None #<integer verbosity level>, -v <integer verbosity level>  verbosity level for debugging/curiosity
"""
================================================================================================================================================================
=======CHANGE ARGS BELOW THIS==============================================================================================================================
================================================================================================================================================================
"""
numchips = 6
medium = "air"
chip = "base3"
diameter = 5
layout_scheme = "random_greedy:15:5000:1"
numlevels = 3
powerdistopt = "uniform_discrete"
powerdistopt_num_iterations = 1
powerdistopt_num_trials = 1
overlap = .2
max_allowed_temperature = 100
verbose = 0
mpi = True
test = None
#num_worker_ranks = 4
"""
================================================================================================================================================================
=======CHANGE ONLY ABOVE THIS==============================================================================================================================
================================================================================================================================================================
"""


arg_dict = {"--medium":medium, "--chip":chip, "--numchips":numchips, "--diameter": diameter, "--layout_scheme":layout_scheme, "--numlevels":numlevels, "--powerdistopt":powerdistopt, "--powerdistopt_num_iterations":powerdistopt_num_iterations, "--powerdistopt_num_trials":powerdistopt_num_trials, "--power_benchmark":power_benchmark, "--overlap":overlap, "--power_budget":power_budget, "--overlap":overlap, "--power_binarysearch_epsilon":power_binarysearch_epsilon, "--max_allowed_temperature":max_allowed_temperature, "--grid_size":grid_size, "--verbose":verbose, "--mpi":mpi, "--test":test}
#print "arg dict is ",arg_dict
run_string = load_ars(arg_dict)
test_results = []
write_string = "num_workers\tavg_runtime"
import multiprocessing
raw_data_string = "num_workers\ttrial\truntime"
#max_num_workers = multiprocessing.cpu_count()
max_num_workers = 32
min_num_workers = 1
trial_num = 10
#print run_string
raw_results_file = "results_LL/mpiexp/koi_raw_mpi_results.txt"
avg_results_file = "results_LL/mpiexp/koi_avg_mpi_results.txt"

try:
	f = open(raw_results_file,'w+')
	f.write(raw_data_string)
	f.close()
	g = open(avg_results_file,'w+')
	g.write(write_string)
	g.close()
	for num_worker_ranks in range(max_num_workers,min_num_workers,-1):
		avg = -1
		to_avg = []
		for trial in range(trial_num):
			print 'Trial ',trial,' workers=',num_worker_ranks
			#print "mpirun -np "+str(num_worker_ranks+1)+" ./optimize_layout.py"+run_string, 'trial ', trial
			command = "mpirun -np "+str(num_worker_ranks+1)+" ./optimize_layout.py"+run_string
			#print 'command is ',command
			start = time.time()
			subprocess.Popen(command, stdout=subprocess.PIPE,  shell=True).wait()
			end = time.time()
			raw_data_string="\n"+str(num_worker_ranks)+"\t"+str(trial+1)+"\t"+str((end-start))

			f = open(raw_results_file,"a+")
			f.write(raw_data_string)
			f.close()

			to_avg.append((end-start))
		avg = (sum(to_avg)/len(to_avg))
		write_string ="\n"+str(num_worker_ranks)+"\t"+str(avg)
		print '!!!!!!!!!! num workers done is ', num_worker_ranks

		g = open(avg_results_file,"a+")
		g.write(write_string)
		g.close()

except IOError:
	print "IOError!!!"
	sys.exit(1)
