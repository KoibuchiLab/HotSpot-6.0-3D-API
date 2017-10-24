#!/usr/bin/python 
import os 
import sys 
import subprocess 
import random 

def append_to_file(filename, message):
    f =open(filename, "a+")
    f.write(message + "\n")
    f.close()


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

        print "----> ", command_line

	try:
		with open(os.devnull, 'w') as devnull:
			output = subprocess.check_output(command_line, stdin=None, stderr=None, shell=True)
	except subprocess.CalledProcessError as e:
		results["outcome"] = "FAILED"
		return results

        print "--> results=", results

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
	
	if (len(args) != 6):
        	sys.stderr.write('Usage: ' + args[0] + ' <# of chips> <# of heuristic runs> <# of chip addition trials> <max # of chip addition trials before giving up> <output file>\n');
        	sys.exit(1)

	num_chips = int(args[1])
        num_runs = int(args[2])
	num_trials = int(args[3])
	max_num_trials = int(args[4])
        output_file = args[5]

	mediums = ["air", "oil", "water"]

	overlaps = [1.0/float(x) for x in [9, 8, 7, 6, 5, 4]]
	#overlaps = [1.0/9.0]

        for medium in mediums:
            append_to_file(output_file, "* MEDIUM = " +  medium)
	    for overlap in overlaps:
		    append_to_file(output_file, "  * OVERLAP = "+ str(overlap))
		    result = run_experiment(num_chips,  medium, 2, "checkerboard", 2, overlap);
		    append_to_file(output_file, "   CHECKBOARD-2: "+ str(result))
                    checkerboard_diameters = []
                    if (result["outcome"] == "SUCCESS"):
                        checkerboard_diameters.append(result["diameter"])
    
		    result = run_experiment(num_chips,  medium, 2, "checkerboard", 3, overlap);
                    append_to_file(output_file, "   CHECKBOARD-3: " +  str(result))
                    if (result["outcome"] == "SUCCESS"):
                        checkerboard_diameters.append(result["diameter"])
    
                    if (len(checkerboard_diameters) == 0):
                            append_to_file(output_file, "Checkerboards have failed... not sure what diameter to use")
                            continue
    
                    for diameter in checkerboard_diameters:
			    append_to_file(output_file, "  * DIAMETER = " + str(diameter))
			    for num_levels in [2,3,4,5,6]:
				    append_to_file(output_file, "    * NUM_LEVELS = "+ str(num_levels))
                                    for iter in xrange(0, num_runs):
                                        result = run_experiment(num_chips,  medium, diameter, "random_greedy:"+str(num_trials)+":"+str(max_num_trials), num_levels, overlap);
                                        append_to_file(output_file, "      HEURISTIC RUN # ", str(iter), ":" +  str(result))
		    

