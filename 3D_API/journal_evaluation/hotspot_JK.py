#!/usr/bin/python
import os
import sys
import time

output_grid_size = 128
args = sys.argv

if ((len(args) != 3) and (len(args) != 4) and (len(args) != 5)):
	sys.stderr.write('Usage: ' + args[0] + ' <input file (.data)> <air|water|oil|fluori|novec> [--no_images][--detailed]\" \n')
	sys.exit(1)

input_file = args[1]
#sorted_file = 'sorted.data'

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
#if (len(args) == 4):
#	if (args[3] == "--no_images"):
#		no_images = True
#	elif (args[3] == "--detailed"):
#		detailed = True
#	else:
#	 	sys.stderr.write("Invalid argument '" + args[3] +"'\n")
#		sys.exit(1)
#
#if (len(args) == 5):
#	if ((args[3] == "--no_images" and args[4] == "--detailed") or (args[3] == "--detailed" and args[4] == "--no_images")):
no_images = False ## True or False
#		detailed = True
#	else:
#	 	sys.stderr.write("Invalid argument '" + args[3] + args[4]+"'\n")
#		sys.exit(1)

count = args[4]

os.system("rm -f null"+str(count)+".data")
os.system("rm -f sorted"+str(count)+".data")
os.system("cat " + input_file + " | sort -n -k2 > sorted"+str(count)+".data")
os.system("cat " + input_file + " | nl | awk '{print $2,$3,$4,$5,$6,$7,$1}' | sort -n -k2 > sorted" + str(count)+".data")

f = open("sorted"+str(count)+".data")
lines2 = f.readlines()
f.close

sorted_file = "sorted"+str(count)+".data"

os.system("rm -f tmp.grid.steady"+str(count))
os.system("rm -f tmp.results"+str(count))
os.system("touch tmp.results"+str(count))
#os.system("rm -f figure/layer*.svg")
#os.system("rm -f figure/layer*.pdf")
#os.system("rm -f figure/layer*.png")
layer = []

counta = 0
for line in lines2:
	data = line[:-1].split(' ')
	layer += [int(data[1])]
	counta += 1
layer_num = layer[len(layer)-1]
#os.system("make -s; ./cell " + sorted_file + " > null.data")
os.system("./cell " + sorted_file + " > null"+str(count)+".data")
os.system("python floor_JK.py " + sorted_file +" " +str(count))
os.system("python ptrace_JK.py " + sorted_file +" " +str(count) )
os.system("python lcf_JK.py " + sorted_file +" "+str(count))
os.system("python config_JK.py " + sorted_file + " " + str(material) +" "+ str(count))
#if args[2] == "water_pillow": ##when using water pillow, ignoring the second path.
#	os.system("../../hotspot -f test1.flp -c test.config -p test.ptrace -model_type grid -model_secondary 0 -grid_steady_file tmp.grid.steady -detailed_3D on -grid_layer_file test.lcf")
#else:
start = time.time()
os.system("../../hotspot -f default.flp -c "+str(count)+"test.config -p "+str(count)+"test.ptrace -model_type grid -model_secondary 1 -grid_steady_file tmp.grid.steady"+str(count)+" -detailed_3D on -grid_layer_file "+str(count)+"test.lcf")
end_time = time.time() - start
#print ""
#print "orignal_time",count, end_time
for i in xrange(0, layer_num):
#	if args[2] == "water_pillow": ##the output would be changed whether the second path is used.
#		os.system("cat tmp.grid.steady | sed -n "+ str(5+i*2*(output_grid_size*output_grid_size+2))+ "," +str(5+i*2*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p | sort -n -k2 | awk \'END{print $2-273.15}\' >> tmp.results")
#		os.system("cat tmp.grid.steady | sed -n "+ str(5+i*2*(output_grid_size*output_grid_size+2))+ "," +str(5+i*2*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p > layer" + str(i+1) + ".grid.steady")
#	else:
	os.system("cat tmp.grid.steady"+str(count)+" | sed -n "+ str(5+(3+i*2)*(output_grid_size*output_grid_size+2))+ "," +str(5+(3+i*2)*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p | sort -n -k2 | awk \'END{print $2-273.15}\' >> tmp.results"+str(count))
#		os.system("cat tmp.grid.steady"+str(count)+" | sed -n "+ str(5+(3+i*2)*(output_grid_size*output_grid_size+2))+ "," +str(5+(3+i*2)*(output_grid_size*output_grid_size+2)+(output_grid_size*output_grid_size-1)) +"p > layer" + str(i+1) + ".grid.steady")
#	if (not no_images):
#		os.system("../../orignal_thermal_map.pl test"+ str(i+1)+".flp layer" +str(i+1) + ".grid.steady > figure/layer" + str(i+1) + ".svg")
#		os.system("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".pdf")
#		os.system("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".png")
#if(detailed):
#	os.system("sort -n -k11 -u detailed.tmp -o detailed.tmp")
#	for i in xrange(0, count):
#		os.system("python detailed.py detailed.tmp "+ str(i+1))


#pick up the max temperature from max temperatures of each layers
temp = open("tmp.results"+str(count)).readline()
if '-273.15\n' == temp:
	sys.stderr.write("error occurred\n")
	sys.exit(1)
#if (detailed):
#	os.system("cat tmp.results | sort -n | awk \'END{print \"maximum temp: \"$1}\'")
else:
	os.system("cat tmp.results"+str(count)+" | sort -n | awk \'END{print $1}\'")
