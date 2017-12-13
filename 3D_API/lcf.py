#!/usr/bin/python
import os
import sys

thickness_of_chip = 0.00004 ## (meter)  default:40um
vertical_distance_between_chips = '1.0e-5' ## (meter) default:10um



if (len(sys.argv) != 2):
        sys.stderr.write("Usage: " + sys.argv[0] + " <input file (.dat)>\n")
        sys.exit(1)

input_file = sys.argv[1]
if not os.access(input_file, os.R_OK):
        sys.stderr.write("Can't read file '"+input_file+"'\n")
        sys.exit(1)


f = open(input_file)
chip_data = f.readlines()
f.close

os.system("rm -f test.lcf")
os.system("touch test.lcf") 


layer = []
for line in chip_data:
	data = line[:-1].split(' ')
	layer += [int(data[1])]

layer_num = layer[len(layer)-1]

for i in xrange(0, layer_num):
	os.system("echo  \"" +str(2*i)+"\"  >> test.lcf")
	os.system("echo  \"Y\nY\n1.75e6\n0.01\n"+str(thickness_of_chip)+"\"  >> test.lcf")  # default chip config data 
	os.system("echo  \"test" +str(i+1)+".flp\n\"  >> test.lcf")
	os.system("echo  \"" +str(2*i+1)+"\"  >> test.lcf")
	os.system("echo  \"Y\nN\n4e6\n0.25\n"+str(vertical_distance_between_chips)+"\"  >> test.lcf")  # default tim config data 
	os.system("echo  \"testTIM.flp\n\"  >> test.lcf")

	


