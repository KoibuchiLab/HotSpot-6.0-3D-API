#!/usr/bin/python
import os
import sys

args = sys.argv
if len(args) == 1:
	sys.stderr.write('error: you need more args \"air or water or oil\" \n')
	sys.exit()
elif len(args) > 2:
	sys.stderr.write('error: you can use only args \"air or water or oil\" \n')
	sys.exit()
elif args[1] == "water":
	material = "water"
elif args[1] == "oil":
	material = "oil"
elif args[1] == "air":
	material = "air"
else:
	sys.stderr.write('error: you used invalid args, you can use \"air or water or oil\" \n')
	sys.exit()
 

	 

#os.system("rm -f tmp.grid.steady")
os.system("rm -f null.data")
os.system("cat test.data | sort -n -k2 > tmp")

f = open('tmp')
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
os.system("make; ./cell > null.data")
os.system("python floor.py")
os.system("python ptrace.py")
os.system("python lcf.py")
os.system("python config.py " +str(material))
os.system("../hotspot -f test1.flp -c test.config -p test.ptrace -model_type grid -use_secondary 1 -grid_steady_file tmp.grid.steady -detailed_3D on -grid_layer_file test.lcf")
for i in xrange(0, layer_num): 
	os.system("cat tmp.grid.steady | sed -n "+ str(5+i*4098*2)+ "," +str(5+i*4098*2+4095) +"p | sort -n -k2 | awk \'END{print $2-273.15}\' >> tmp.results")
	os.system("cat tmp.grid.steady | sed -n "+ str(5+i*4098*2)+ "," +str(5+i*4098*2+4095) +"p > layer" + str(i+1) + ".grid.steady")
	os.system("../orignal_thermal_map.pl test"+ str(i+1)+".flp layer" +str(i+1) + ".grid.steady > figure/layer" + str(i+1) + ".svg")
	os.system("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".pdf")
	os.system("convert -font Helvetica figure/layer" +str(i+1)+ ".svg figure/layer" +str(i+1) +".png")
	os.system("cat tmp.results | sort -n | awk \'END{print $1}\'")
