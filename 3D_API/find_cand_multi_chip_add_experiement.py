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
	numchips = [21]
	#candidates = workers*2
	candidate_trials = 100000
	overlaps = [.2,.1]
	#overlaps = [.1, .2]
	add_by = ['1','cradle','2','3']
	#add_by = [ '3', '2', '1','cradle']
	pickby = ['power']
	#can_range = [-2,-1,0,1,2]
	can_range = [0]

	export_path = " -e LL/results_LLfigures/"
	file_name = "21chip_heu"
	raw_result_file = "LL/results_LL/"+file_name+"_raw.txt"
	avg_result_file = "LL/results_LL/"+file_name+"_avg.txt"
	raw_output_file = "LL/results_LL/"+file_name+"_output.txt"
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
						#if num == add:
							#continue
						trial_results = []
						trial_ex_time = []
						candidates = workers*2
						#candiates must be > 4 for candidate range -2 to +2
						if num == 6 and overlap == .1:
							if '3' in add:
								continue
								candidates = 38
								#candidates = 23
							elif '2' in add:
								continue
								candidates = 19
								#candidates = 17
							elif '1' in add:
								continue
								candidates = 12
							elif 'cradle' in add:
								candidates = 47 
								#candidates = 25
						elif num == 6 and overlap ==.2:
							if '3' in add:
								continue
								candidates = 32
							elif '2' in add:
								continue
								candidates = 15
							elif '1' in add:
								continue
								candidates = 11
							elif 'cradle' in add:
								#candidates = 20
								candidates = 47
	
						if num == 9 and overlap == .1:
							if '3' in add:
								candidates = 43
								#candidates = 23
							elif '2' in add:
								#candidates = 22
								candidates = 28
							elif '1' in add:
								candidates = 17
							elif 'cradle' in add:
								candidates = 63
								#candidates = 25
						elif num == 9 and overlap ==.2:
							if '3' in add:
								candidates = 24
							elif '2' in add:
								continue
								candidates = 14
							elif '1' in add:
								continue
								candidates = 9
							elif 'cradle' in add:
								#candidates = 20
								candidates = 34
						#candidates = 14
						original_can = candidates
						avg_ex_time = -1
						for can in can_range:
							"""
							if num  == 6 and avg_ex_time > 300:  #TODO: time in sec, dont hard code this
								print '!!!avg_exe time too long, skipping candidate num = ', can,' for numchips = ',num
								continue
							if num == 9 and avg_ex_time > 1200:  #TODO: time in sec, dont hard code this
								print '!!!avg_exe time too long, skipping candidate num = ', can,' for numchips = ',num
								continue
							"""
							for trial in range(1,11):
								print '+++ candidate=',original_can,' num chip=',num,' overlap=',overlap,' add by=',add,' +++'
								#candidates = 14
								candidates = original_can + can
								print '=== candidate plus range=',can,' is ',candidates,' ==='
								#add trials in after we run successfully
								command = "mpirun -np "+str(7+1)+" ./optimize_layout.py --numchips "+str(num)+" --medium air --chip base3 --diameter "+str(num)+" --layout_scheme random_greedy:"+str(candidates)+":50000:"+str(add)+"  --numlevels 7 --powerdistopt uniform_discrete --powerdistopt_num_iterations 1 --powerdistopt_num_trials 1  --overlap "+str(overlap)+" --max_allowed_temperature 50  --verbose 0 -P "+str(pick)+" --mpi"#+export_path+str(num)+"_chip_add_by_"+str(add)+"_trial_"+str(trial)+".pdf"

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
								print '  Trial ',trial, ' execution time is ',ex_time
							avg_string = get_avg_string(trial_results,trial_ex_time)
							avg_result = str(add)+"\t"+avg_string+"\t"+str(pick)+"\t"+str(overlap)+"\t"+str(num)+"\t"+str(candidates)+"\n"
							g = open(avg_result_file, "a+")
							g.write(avg_result)
							g.close()
							split_avg_string = re.split(r'\t',avg_string)
							avg_ex_time = float(split_avg_string[0])
							print '\n>>>>>>> avg ex time is ',avg_ex_time,' <<<<<<<<<<<<\n'
#						footer = "base3\nlayout_size = "+str(num)+"\ncandidates "+str(candidates)+"\n\n"
#						g = open(avg_result_file, "a+")
#						g.write(footer)
#						g.close()
						print 'Done numchps ',num,' and add ', add

	except IOError:
		print "IOError!!!"
		sys.exit(1)

if __name__ == '__main__':
	main()
