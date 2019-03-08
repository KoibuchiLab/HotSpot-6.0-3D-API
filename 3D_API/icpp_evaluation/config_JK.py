#!/usr/bin/python

import os
import sys

args = sys.argv
output_grid_size = 128 

tulsa_x = 0.02184 #default tulsa chip size
tulsa_y = 0.02184

phi7250_x = 0.0315 #default phi7250 chip size 
phi7250_y = 0.0205

e52667v4_x = 0.012634 #default e5-2676v4 chip size
e52667v4_y = 0.014172 

base1_x = 0.016
base1_y = 0.016

base2_x = 0.013
base2_y = 0.013

spreader_x = 0.06
spreader_y = 0.06

k_pcb = 3.0 #default
t_pcb = 0.002 #default

## I'm not sure what value is the best estimation
## When it is AIR, I use forced convection. But when OIL or WATER, etc., I use natural convection.(velocity would be around 0.0(?) m/s)  			
#AIR_H = 40 # W/(m^2 K)  Heat Transffer Coefficient of AIR (velocity is aroud 1.0 m/s)
AIR_H = 14 # W/(m^2 K)  Heat Transffer Coefficient of AIR (velocity is aroud 1.0 m/s)
#AIR_H = 13 # W/(m^2 K)  Heat Transffer Coefficient of AIR (velocity is aroud 1.0 m/s)
OIL_H = 160 # W/(m^2 K) Heat Transffer Coefficient of OIL (using natural convection)
WATER_H = 800 # W/(m^2 K) Heat Transffer Coefficient of WATER (using natural convection)
FLUORI_H = 180 # W/(m^2 K) Heat Transffer Coefficient of FLUORINERT (using natural convection)
NOVEC_H = 180##caution! this value is not correct.  # W/(m^2 K) Heat Transffer Coefficient of NOVEC (using natural convection)
WATER_PILLOW_H = 5000 # W/(m^2 K) Heat Transffer Coefficient of WATER_PILLOW (using forced convection, velocity = 0.5m/s)

#if (len(args) != 3):
#	sys.stderr.write("Usage: " + args[0] + " <input file (.dat)> <water | air | oil>\n")
#	sys.exit(1)
counttt = args[3]
	
if args[2] == "water":
	H_TRANS = WATER_H
	k_pcb = 1.237
	t_pcb = 0.00215
elif args[2] == "air":
	H_TRANS = AIR_H
elif args[2] == "oil":
	H_TRANS = OIL_H
elif args[2] == "fluori":
	H_TRANS = FLUORI_H
elif args[2] == "novec":
	H_TRANS = NOVEC_H
elif args[2] == "water_pillow":
	H_TRANS = WATER_PILLOW_H
elif args[2] == "arumi":
	H_TRANS = WATER_H
else:
	sys.stderr.write("Invalid argument '" + args[2] + "'\n")
	sys.exit(1)

input_file = args[1]
if not os.access(input_file, os.R_OK):
	sys.stderr.write("Can't read file '"+input_file+"'\n")
	sys.exit(1)


f = open(input_file)
chip_lines = f.readlines()
f.close

os.system("rm -f "+str(counttt)+"test.config")
os.system("rm -f "+str(counttt)+"testTIM.flp")


layer_tmp = 0;
count_tmp = 0;

lay, count, rotate = [], [], []
chip_x, chip_y = [], []
x, y = [], []

for line in chip_lines:
	data = line[:-1].split(' ')
	chip_name = str(data[0])
	rotate += [int(data[5])]

	if 'tulsa' in chip_name:
		chip_x += [float (tulsa_x)]
		chip_y += [float (tulsa_y)]
	elif 'phi7250' in chip_name:
		chip_x += [float (phi7250_x)]
		chip_y += [float (phi7250_y)]
	elif 'e5-2667v4' in chip_name:
		chip_x += [float (e52667v4_x)]
		chip_y += [float (e52667v4_y)]
	elif 'base1' in chip_name:
		chip_x += [float (base1_x)]
		chip_y += [float (base1_y)]
	elif 'base2' in chip_name:
		chip_x += [float (base2_x)]
		chip_y += [float (base2_y)]
	elif 'base3' in chip_name:
		chip_x += [float (base2_x)]
		chip_y += [float (base2_y)]
	elif 'spreader' in chip_name:
		chip_x += [float (spreader_x)]
		chip_y += [float (spreader_y)]
	elif 'null' == chip_name:
		chip_x += [0.00001]
		chip_y += [0.00001]
	else:
		sys.stderr('invalid chip name in input file ' + input_file)
		sys.exit()

	lay += [int(data[1])]
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
system_size = -10.0 
for i in xrange(0, num):
	if rotate[i] == 0 or rotate[i] == 180:
		if x[i]+chip_x[i] > system_size:
			system_size = x[i]+chip_x[i]
		if y[i]+chip_y[i] > system_size:
			system_size = y[i]+chip_y[i]
	elif rotate[i] == 90 or rotate[i] == 270:
		if x[i]+chip_y[i] > system_size:
			system_size = x[i]+chip_y[i]
		if y[i]+chip_x[i] > system_size:
			system_size = y[i]+chip_x[i]
	else:
		sys.stderr('invalid rotation')
		sys.exit()
heatsink_fin_num = 20 ## 10(boards) * 2(both sides) 
heatsink_thickness = 0.0069  ##default heatsink thickness size
heat_spread_size = 3.0 * system_size ## I set those ratio(3.0 and 6.0) referring defalut chip ratio.
heatsink_size = 6.0 * system_size
heatsink_height = heatsink_size
convec_first = 1 / (H_TRANS * (heatsink_size * heatsink_size + heatsink_size * heatsink_height * heatsink_fin_num)) ##Heat convection can be calculated by 1/(H_TRANS * area). area: bottom area + side area
convec_second = 1 / (H_TRANS * heatsink_size * heatsink_size)

##when water pillow, removing heat sink.
if args[2] == "water_pillow":
	convec_first = 1 / (H_TRANS * heatsink_size * heatsink_size * 2) ## ignoring side area 
	heatsink_thickness = 0.00001 ##by using tiny thickness, removing heat sink   

os.system("cat default.config |\
           sed s/__SPREAD__/"+str(heat_spread_size)+"/ |\
           sed s/__SINK__/"+str(heatsink_size)+"/ |\
           sed s/__THICKNESS__/"+str(heatsink_thickness)+"/ |\
           sed s/__OUTPUT_GRID_SIZE__/"+str(output_grid_size)+"/ |\
           sed s/__TPCB__/"+str(t_pcb)+"/ |\
           sed s/__KPCB__/"+str(k_pcb)+"/ |\
           sed s/__CONVEC1__/"+str(convec_first)+"/ |\
           sed s/__CONVEC2__/"+str(convec_second)+"/ > "+str(counttt)+"test.config")

os.system("cat TIM.flp |\
           sed s/__TIMSIZE__/"+str(system_size)+"/ |\
           sed s/__TIMSIZE__/"+str(system_size)+"/  > "+str(counttt)+"testTIM.flp")


	 


	 
		
		


