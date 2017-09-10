#!/usr/bin/python

import os
import sys

grid_size = 64
grid = [[0.0 for i in range(grid_size)] for j in range(grid_size)]

input_file = sys.argv[1]
if not os.access(input_file, os.R_OK):
        sys.stderr.write("Can't read file '"+input_file+"'\n")
f = open(input_file)
chip_lines = f.readlines()
f.close


input_file = sys.argv[2]
if not os.access(input_file, os.R_OK):
        sys.stderr.write("Can't read file '"+input_file+"'\n")
f = open(input_file)
temp_lines = f.readlines()
f.close

layer_num = sys.argv[3]

x_count = 0
y_count = 0
for line1 in temp_lines:
	data1 = line1[:-1].split('\t')
	temp = data1[1]
	grid[x_count][y_count] = temp
	if x_count == 63:
		if y_count == 63:
			break
		else:
			x_count = 0
			y_count += 1
	else:
		x_count += 1
 	
#print layer_num + "th layer detailed"

for line2 in chip_lines:
	data2 = line2[:-1].split(' ')
	if layer_num == data2[1]:
		chip_name = data2[0]
		x_left = int(data2[2])
		x_right = int(data2[3])
		y_top = int(data2[4])
		y_bottom = int(data2[5])
		x_chip = float(data2[6])
		y_chip = float(data2[7])
		max_temp = -10.0
		for i in range(x_left, x_right):
			for j in range(y_top, y_bottom):
				temp = float(grid[i][j])-273.15
				if temp > max_temp:
					max_temp = temp
		print max_temp, chip_name, layer_num, x_chip, y_chip

