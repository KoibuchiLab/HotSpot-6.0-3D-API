#!/usr/bin/python
import os
import sys
import nulldata_file
import floorplan

tulsa_x = 0.02184 #default xeon tulsa chip size
tulsa_y = 0.02184
phi7250_x = 0.0315 #default phi7250 chip size
phi7250_y = 0.0205
e52667v4_x = 0.012634 #default e5-2667-v4 chip size
e52667v4_y = 0.014172
base1_x = 0.016
base1_y = 0.016
base2_x = 0.013
base2_y = 0.013
spreader_x = 0.06
spreader_y = 0.06

material = 0 # 0:tim 1:metal 2:air
material_capacity = [0.25, 4e6, 4e6]
material_resistance = [2e-5, 0.0025, 0.25]

"""
def read_null_data(null_dot_data):
	f2 = open('null.data')
	null_data_lines = f2.readlines()
	f2.close

	for lines in null_data_lines:
		data2 = line2[:-1].split(' ')
		null_layer += [int(data2[0])]
		name += [str(data2[1])]
		null_x += [float(data2[2])]
		null_y += [float(data2[3])]
		null_x_len += [float(data2[4])]
		null_y_len += [float(data2[5])]
"""

#def floor(sorted_input):
def floor(sorted_input, null_data, pid):

	layer_tmp = 0;
	count_tmp = 0;

	chip_layer, count, rotate = [], [], []
	chip_x, chip_y, chip_name = [], [], []
	chip_xlen, chip_ylen = [], []

	for data in sorted_input:
		#data = line[:-1].split(' ') #tuple, dont need to split
		chip_layer += [int(data[1])]
		rotate += [int(data[5])]
		chip_x += [float(data[2])]
		chip_y += [float(data[3])]
		if 'tulsa' in str(data[0]):
			chip_xlen += [float(tulsa_x)]
			chip_ylen += [float(tulsa_y)]
			chip_name += ['tulsa']
		elif 'phi7250' in str(data[0]):
			chip_xlen += [float(phi7250_x)]
			chip_ylen += [float(phi7250_y)]
			chip_name += ['phi7250']
		elif 'e5-2667v4' in str(data[0]):
			chip_xlen += [float(e52667v4_x)]
			chip_ylen += [float(e52667v4_y)]
			chip_name += ['e5-2667v4']
		elif 'base1' in str(data[0]):
			chip_xlen += [float(base1_x)]
			chip_ylen += [float(base1_y)]
			chip_name += ['base1']
		elif 'base2L2DRAM' in str(data[0]):
			chip_xlen += [float(base2_x)]
			chip_ylen += [float(base2_y)]
			chip_name += ['base2L2DRAM']
		elif 'base2L2' in str(data[0]):
			chip_xlen += [float(base2_x)]
			chip_ylen += [float(base2_y)]
			chip_name += ['base2L2']
		elif 'base2CPU' in str(data[0]):
			chip_xlen += [float(base2_x)]
			chip_ylen += [float(base2_y)]
			chip_name += ['base2CPU']
		elif 'base2DRAM' in str(data[0]):
			chip_xlen += [float(base2_x)]
			chip_ylen += [float(base2_y)]
			chip_name += ['base2DRAM']
		elif 'base2' in str(data[0]):
			chip_xlen += [float(base2_x)]
			chip_ylen += [float(base2_y)]
			chip_name += ['base2']
		elif 'base3' in str(data[0]):
			chip_xlen += [float(base2_x)]
			chip_ylen += [float(base2_y)]
			chip_name += ['base3']
		elif 'spreader' in str(data[0]):
			chip_xlen += [float(spreader_x)]
			chip_ylen += [float(spreader_y)]
			chip_name += ['spreader']
		elif 'null' == str(data[0]):
			chip_xlen += [0.00001]
			chip_ylen += [0.00001]
			chip_name += ['null']
		else:
			sys.stderr('invalid chip name')
			sys.exit(1)
		if int(data[1])== layer_tmp:
			count_tmp +=1
			layer_tmp = int(data[1])
		else:
			count_tmp = 1
			layer_tmp = int(data[1])
		count += [count_tmp]

	layer_num = chip_layer[len(chip_layer)-1]+1;

	#######
	#for debug print
	#######

	nulldatall = null_data
	floorplanObject=floorplan.floorplan()
	for i in xrange(1, layer_num):
		#os.system("touch test" + str(i) + ".flp") #usd in lcf.py
		#print "+++++++++++++++ here"
		file_name = "test" + str(i) + "_"+str(pid)+".flp"
		file = open(file_name,"w+")
		for j in xrange(0, len(chip_layer)):
			if chip_layer[j] == i:
				if rotate[j] == 0:
					to_write = floorplanObject.write_rotate_0(chip_name[j], chip_layer[j],count[j], chip_x[j], chip_y[j])
					file.write(to_write)
				elif rotate[j] == 90:
					to_write = floorplanObject.write_rotate_90(chip_name[j], chip_layer[j],count[j], chip_x[j], chip_y[j], chip_xlen[j], chip_ylen[j])
					file.write(to_write)
				elif rotate[j] == 180:
					to_write = floorplanObject.write_rotate_180(chip_name[j], chip_layer[j],count[j], chip_x[j], chip_y[j], chip_xlen[j], chip_ylen[j])
					file.write(to_write)
				elif rotate[j] == 270:
					to_write = floorplanObject.write_rotate_270(chip_name[j], chip_layer[j],count[j], chip_x[j], chip_y[j], chip_xlen[j], chip_ylen[j])
					file.write(to_write)
		write_null = ""
		for k in xrange(0, len(nulldatall.get_null_layer())):	#use null class func
			if int(nulldatall.get_null_layer()[k]) == i:
				write_null += nulldatall.get_name()[k]+" "+str(nulldatall.get_null_x()[k])+" "+str(nulldatall.get_null_y()[k])+" "+str(nulldatall.get_null_x_len()[k])+" "+str(nulldatall.get_null_y_len()[k])+" " + str(material_capacity[material])+" "+str(material_resistance[material])+"\n"
		file.write(write_null)
		file.close()
