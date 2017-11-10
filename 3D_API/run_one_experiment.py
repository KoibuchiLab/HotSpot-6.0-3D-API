#!/usr/bin/python 
import os 
import sys 
import subprocess 
import random 

def append_to_file(filename, message):
    f =open(filename, "a+")
    f.write(message + "\n")
    f.close()


def run_experiment(n, medium, diameter, scheme, num_levels, overlap, power_dist_opt): 
	command_line = "" 
	command_line += "./optimize_layout.py" 
	command_line += " --numchips " + str(n) 
	command_line += " --medium " + medium 
	command_line += " --chip base2" 
	command_line += " --diameter " + str(diameter)
	command_line += " --layout_scheme " + scheme
	command_line += " --numlevels " + str(num_levels)
	command_line += " --powerdistopt " + power_dist_opt
	command_line += " --powerdistopt_num_iterations 1"
	command_line += " --powerdistopt_num_trials 5"
	command_line += " --overlap " + str(overlap)
	command_line += " --max_allowed_temperature 58"
	command_line += " --verbose 3"


	results = {}
	results["scheme"] = scheme
	results["num_levels"] = int(num_levels)
	results["overlap"] = float(overlap)
	results["num_chips"] = float(n)
	results["medium"] = medium

        print "----> ", command_line

	try:
		with open(os.devnull, 'w') as devnull:
			output = subprocess.check_output(command_line, stdin=None, stderr=None, shell=True)
	except subprocess.CalledProcessError as e:
		results["outcome"] = "FAILED"
		return results

        print "--> results=", results

	lines = output.split('\n')
	output_headers = [("Number of edges = ", "num_edges"), ("Diameter = ", "diameter"), ("ASPL = ", "ASPL"), ("Power budget = ", "power"), ("Temperature = ", "temperature"), ("Frequency distribution = ", "frequencies"), ("Number of levels = ", "num_levels"), ("Layout = ", "chip_positions"), ("Topology =", "topology")]
	for line in lines:
		for (output_header, key) in output_headers:
			if (len(line.split(output_header)) == 2):
				results[key] = line.split(output_header)[1]

	results["diameter"] = int(results["diameter"])
	results["outcome"] = "SUCCESS"
	results["num_edges"] = int(results["num_edges"])
	results["ASPL"] = float(results["ASPL"])
	results["power"] = float(results["power"])
	results["temperature"] = float(results["temperature"])
#	results["frequencies"] = float(results["frequencies"].split("[")[1].split(",")[0])

	return results
	
	
if __name__ == '__main__':

	args = sys.argv
	
	if (len(args) != 10):
        	sys.stderr.write('Usage: ' + args[0] + ' <# of chips> <scheme> <medium> <diameter> <overlap> <num_levels> <repeats> <powerdist_opt> <output file>\n');
        	sys.exit(1)

	num_chips = int(args[1])
	scheme = args[2]
        medium = args[3]
	diameter = int(args[4])
        overlap = float(args[5])
	num_levels = int(args[6])
        repeats = int(args[7])
	power_dist_opt = args[8]
        output_file = args[9]

	for repeat in xrange(0, repeats):
       		result = run_experiment(num_chips, medium, diameter, scheme, num_levels, overlap, power_dist_opt)
      		append_to_file(output_file, str(result) + "\n")
		    

