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
	#print 'out is \n',out
	if 'Error' in out:
		#set all output to -1
		print "Error Here"
		return return_string

	edge = out[out.index("edges")+2]
	level = out[out.index("Diameter")-1]
	diameter = out[out.index("Diameter")+2]
	aspl =  out[out.index("ASPL")+2]
	power = out[out.index("distribution")+2]
	freq = out[out.index("Frequency")+3]
	temp = out[out.index("Temperature")+2]

	return_string = str(edge)+"\t"+str(level)+"\t"+str(diameter)+"\t"+str(aspl)+"\t"+str(power)+"\t"+str(freq)+"\t"+str(temp)+"\n"
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

	return_string = str(time/len(trial_ex_time))+"\t"+str(edge/len(trial_results))+"\t"+str(level/len(trial_results))+"\t"+str(diameter/len(trial_results))+"\t"+str(aspl/len(trial_results))+"\t"+str(power/len(trial_results))+"\t"+str(freq/len(trial_results))+"\t"+str(temp/len(trial_results))+"\n"

	return return_string

def main():
	numchips = [9,12]
	candidates = 15
	candidate_trials = 1000
	add_by = ['cradle', '3', '2', '1']
	export_path = " -e results_LL/multiaddexp/figures/"
	raw_result_file = "results_LL/multiaddexp/2heu_raw_multichip_results.txt"
	avg_result_file = "results_LL/multiaddexp/2heu_avg_multichip_results.txt"
	#start = end = -1
	try:
		f = open(raw_result_file, "w+")
		header = "trial\tchips_added_at_a_time\texecution_time\tedges\tlevels\tdiameter\tASPL\tpower\tfrequency\ttempurature\n"
		f.write(header)
		f.close()
		g = open(avg_result_file, "w+")
		header = "chips_added_at_a_time\texecution_time\tedges\tlevels\tdiameter\tASPL\tpower\tfrequency\ttempurature\n"
		g.write(header)
		g.close()
		for num in numchips:
			for add in add_by:
				if num == add:
					continue
				trial_results = []
				trial_ex_time = []
				for trial in range(1,11):
					#add trials in after we run successfully
					command = "mpirun -np 8 ./optimize_layout.py --numchips "+str(num)+" --medium air --chip base3 --diameter "+str(num)+" --layout_scheme random_greedy:15:5000:"+str(add)+"  --numlevels 7 --powerdistopt uniform_discrete --powerdistopt_num_iterations 1 --powerdistopt_num_trials 1  --overlap .20 --max_allowed_temperature 50  --verbose 0 --mpi"+export_path+str(num)+"_chip_add_by_"+str(add)+"_trial_"+str(trial)+".pdf"
					
					print command
					#sys.stderr.write("Error: test command\n")
       					#sys.exit(1)
					start = time.time()
					devnull = open('/dev/null', 'w')
					proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, stderr=devnull)
					proc.wait()
					end = time.time()
					out = proc.stdout.read()
					#out, err = procs.communicate()
					out_str, out_val = parse_output(out)
					ex_time = float(end-start)
					trial_results.append(out_val)
					trial_ex_time.append(ex_time)
					raw_result = str(trial)+"\t"+str(add)+"\t"+str(ex_time)+"\t"+out_str
					f = open(raw_result_file, "a+")
					f.write(raw_result)
					f.close()
					print '  Trial ',trial, ' execution time is ',ex_time
				avg_string = get_avg_string(trial_results,trial_ex_time)
				avg_result = str(add)+"\t"+avg_string
				g = open(avg_result_file, "a+")
				g.write(avg_result)
				g.close()
			footer = "base3\nlayout_size = "+str(num)+"\ncandidates "+str(candidates)+"\n\n"
			g = open(avg_result_file, "a+")
			g.write(footer)
			g.close()
			print 'Done numchps ',num,' and add ', add

	except IOError:
		print "IOError!!!"
		sys.exit(1)

if __name__ == '__main__':
	main()
