#!/usr/bin/python
import os
import sys
import operator
import itertools
import multiprocessing

import input_file
import nulldata_file
import floorplan
import floor
import ptrace
import lcf
import config

output_grid_size = 128
args = sys.argv

def compile_cell(pid):
	#print "gcc -Wall -Ofast cell.c -o cell"+str(pid)+" -s;"
	os.system("gcc -Wall -O3 -fopenmp -lm cell.c -o cell"+str(pid)+" -s;")

def call_cell(sorted_file, pid):
	#os.system("gcc -Wall -Ofast cell.c -o cell"+str(pid)+" -s; ./cell"+str(pid)+" " + sorted_file+" "+str(pid))
	#print "./cell"+str(pid)+" "+sorted_file+" "+str(pid)
	os.system("./cell"+str(pid)+" "+sorted_file+" "+str(pid)) #PID needs to get passed to cell to avoid competition for executibles

def call_hotspot(material, pid):
	if material == "water_pillow": ##when using water pillow, ignoring the second path.
		os.system("../hotspot -f test1_"+str(pid)+".flp -c test_"+str(pid)+".config -p test_"+str(pid)+".ptrace -model_type grid -model_secondary 0 -grid_steady_file tmp_"+str(pid)+".grid.steady -detailed_3D on -grid_layer_file test_"+str(pid)+".lcf")
	else:
		os.system("../hotspot -f test1_"+str(pid)+".flp -c test_"+str(pid)+".config -p test_"+str(pid)+".ptrace -model_type grid -model_secondary 1 -grid_steady_file tmp_"+str(pid)+".grid.steady -detailed_3D on -grid_layer_file test_"+str(pid)+".lcf")



if ((len(args) != 3) and (len(args) != 4) and (len(args) != 5)):
	sys.stderr.write('Usage: ' + args[0] + ' <input file (.data)> <air|water|oil|fluori|novec> [--no_images][--detailed]\" \n')
	sys.exit(1)

test_file = args[1]
#sorted_file = 'sorted.data'

if not os.access(test_file, os.R_OK):
	sys.stderr.write("Can't read file '"+test_file+"'\n")
	sys.exit(1)

if args[2] == "water":
	material = "water"
elif args[2] == "oil":
	material = "oil"
elif args[2] == "air":
	material = "air"
elif args[2] == "fluori":
	material = "fluori"
elif args[2] == "novec":
	material = "novec"
elif args[2] == "water_pillow":
	material = "water_pillow"
else:
	sys.stderr.write('Invalid medium argument. Should be [air|water|oil|fluori|novec]\" \n')
	sys.exit(1)

no_images = False
detailed = False
if (len(args) == 4):
	if (args[3] == "--no_images"):
		no_images = True
	elif (args[3] == "--detailed"):
		detailed = True
	else:
	 	sys.stderr.write("Invalid argument '" + args[3] +"'\n")
		sys.exit(1)

if (len(args) == 5):
	if ((args[3] == "--no_images" and args[4] == "--detailed") or (args[3] == "--detailed" and args[4] == "--no_images")):
		no_images = True
		detailed = True
	else:
	 	sys.stderr.write("Invalid argument '" + args[3] + args[4]+"'\n")
		sys.exit(1)
try:
	pid = os.getpid()
	input = input_file.input_file(test_file, pid)
	sorted_input = input.get_sorted_file()
	sorted_file=input.sorted_to_file(pid)
	layer = input.get_layer_array()

	#compiles cell
	compile_cell(pid)

	#call cell to, makes nulldata file
	call_cell(sorted_file, pid)

	#creates object to store whats in null data
	null_data = nulldata_file.nulldata_file('null_'+str(pid)+'.data') #dont hardcode name?

	#creates *.flp files for hotspot.c
	floor.floor(sorted_input, null_data, pid)	#may have to fix to pass whole object

	#creates *.ptrace file for hotspot.c
	ptrace.ptrace(input, null_data, pid)

	#creates *.lcf files for hotspot.c
	lcf.lcf(input, pid)

	#creates *.config and *TIM.flp for hotspot.c
	config.config(input, str(material), pid)

	#calls hotspot.c
	call_hotspot(material, pid)

	results_file = open("tmp_"+str(pid)+".results","w")
	results_list = []
	for i in xrange(0, layer[-1]):
		if material == "water_pillow": #the output would be changed when the second path is used.
			#needs to be tested. bug in config.py prevented full testing.
			with open("tmp_"+str(pid)+".grid.steady", "r") as tmp_grid_steady:
				write_to_layer = ""
				for record in itertools.islice(tmp_grid_steady, (5+i*2*(output_grid_size*output_grid_size+2)-1), (5+i*2*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1))):
					write_to_layer+=record
					record = record.strip(" \n")
					record = record.replace("\t"," ")
					record = record.split(' ')
					#print str(record[1])
					temps.append(str(record[1]))	#float?
				#print str(i)+" iteration \n"+str(temps)
				results_file.write(str(float(max(temps))-273.15)+"\n")
				layer_name = "layer"+str(i+1)+"_"+str(pid)+".grid.steady"
				layer_grid_steady = open(layer_name,"w")
				layer_grid_steady.write(write_to_layer)
				layer_grid_steady.close()
			tmp_grid_steady.close()

		else:
			temps = []
			with open("tmp_"+str(pid)+".grid.steady", "r") as tmp_grid_steady:
				write_to_layer = ""

				read_start = (5+(3+i*2)*(output_grid_size*output_grid_size+2)-1)
				read_end = (5+(3+i*2)*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1))

				for record in itertools.islice(tmp_grid_steady, read_start, read_end):
					write_to_layer+=record
					record = record.strip(" \n")
					record = record.replace("\t"," ")
					record = record.split(' ')
					temps.append(str(record[1]))	#float?
				maxTemp = str(float(max(temps))-273.15)
				results_file.write(str(maxTemp+"\n"))
				results_list.append((maxTemp))	#for check at bottom
				layer_name = "layer"+str(i+1)+"_"+str(pid)+".grid.steady"
				layer_grid_steady = open(layer_name,"w")
				layer_grid_steady.write(write_to_layer)
				layer_grid_steady.close()
			tmp_grid_steady.close()
		if (not no_images):
			os.system("../orignal_thermal_map.pl test"+ str(i+1)+".flp layer" +str(i+1) + ".grid.steady > figure/layer" + str(i+1) + ".svg")
			os.system("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".pdf")
			os.system("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".png")

	results_file.close()
	if(detailed):
		os.system("sort -n -k11 -u detailed.tmp -o detailed.tmp")
		for i in xrange(0, len(layer)):
			os.system("python detailed.py detailed.tmp "+ str(i+1))

	temp = open("tmp_"+str(pid)+".results").readline()
	if (float(min(results_list)))<0:
		sys.stderr.write("error occurred\n")
		sys.exit(1)

	if (detailed):
		print "maximum temp: "+str(max(results_list))
	else:
		print str(max(results_list))

except IOError:
	print '\nKeyboardInterrupt, Removing temp files containing pid = ',pid
	results_file.close()
	os.system("rm -f *"+str(pid)+"*")
	print '********EXITING HOTSPOT********'
	sys.exit(1)

#clean up
os.system("rm -f *"+str(pid)+"*")
