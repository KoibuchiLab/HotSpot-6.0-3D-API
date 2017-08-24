#!/usr/bin/python
import os
import sys


args = sys.argv

if ((len(args) != 3) and (len(args) != 4)):
	sys.stderr.write('Usage: ' + args[0] + ' <input file (.data)> <air|water|oil> [--no_images]\" \n')
	sys.exit(1)

input_file = args[1]
sorted_file = 'sorted_data'

if not os.access(input_file, os.R_OK):
	sys.stderr.write("Can't read file '"+input_file+"'\n")
	sys.exit(1)

if args[2] == "water":
	material = "water"
elif args[2] == "oil":
	material = "oil"
elif args[2] == "air":
	material = "air"
else:
	sys.stderr.write('Invalid medium argument. Should be [air|water|oil]\" \n')
	sys.exit(1)
 
no_images = False
if (len(args) == 4):
	if (args[3] == "--no_images"):
		no_images = True
	else:
	 	sys.stderr.write("Invalid argument '" + args[3] +"'\n")
		sys.exit(1)


#os.system("rm -f tmp.grid.steady")
os.system("rm -f null.data")
os.system("rm -f sorted.data")
os.system("cat " + input_file + " | sort -n -k2 > " +sorted_file)

f = open(sorted_file)
lines2 = f.readlines()
f.close

os.system("rm -f tmp.results")
os.system("touch tmp.results") 
os.system("rm -f figure/layer*.svg")
os.system("rm -f figure/layer*.pdf")
os.system("rm -f figure/layer*.png")
layer = []

for line in lines2:
	data = line[:-1].split(' ')
	layer += [int(data[1])]
layer_num = layer[len(layer)-1]
os.system("make -s; ./cell " + sorted_file + " > null.data")
os.system("python floor.py " + sorted_file)
os.system("python ptrace.py " + sorted_file)
os.system("python lcf.py " + sorted_file)
os.system("python config.py " + sorted_file + " " + str(material))
os.system("../hotspot -f test1.flp -c test.config -p test.ptrace -model_type grid -use_secondary 1 -grid_steady_file tmp.grid.steady -detailed_3D on -grid_layer_file test.lcf")
for i in xrange(0, layer_num): 
	os.system("cat tmp.grid.steady | sed -n "+ str(5+i*4098*2)+ "," +str(5+i*4098*2+4095) +"p | sort -n -k2 | awk \'END{print $2-273.15}\' >> tmp.results")
	os.system("cat tmp.grid.steady | sed -n "+ str(5+i*4098*2)+ "," +str(5+i*4098*2+4095) +"p > layer" + str(i+1) + ".grid.steady")
	if (not no_images):
		os.system("../orignal_thermal_map.pl test"+ str(i+1)+".flp layer" +str(i+1) + ".grid.steady > figure/layer" + str(i+1) + ".svg")
		os.system("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".pdf")
		os.system("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".png")

#pick up the max temperature form max temperature of each layers
os.system("cat tmp.results | sort -n | awk \'END{print $1}\'")
