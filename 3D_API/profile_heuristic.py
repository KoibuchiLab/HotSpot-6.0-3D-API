#!/usr/bin/python

import subprocess

def main():
	
	add_by = ['cradle','3','2','1']
	num_chips = [6,9]
	path = "LL/results_LL/heuristic_profile/"
	for chip in num_chips:
		for add in add_by:
			output_file_name = str(path)+""+str(chip)+"_add_by_"+str(add)+"_profile_output.txt"
			command =  "python -m cProfile ./optimize_layout.py --numchips "+str(chip)+" --medium air --chip base3 --diameter "+str(chip)+" --layout_scheme random_greedy:1:5000:"+str(add)+" --numlevels 7 --powerdistopt uniform_discrete --powerdistopt_num_iterations 1 --powerdistopt_num_trials 1 --overlap .2 --max_allowed_temperature 500 --verbose 0 -P power > "+str(output_file_name) 

			print ">>>>>> output file name is "+str(output_file_name)
			proc = subprocess.Popen(command, shell=True)
			proc.wait()

if __name__=='__main__':
	main()

