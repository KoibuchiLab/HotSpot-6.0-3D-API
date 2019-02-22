#!/usr/bin/python

import os
import sys

output_grid_size = 128
grid = [[0.0 for i in range(output_grid_size)] for j in range(output_grid_size)]

input_file = sys.argv[1]
if not os.access(input_file, os.R_OK):
        sys.stderr.write("Can't read file '"+input_file+"'\n")
f = open(input_file)
chip_lines = f.readlines()
f.close

rank = sys.argv[2]
pid = sys.argv[3]

line2 = chip_lines[int(rank)-1]
data2 = line2[:-1].split(' ')
layer_num = int(data2[1])

f = open("layer"+str(layer_num)+"_"+str(pid)+".grid.steady")
temp_lines = f.readlines()
f.close

x_count = 0
y_count = 0
for line1 in temp_lines:
	data1 = line1[:-1].split('\t')
	temp = data1[1]
	grid[x_count][y_count] = temp
	if x_count == output_grid_size-1:
		if y_count == output_grid_size-1:
			break
		else:
			x_count = 0
			y_count += 1
	else:
		x_count += 1
chip_name = data2[0]
x_left = int(data2[2])
x_right = int(data2[3])
y_top = int(data2[4])
y_bottom = int(data2[5])
x_chip = float(data2[6])
y_chip = float(data2[7])
freq = str(data2[8])
rotate = int(data2[9])
max_temp = -10.0
for i in range(x_left, x_right):
	for j in range(y_top, y_bottom):
		temp = float(grid[i][j])-273.15
		if temp > max_temp:
			max_temp = temp
print max_temp, chip_name, layer_num, x_chip, y_chip, freq, rotate

