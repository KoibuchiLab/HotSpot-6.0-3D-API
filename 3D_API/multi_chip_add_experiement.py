#!/usr/bin/python

import os
import time
import sys
import subprocess
import re

def parse_output(out):
	return_string = str(-1)+"\t"+str(-1)+"\t"+str(-1)+"\t"+str(-1)+"\t"+str(-1)+"\t"+str(-1)+"\t"+str(-1)+"\n"

	out = re.sub('[\[\],()]', '', out)
	out = out.rstrip()
	out = out.split()
	if 'Error' in out:
		#set all output to -1
		print "Here"
		return return_string

	edge = out[out.index("edges")+2]
	level = out[out.index("Diameter")-1]
	diameter = out[out.index("Diameter")+2]
	aspl =  out[out.index("ASPL")+2]
	power = out[out.index("distribution")+2]
	freq = out[out.index("Frequency")+3]
	temp = out[out.index("Temperature")+2]

	return_string = str(edge)+"\t"+str(level)+"\t"+str(diameter)+"\t"+str(aspl)+"\t"+str(power)+"\t"+str(freq)+"\t"+str(temp)+"\n"
	return return_string

def main():
	"""
	medium = "air"
	chip = "base2"
	diameter = [7,5]
	layout_scheme = "random_greedy"
	numlevels = [7,5]
	powerdistopt = "uniform_discrete"
	powerdistopt_num_iterations = 1
	powerdistopt_num_trials = 1
	overlap = .2
	max_allowed_temperature = 68
	verbose = 0
	mpi = True
	test = None
	"""
	numchips = [12,9]
	candidates = 15
	candidate_trials = 1000
	add_by = [9,6,3,1]
	#time = -1

	#start = end = -1
	try:
		f = open("results_LL/multiaddexp/prelim_multichip_results.txt", "w+")
		header = "chips_added_at_a_time\texecution_time\tedges\tlevels\tdiameter\tASPL\tpower\tfrequency\ttempurature\n"
		f.write(header)
		f.close()
		for num in numchips:
			for add in add_by:
				#add trials in after we run successfully
				command = "mpirun -np 16 ./optimize_layout.py --numchips "+str(num)+" --medium air --chip base3 --diameter 7 --layout_scheme random_greedy:15:3000:"+str(add)+"  --numlevels 7 --powerdistopt uniform_discrete --powerdistopt_num_iterations 1 --powerdistopt_num_trials 1  --overlap .20 --max_allowed_temperature 100  --verbose 0 --mpi"
				start = time.time()
				devnull = open('/dev/null', 'w')
				proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, stderr=devnull)
				end = time.time()
				out = proc.stdout.read()
				#out, err = procs.communicate()
				result = str(add)+"\t"+str(end-start)+"\t"+parse_output(out)
				f = open("results_LL/multiaddexp/prelim_multichip_results.txt", "a")
				f.write(result)
				f.close()
				print 'Done numchps ',num,' and add ', add
			footer = "base3\nlayout_size = "+str(num)+"\ncandidates "+str(candidates)+"\n\n"
			f = open("results_LL/multiaddexp/prelim_multichip_results.txt", "a")
			f.write(footer)
			f.close()

	except IOError:
		print "IOError!!!"
		sys.exit(1)

if __name__ == '__main__':
	main()
