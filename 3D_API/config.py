#!/usr/bin/python
import os
import sys

args = sys.argv

AIR_H = 13
OIL_H = 160
WATER_H = 800

if args[1] == "water":
	H_TRANS = WATER_H
elif args[1] == "air":
	H_TRANS = AIR_H
elif args[1] == "oil":
	H_TRANS = OIL_H
else:
	sys.stderr('error args')
	sys.exit()

os.system("rm -f tmp")
os.system("cat test.data | sort -n -k2 > tmp")

f = open('tmp')
lines2 = f.readlines()
f.close

os.system("rm -f test.config")
os.system("rm -f testTIM.flp")


layer_tmp = 0;
count_tmp = 0;

lay, count, rotate = [], [], []
x, y = [], []
tulsa_x = 0.02184
tulsa_y = 0.02184
for line in lines2:
	data = line[:-1].split(' ')
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
		if x[i]+tulsa_x > max_size:
			max_size = x[i]+tulsa_x
		if y[i]+tulsa_y > max_size:
			max_size = y[i]+tulsa_y
	else:
		if x[i]+tulsa_y > max_size:
			max_size = x[i]+tulsa_y
		if y[i]+tulsa_x > max_size:
			max_size = y[i]+tulsa_x

heat_spread_size = 3.0*max_size 
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


	 


	 
		
		


