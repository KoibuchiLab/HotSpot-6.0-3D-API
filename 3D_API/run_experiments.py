#!/usr/bin/python 
import os 
import sys 
import subprocess 
import random 

def run_experiment(n, medium, diameter, scheme, num_levels, overlap): 
	command_line = "" 
	command_line += "./optimize_layout.py" 
	command_line += " --numchips " + str(n) 
	command_line += " --medium " + medium 
	command_line += " --chip base2" 
	command_line += " --diameter " + str(diameter)
	command_line += " --layout_scheme " + scheme
	command_line += " --numlevels " + str(num_levels)
	command_line += " --powerdistopt uniform_discrete"
	command_line += " --powerdistopt_num_iterations 1"
	command_line += " --powerdistopt_num_trials 5"
	command_line += " --overlap " + str(overlap)
	command_line += " --max_allowed_temperature 58"


	results = {}
	results["scheme"] = scheme
	results["num_levels"] = int(num_levels)
	results["overlap"] = float(overlap)
	results["num_chips"] = float(n)

        #print "----> ", command_line

	try:
		with open(os.devnull, 'w') as devnull:
			output = subprocess.check_output(command_line, stdin=None, stderr=None, shell=True)
	except subprocess.CalledProcessError as e:
		results["outcome"] = "FAILED"
                print "RETURNIN ", results
		return results

        print "--> NO EXCEPTION: results=", results

	lines = output.split('\n')
	output_headers = [("Number of edges = ", "num_edges"), ("Diameter = ", "diameter"), ("ASPL = ", "ASPL"), ("Power budget = ", "power"), ("Temperature = ", "temperature"), ("Frequency distribution = ", "frequencies"), ("Number of levels = ", "num_levels")]
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
	results["frequencies"] = float(results["frequencies"].split("[")[1].split(",")[0])

	return results
	

	
if __name__ == '__main__':

	args = sys.argv
	
	if (len(args) != 4):
        	sys.stderr.write('Usage: ' + args[0] + ' <# of chips> <# of trials> <max # of trials>\n');
        	sys.exit(1)

	num_chips = int(args[1])
	num_trials = int(args[2])
	max_num_trials = int(args[3])


	medium = "air"
	#overlaps = [1.0/float(x) for x in [9, 8, 7, 6, 5, 4]]
	overlaps = [1.0/9.0]

	for overlap in overlaps:
		print "* OVERLAP = ", overlap
		result = run_experiment(num_chips,  medium, 2, "checkerboard", 2, overlap);
		print "    ", result
                checkboard_diameter = -1
                if (result["outcome"] == "SUCCESS"):
                    checkerboard_diameter = results["diameter"]

		result = run_experiment(num_chips,  medium, 2, "checkerboard", 3, overlap);
		print "    ", result
                if (result["outcome"] == "SUCCESS"):
                    checkerboard_diameter = max(checkboard_diameter, result["diameter"])

                if (checkerboard_diameter < 0):
                        print "Checkerboards have failed... not sure what diameter to use"
                        sys.exit(1)

                for diameter in [checkerboard_diameter]:
			print "  * DIAMETER = ", diameter 
			for num_levels in [2,3,4,5]:
				print "    * NUM_LEVELS = ", num_levels 
                                result = run_experiment(num_chips,  medium, diameter, "random_greedy:"+str(num_trials)+":"+str(max_num_trials), num_levels, overlap);
				print "      ", result
		

