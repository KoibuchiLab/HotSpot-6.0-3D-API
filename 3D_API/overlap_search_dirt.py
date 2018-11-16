#!/usr/bin/python

import os
import time
import sys
import subprocess
import re
import datetime

def parse_output(out,exit_code):
	#return_string = str(-1)+"\t"+str(-1)+"\t"+str(-1)+"\t"+str(-1)+"\t"+str(-1)+"\t"+str(-1)+"\t"+str(-1)
	return_string = str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)
	edge = 0
	level = 0
	diameter = 0
	aspl = 0
	power = 0
	freq = 0
	temp = 0
	if int(exit_code) == 0:
		out = re.sub('[\[\],()]', '', out)
		out = out.rstrip()
		out = out.split()
		#print 'out is \n',out
		"""
		if ('Error' in out) or not ('edges' in out):
			#set all output to -1
			print "Error Here"
			return return_string
		"""
		edge = out[out.index("edges")+2]
		level = out[out.index("Diameter")-1]
		diameter = out[out.index("Diameter")+2]
		aspl =  out[out.index("ASPL")+2]
		power = out[out.index("distribution")+2]
		freq = out[out.index("Frequency")+3]
		temp = out[out.index("Temperature")+2]
<<<<<<< HEAD

=======
	
>>>>>>> 8e10d5f6de5f7c756bc0375109b576638cf00bec
	if temp == None:
		temp = 0
	return_string = str(edge)+"\t"+str(level)+"\t"+str(diameter)+"\t"+str(aspl)+"\t"+str(power)+"\t"+str(freq)+"\t"+str(temp)
	return_value = [float(edge),float(level),float(diameter),float(aspl),float(power),float(freq),float(temp)]
	return [return_string,return_value]

def get_avg_string(trial_results, trial_ex_time):
	if len(trial_results) != len(trial_ex_time):
		print "Error, array lengths differ"
		sys.exit(1)
	time = 0.0
	edge = 0.0
	level = 0.0
	diameter = 0.0
	aspl = 0.0
	power = 0.0
	freq = 0.0
	temp = 0.0
	for trial in trial_results:
		edge+=trial[0]
		level+=trial[1]
		diameter+=trial[2]
		aspl+=trial[3]
		power+=trial[4]
		freq+=trial[5]
		temp+=trial[6]

	for times in trial_ex_time:
		time+=times

	return_string = str(time/len(trial_ex_time))+"\t"+str(edge/len(trial_results))+"\t"+str(level/len(trial_results))+"\t"+str(diameter/len(trial_results))+"\t"+str(aspl/len(trial_results))+"\t"+str(power/len(trial_results))+"\t"+str(freq/len(trial_results))+"\t"+str(temp/len(trial_results))

	return return_string

def main():
	workers = 7
	numchips = [13,5]
	candidates = workers*2
	candidate_trials = 1000
	overlaps = [.25, .20, .15, .10, .05]
	start_overlap = overlaps[-1]
	#overlaps = [.1, .2]
	#add_by = ['1','3','cradle']
	add = 'cradle'
	pickby = 'network'
	#can_range = [-2,-1,0,1,2]
	can_range = [0]
	chip_type = ['base3','base2']
	max_temp = 80

	export_path = " -e LL/results_LLres/"
	file_name = "dirt_find_overlap"
	raw_result_file = "LL/results_LL/"+file_name+"_raw.txt"
	avg_result_file = "LL/results_LL/"+file_name+"_avg.txt"
	raw_output_file = "LL/results_LL/"+file_name+"_output.txt"
	#start = end = -1
	try:
		f = open(raw_result_file, "w+")
		header = "trial\tchips_added_at_a_time\texecution_time\tedges\tlevels\tdiameter\tASPL\tpower\tfrequency\ttempurature\tpicked_by\toverlap\tnumchips\tcandidates\ttype\n"
		f.write(header)
		f.close()

		g = open(avg_result_file, "w+")
		header_g = "chips_added_at_a_time\texecution_time\tedges\tlevels\tdiameter\tASPL\tpower\tfrequency\ttempurature\tpicked_by\toverlap\tnumchips\tcandidates\n"
		g.write(header_g)
		g.close()

		h = open(raw_output_file, "w+")
		header_h = "raw output\n\n"
		h.write(header_h)
		h.close()

		overlap_good = False
		for trial in xrange(1,11):
			for type in chip_type:
				for num in xrange(15,3,-1):

					guess_temperature = None
					lower_bound = 0 #TODO:top level find max power budget checks max and min, set lower boutnd =1? and upper boutnd len(power_levels)-1-1
					upper_bound = len(overlaps)-1 ###TODO: check that - 2 works, changed from - 1
					guess_index = -1
					save_out_vals = [None]

					### check if min overlap is feasible
					command = "mpirun -np "+str(workers+1)+" ./optimize_layout.py --numchips "+str(num)+" --medium air --chip "+type+" --diameter "+str(num)+" --layout_scheme random_greedy:"+str(candidates)+":5000:"+str(add)+"  --numlevels 7 --powerdistopt max --powerdistopt_num_iterations 1 --powerdistopt_num_trials 1  --overlap "+str(start_overlap)+" --max_allowed_temperature "+str(max_temp)+" --verbose 0 -P "+str(pickby)+" --mpi -C square"#+export_path+str(num)+"_chip_add_by_"+str(add)+"_trial_"+str(trial)+".pdf"
					print command
					proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE) #TODO: set a time limit and kill if over
					proc.wait()
					out, err = proc.communicate()
					out_str, out_val = parse_output(out,proc.returncode)
					save_out_vals = out_val

					if out_val[-1] == 0:
						### if min overlap not feasible, cont
						print "Lowest overlap not feasible for numchips = ",num
						continue
					else:
						### binary search over the remaining possible overlaps, [1:]
						while (lower_bound != upper_bound):
						#print "l=", lower_bound, "u=", upper_bound
							if (guess_index == (upper_bound + lower_bound) / 2):
								break
							guess_index = (upper_bound + lower_bound) / 2
							overlap = overlaps[guess_index]
