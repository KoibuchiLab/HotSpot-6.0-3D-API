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
	numchips = [9,6]
	#candidates = workers*2
	candidate_trials = 1000
	overlaps = [.2, .1]
	#overlaps = [.1, .2]
	#add_by = ['1']#,'3','cradle']
	add_by = [ '3', '2', '1', 'cradle']
	pickby = ['network','temp','power']

	export_path = " -e results_LL/multiaddexp/figures/"
	file_name = "dirt_pick_criteria"
	raw_result_file = "LL/results_LL/"+file_name+"_raw_results.txt"
	avg_result_file = "LL/results_LL/"+file_name+"_avg_results.txt"
	raw_output_file = "LL/results_LL/"+file_name+"_raw_output.txt"
	#start = end = -1
	try:
		f = open(raw_result_file, "w+")
		header = "trial\tchips_added_at_a_time\texecution_time\tedges\tlevels\tdiameter\tASPL\tpower\tfrequency\ttempurature\tpicked_by\toverlap\tnumchips\tcandidates\n"
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

		for pick in pickby:
			for overlap in overlaps:
				for num in numchips:
					for add in add_by:
						if num == add:
							continue
						trial_results = []
						trial_ex_time = []
						candidates = workers*2
						original_can = candidates
						avg_ex_time = -1
						for dumb in range(1,2):
							for trial in range(1,11):
								#print '+++ candidate is ',original_can,' +++'
								#candidates = original_can + can
								#print '=== candidate plus range=',can,' is ',candidates,' ==='
								#add trials in after we run successfully
								command = "mpirun -np "+str(workers+1)+" ./optimize_layout.py --numchips "+str(num)+" --medium air --chip base3 --diameter "+str(num)+" --layout_scheme random_greedy:"+str(candidates)+":5000:"+str(add)+"  --numlevels "+str(num)+" --powerdistopt uniform_discrete --powerdistopt_num_iterations 1 --powerdistopt_num_trials 1  --overlap "+str(overlap)+" --max_allowed_temperature 50  --verbose 0 -P "+str(pick)+" --mpi"#+export_path+str(num)+"_chip_add_by_"+str(add)+"_trial_"+str(trial)+".pdf"

								#command = "./optimize_layout.py --numchips "+str(num)+" --medium air --chip base3 --diameter "+str(num)+" --layout_scheme checkerboard  --numlevels 7 --powerdistopt uniform_discrete --powerdistopt_num_iterations 1 --powerdistopt_num_trials 1  --overlap "+str(overlap)+" --max_allowed_temperature 50  --verbose 0 -P "+str(pick)#+" --mpi"+export_path+str(num)+"_chip_add_by_"+str(add)+"_trial_"+str(trial)+".pdf"

								#print command
								#sys.stderr.write("Error: test command\n")
								#sys.exit(1)
								print 'started at ',datetime.datetime.now()
								start = time.time()
								#devnull = open('/dev/null', 'w')
								proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE) #TODO: set a time limit and kill if over
								proc.wait()
								end = time.time()
								#out = proc.stdout.read()
								#print 'returned from subprocess'
								out, err = proc.communicate()
								#print 'parsing'
								ex_time = float(end-start)

								h = open(raw_output_file, "a+")
								h.write("\ntrial "+str(trial)+"\t add by "+str(add)+"\t ex time "+str(ex_time)+"\tpicked by "+str(pick)+"\toverlap "+str(overlap)+"\n"+out+"\n")
								h.close()
								out_str, out_val = parse_output(out,proc.returncode)

								if out_val[2] > 0:
									trial_results.append(out_val)
									trial_ex_time.append(ex_time)
								raw_result = str(trial)+"\t"+str(add)+"\t"+str(ex_time)+"\t"+out_str+"\t"+str(pick)+"\t"+str(overlap)+"\t"+str(num)+"\t"+str(candidates)+"\n"
								f = open(raw_result_file, "a+")
								f.write(raw_result)
								f.close()
								print '>>>  Trial ',trial, ' execution time is ',ex_time,' numchips = ',num,' overlap = ',overlap,' add by =  ',add
							avg_string = get_avg_string(trial_results,trial_ex_time)
							avg_result = str(add)+"\t"+avg_string+"\t"+str(pick)+"\t"+str(overlap)+"\t"+str(num)+"\t"+str(candidates)+"\n"
							g = open(avg_result_file, "a+")
							g.write(avg_result)
							g.close()
							split_avg_string = re.split(r'\t',avg_string)
							avg_ex_time = float(split_avg_string[0])
						print 'Done numchps ',num,' and add ', add

	except IOError:
		print "IOError!!!"
		sys.exit(1)

if __name__ == '__main__':
	main()
