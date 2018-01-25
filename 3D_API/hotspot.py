#!/usr/bin/python
import os
import sys
import subprocess

output_grid_size = 128
args = sys.argv

if ((len(args) != 3) and (len(args) != 4) and (len(args) != 5)):
	sys.stderr.write('Usage: ' + args[0] + ' <input file (.data)> <air|water|oil|fluori|novec> [--no_images][--detailed]\" \n')
	sys.exit(1)

input_file = args[1]
sorted_file = 'sorted.data'

if not os.access(input_file, os.R_OK):
	sys.stderr.write("Can't read file '"+input_file+"'\n")
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

subprocess.call("rm -f null.data", shell = True)
subprocess.call("rm -f sorted.data", shell = True)
#subprocess.call("cat " + input_file + " | sort -n -k2 > " +sorted_file, shell = True)
subprocess.call("cat " + input_file + " | nl | awk '{print $2,$3,$4,$5,$6,$7,$1}' | sort -n -k2 > " +sorted_file, shell = True)

f = open(sorted_file)
lines2 = f.readlines()
f.close

subprocess.call("rm -f tmp.grid.steady", shell = True)
subprocess.call("rm -f tmp.results", shell = True)
subprocess.call("touch tmp.results", shell = True) 
subprocess.call("rm -f figure/layer*.svg", shell = True)
subprocess.call("rm -f figure/layer*.pdf", shell = True)
subprocess.call("rm -f figure/layer*.png", shell = True)
layer = []

count = 0
for line in lines2:
	data = line[:-1].split(' ')
	layer += [int(data[1])]
	count += 1
layer_num = layer[len(layer)-1]
subprocess.call("make -s; ./cell " + sorted_file + " > null.data", shell = True)
subprocess.call("python floor.py " + sorted_file, shell = True)
subprocess.call("python ptrace.py " + sorted_file, shell = True)
subprocess.call("python lcf.py " + sorted_file, shell = True)
subprocess.call("python config.py " + sorted_file + " " + str(material), shell = True)
if args[2] == "water_pillow": ##when using water pillow, ignoring the second path.
	subprocess.call("../hotspot -f test1.flp -c test.config -p test.ptrace -model_type grid -model_secondary 0 -grid_steady_file tmp.grid.steady -detailed_3D on -grid_layer_file test.lcf", shell = True)
else:
	subprocess.call("../hotspot -f test1.flp -c test.config -p test.ptrace -model_type grid -model_secondary 1 -grid_steady_file tmp.grid.steady -detailed_3D on -grid_layer_file test.lcf", shell = True)
for i in xrange(0, layer_num):
	if args[2] == "water_pillow": ##the output would be changed whether the second path is used.  
		subprocess.call("cat tmp.grid.steady | sed -n "+ str(5+i*2*(output_grid_size*output_grid_size+2))+ "," +str(5+i*2*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p | sort -n -k2 | awk \'END{print $2-273.15}\' >> tmp.results", shell = True)
		subprocess.call("cat tmp.grid.steady | sed -n "+ str(5+i*2*(output_grid_size*output_grid_size+2))+ "," +str(5+i*2*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p > layer" + str(i+1) + ".grid.steady", shell = True)
	else:
		subprocess.call("cat tmp.grid.steady | sed -n "+ str(5+(3+i*2)*(output_grid_size*output_grid_size+2))+ "," +str(5+(3+i*2)*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p | sort -n -k2 | awk \'END{print $2-273.15}\' >> tmp.results", shell = True)
		subprocess.call("cat tmp.grid.steady | sed -n "+ str(5+(3+i*2)*(output_grid_size*output_grid_size+2))+ "," +str(5+(3+i*2)*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p > layer" + str(i+1) + ".grid.steady", shell = True)
	if (not no_images):
		subprocess.call("../orignal_thermal_map.pl test"+ str(i+1)+".flp layer" +str(i+1) + ".grid.steady > figure/layer" + str(i+1) + ".svg", shell = True)
		subprocess.call("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".pdf", shell = True)
		subprocess.call("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".png", shell = True)
if(detailed):
	subprocess.call("sort -n -k11 -u detailed.tmp -o detailed.tmp", shell = True)
	for i in xrange(0, count):	
		subprocess.call("python detailed.py detailed.tmp "+ str(i+1), shell = True)
		

#pick up the max temperature from max temperatures of each layers
temp = open('tmp.results').readline()
if '-273.15\n' == temp:
	sys.stderr.write("error occurred\n")
	sys.exit(1)
if (detailed):
	subprocess.call("cat tmp.results | sort -n | awk \'END{print \"maximum temp: \"$1}\'", shell = True)
else:
	subprocess.call("cat tmp.results | sort -n | awk \'END{print $1}\'", shell = True)
	