<<<<<<< HEAD
							command = "mpirun -np "+str(workers+1)+" ./optimize_layout.py --numchips "+str(num)+" --medium air --chip "+ type+" --diameter "+str(num)+" --layout_scheme random_greedy:"+str(candidates)+":5000:"+str(add)+"  --numlevels 7 --powerdistopt max --powerdistopt_num_iterations 1 --powerdistopt_num_trials 1  --overlap "+str(overlap)+" --max_allowed_temperature "+str(max_temp)+" --verbose 0 -P "+str(pickby)+" --mpi "#+export_path+str(num)+"_chip_add_by_"+str(add)+"_trial_"+str(trial)+".pdf"
=======
							command = "mpirun -np "+str(workers+1)+" ./optimize_layout.py --numchips "+str(num)+" --medium air --chip "+ type+" --diameter "+str(num)+" --layout_scheme random_greedy:"+str(candidates)+":5000:"+str(add)+"  --numlevels 7 --powerdistopt max --powerdistopt_num_iterations 1 --powerdistopt_num_trials 1  --overlap "+str(overlap)+" --max_allowed_temperature "+str(max_temp)+" --verbose 0 -P "+str(pickby)+" --mpi -C square "#+export_path+str(num)+"_chip_add_by_"+str(add)+"_trial_"+str(trial)+".pdf"
>>>>>>> 8e10d5f6de5f7c756bc0375109b576638cf00bec
							print command
							start = time.time()
							proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
							proc.wait()
							out, err = proc.communicate()
							out_str, out_val = parse_output(out,proc.returncode)
							end = time.time()
							ex_time = float(end-start)
							print 'ex time = ',str(ex_time),' for num = ',str(num),' overlap = ',str(overlap),' chip =',type
							h = open(raw_output_file, "a+")
							h.write("\ntrial "+str(trial)+"\t add by "+str(add)+"\t ex time "+str(ex_time)+"\tpicked by "+str(pickby)+"\toverlap "+str(overlap)+"\t chip type"+type+"\n"+out+"\n")
							h.close()
							#print 'guess = ',str(guess_index)
							if (proc.returncode > 0 ) or (out_val[-1] > max_temp):
								#upper_bound = guess_index
								lower_bound = guess_index
								#print 'here'
							else:
								save_out_vals = out_val
								#lower_bound = guess_index
								upper_bound = guess_index

					#print 'tem is ',str(save_out_vals[-1])
					#sys.stderr.write("Error: test command\n")
					#sys.exit(1)

					raw_result = str(trial)+"\t"+str(add)+"\t"+str(ex_time)+"\t"+out_str+"\t"+str(pickby)+"\t"+str(overlap)+"\t"+str(num)+"\t"+str(candidates)+"\t"+type+"\n"
					f = open(raw_result_file, "a+")
					f.write(raw_result)
					f.close()

	except IOError:
		print "IOError!!!"
		sys.exit(1)

if __name__ == '__main__':
	main()
