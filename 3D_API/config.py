#!/usr/bin/python
import os
import sys

args = sys.argv


tulsa_x = 0.02184 #default tulsa chip size
tulsa_y = 0.02184

phi7250_x = 0.0315 #default phi7250 chip size 
phi7250_y = 0.0205

e52667v4_x = 0.012634 #default e5-2676v4 chip size
e52667v4_y = 0.014172 

AIR_H = 13 # W/(m^2 K)  Heat Transffer Coefficient of AIR 
OIL_H = 160 # W/(m^2 K) Heat Transffer Coefficient of OIL
WATER_H = 800 # W/(m^2 K) Heat Transffer Coefficient of WATER

if (len(args) != 3):
	sys.stderr.write("Usage: " + args[0] + " <input file (.dat)> <water | air | oil>\n")
	sys.exit(1)
	
if args[2] == "water":
	H_TRANS = WATER_H
elif args[2] == "air":
	H_TRANS = AIR_H
elif args[2] == "oil":
	H_TRANS = OIL_H
else:
	sys.stderr.write("Invalid argument '" + args[2] + "'\n")
	sys.exit(1)

input_file = args[1]
if not os.access(input_file, os.R_OK):
	sys.stderr.write("Can't read file '"+input_file+"'\n")
	sys.exit(1)


os.system("rm -f tmp")
os.system("cat " + input_file + " | sort -n -k2 > tmp")

f = open('tmp')
chip_lines = f.readlines()
f.close

os.system("rm -f test.config")
os.system("rm -f testTIM.flp")


layer_tmp = 0;
count_tmp = 0;

lay, count, rotate = [], [], []
chip_x, chip_y = [], []
x, y = [], []

for line in chip_lines:
	data = line[:-1].split(' ')
	chip_name = str(data[0])

	if chip_name == 'tulsa':
		chip_x += [float (tulsa_x)]
		chip_y += [float (tulsa_y)]
	elif chip_name == 'phi7250':
		chip_x += [float (phi7250_x)]
		chip_y += [float (phi7250_y)]
	elif chip_name == 'e5-2667v4':
		chip_x += [float (e52667v4_x)]
		chip_y += [float (e52667v4_y)]
	else:
		sys.stderr('invalid chip name in input file ' + input_file)
		sys.exit()

	lay += [int(data[1])]
	rotate += [int(data[5])]
	x += [float(data[2])]
	y += [float(data[3])]
	if int(data[1])== layer_tmp:
		count_tmp +=1
		layer_tmp = int(data[1])
	else:	
		count_tmp = 1
		layer_tmp = int(data[1])
	count += [count_tmp]
 
num = len(rotate)
max_size = -10.0 
for i in xrange(0, num):
	if rotate[i] == 0 or rotate[i] == 180:
		if x[i]+chip_x[i] > max_size:
			max_size = x[i]+chip_x[i]
		if y[i]+chip_y[i] > max_size:
			max_size = y[i]+chip_y[i]
	else:
		if x[i]+chip_y[i] > max_size:
			max_size = x[i]+chip_y[i]
		if y[i]+chip_x[i] > max_size:
			max_size = y[i]+chip_x[i]

heat_spread_size = 3.0*max_size  ## I will fix after work
heatsink_size = 6.0*max_size
convec_first = 1 / (H_TRANS * (0.3024*heatsink_size/0.12) *(0.3024*heatsink_size/0.12)) 
convec_second = 1 / (H_TRANS * heatsink_size * heatsink_size) 

os.system("cat default.config |\
           sed s/__SPREAD__/"+str(heat_spread_size)+"/ |\
           sed s/__SINK__/"+str(heatsink_size)+"/ |\
           sed s/__CONVEC1__/"+str(convec_first)+"/ |\
           sed s/__CONVEC2__/"+str(convec_second)+"/ > test.config")

os.system("cat TIM.flp |\
           sed s/__TIMSIZE__/"+str(max_size)+"/ |\
           sed s/__TIMSIZE__/"+str(max_size)+"/  > testTIM.flp")


	 


	 
		
		


