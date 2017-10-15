#!/usr/bin/python
import os
import sys
import operator
import input_file
import null_data_file
import floorplan_LL
import floor_LL
import ptrace_LL
import lcf_LL

output_grid_size = 64
args = sys.argv

if ((len(args) != 3) and (len(args) != 4) and (len(args) != 5)):
	sys.stderr.write('Usage: ' + args[0] + ' <input file (.data)> <air|water|oil|fluori|novec> [--no_images][--detailed]\" \n')
	sys.exit(1)

test_file = args[1]
#print "input file is "+test_file
sorted_file = 'sorted.data'

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
"""
#os.system("rm -f null.data")
#os.system("rm -f sorted.data")
#os.system("cat " + input_file + " | sort -n -k2 > " +sorted_file)
os.system("cat " + input_file + " | nl | awk '{print $2,$3,$4,$5,$6,$7,$1}' | sort -n -k2 > " +sorted_file)
#print "cat " + input_file + " | nl | awk '{print $2,$3,$4,$5,$6,$7,$1}' | sort -n -k2 > " +sorted_file

read = open(input_file)
input_object = read.readlines()
read.close

line_number = 1
to_sort = []
for line in input_object:
	#print "input line is "+ str(line)
	line = line[:-1].split(' ')
	#print "after line split "+str(line)
	line.append(line_number)
	line_number += 1
	to_sort.append(tuple(line))
	
sorted_input = sorted(to_sort, key=operator.itemgetter(1,0))

layer = []
for tup in sorted_input:
	layer += [int(tup[1])]
layer_num =layer[-1]
#print "layer[-1] is "+ str(layer[-1])

print "new_layer: %s\n" % layer
print "new_layer_num: %s\n" % layer_num
print "new_layer count: %s\n" % len(layer)


f = open(sorted_file)
lines2 = f.readlines()#store in array? may not need file
#print "lines2 = %s" % lines2
f.close
#os.system("rm -f tmp.grid.steady")
#os.system("rm -f tmp.results")
os.system("touch tmp.results") 
#os.system("rm -f figure/layer*.svg")
#os.system("rm -f figure/layer*.pdf")
#os.system("rm -f figure/layer*.png")
layer = []

count = 0
for line in lines2:
	data = line[:-1].split(' ')
	print "data is %s\n" % data
	print "data[1] is %s\n" % data[1]
	layer += [int(data[1])]
	count += 1
print "count is : %d \n" % count
print "sorted input lenght: %d\n" % len(sorted_input)
print "layer is %s" % layer
print "layer[len(layer)-1] is %s" % layer[len(layer)-1]
print "layer[-1] is %s" % layer[-1]
layer_num = layer[-1]
print "layer_num is %s" % layer_num
"""

input = input_file.input_file(test_file)
sorted_input = input.get_sorted_file()
input.sorted_to_file()
layer = input.get_layer_array()

#os.system("make -s; ./cell_LL " + sorted_file + " > null1.data")
#os.system("gcc -Wall -O3 cell_LL.c -o cell_LL -s; ./cell_LL " + sorted_file) #make called before running per README

null_data = null_data_file.null_data_file('null.data') #dont hardcode name

floor_LL.floor(sorted_input, null_data)
ptrace_LL.ptrace(input, null_data)
lcf_LL.lcf(input)

"""
#old calls
#os.system("python floor.py " + sorted_file) #null.data called in here
#os.system("python ptrace.py " + sorted_file)
os.system("python lcf.py " + sorted_file)
"""

os.system("python config.py " + sorted_file + " " + str(material))

if args[2] == "water_pillow": ##when using water pillow, ignoring the second path.
	os.system("../hotspot -f test1_LL.flp -c test.config -p test_LL.ptrace -model_type grid -model_secondary 0 -grid_steady_file tmp.grid.steady -detailed_3D on -grid_layer_file test_LL.lcf")
else:
	os.system("../hotspot -f test1_LL.flp -c test.config -p test_LL.ptrace -model_type grid -model_secondary 1 -grid_steady_file tmp.grid.steady -detailed_3D on -grid_layer_file test_LL.lcf")
for i in xrange(0, layer[-1]):
	if args[2] == "water_pillow": ##the output would be changed whether the second path is used.  
		os.system("cat tmp.grid.steady | sed -n "+ str(5+i*2*(output_grid_size*output_grid_size+2))+ "," +str(5+i*2*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p | sort -n -k2 | awk \'END{print $2-273.15}\' >> tmp.results")
		os.system("cat tmp.grid.steady | sed -n "+ str(5+i*2*(output_grid_size*output_grid_size+2))+ "," +str(5+i*2*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p > layer" + str(i+1) + ".grid.steady")
	else:
		os.system("cat tmp.grid.steady | sed -n "+ str(5+(3+i*2)*(output_grid_size*output_grid_size+2))+ "," +str(5+(3+i*2)*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p | sort -n -k2 | awk \'END{print $2-273.15}\' >> tmp.results")
		os.system("cat tmp.grid.steady | sed -n "+ str(5+(3+i*2)*(output_grid_size*output_grid_size+2))+ "," +str(5+(3+i*2)*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p > layer" + str(i+1) + ".grid.steady")
	if (not no_images):
		os.system("../orignal_thermal_map.pl test"+ str(i+1)+".flp layer" +str(i+1) + ".grid.steady > figure/layer" + str(i+1) + ".svg")
		os.system("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".pdf")
		os.system("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".png")
if(detailed):
	os.system("sort -n -k11 -u detailed.tmp -o detailed.tmp")
	for i in xrange(0, len(layer)):	
		os.system("python detailed.py detailed.tmp "+ str(i+1))
		

#pick up the max temperature from max temperatures of each layers
temp = open('tmp.results').readline()
if '-273.15\n' == temp:
	sys.stderr.write("error occurred\n")
	sys.exit(1)
if (detailed):
	os.system("cat tmp.results | sort -n | awk \'END{print \"maximum temp: \"$1}\'")
else:
	os.system("cat tmp.results | sort -n | awk \'END{print $1}\'")
	
