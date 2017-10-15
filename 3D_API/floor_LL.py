#!/usr/bin/python
import os
import sys
import null_data_file
import floorplan_LL

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
def floor(sorted_input, null_data):
	"""
	if (len(sys.argv) != 2):
		sys.stderr.write("Usage: " + sys.argv[0] + " <input file (.dat)>\n")
		sys.exit(1)

	input_file = sys.argv[1]
	if not os.access(input_file, os.R_OK):
			sys.stderr.write("Can't read file '"+input_file+"'\n")
			sys.exit(1)
	"""
	"""
	input_file = 'sorted.data'
	f = open(input_file)
	data_lines = f.readlines()
	f.close
	
	f2 = open('null.data')
	null_data_lines = f2.readlines()
	f2.close
	"""
	#os.system("rm -f test*.flp")


	layer_tmp = 0;
	count_tmp = 0;

	chip_layer, count, rotate = [], [], []
	chip_x, chip_y, chip_name = [], [], []
	chip_xlen, chip_ylen = [], []
	
	"""
	for line in sorted_input:
		print "sorted input line is %s" % str(line)
		data = str(line)
		print "sort input data is %s" % data
	for line in data_lines:
		print "input file line is %s" % line
		data = line[:-1].split(' ')
		print "data line -1 is %s"% data
	"""
	for line in sorted_input:	#replace later if worth it
		#print "line is "+str(line)
		data = line[:-1]
		#print "data is "+str(data)
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
		elif 'base2' in str(data[0]):
			chip_xlen += [float(base2_x)]
			chip_ylen += [float(base2_y)]
			chip_name += ['base2']
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
	"""
	null_layer, name, null_x, null_y, null_x_len, null_y_len = [],[],[],[],[],[] 

	for line2 in null_data:
		data2 = line2[:-1].split(' ')
		null_layer += [int(data2[0])]
		name += [str(data2[1])]
		null_x += [float(data2[2])]
		null_y += [float(data2[3])]
		null_x_len += [float(data2[4])]
		null_y_len += [float(data2[5])]
		
	"""
	layer_num = chip_layer[len(chip_layer)-1]+1;

	#######
	#for debug print 
	#######

	#def out(s):
	#	print s
	#os.system = out
	#nulldatall = null_data_file.null_data_file('null.data')
	nulldatall = null_data
	floorplan=floorplan_LL.floorplan()
	for i in xrange(1, layer_num):
		#print "xrange is "+ str(xrange(1, layer_num))
		os.system("touch test" + str(i) + ".flp") #usd in lcf.py
		file_name = "test" + str(i) + "_LL.flp"
		file = open(file_name,"w+")
		for j in xrange(0, len(chip_layer)):
		# create file called "test"+i.flp, Open it and fill it with contents below
			if chip_layer[j] == i:
				if rotate[j] == 0: 
					to_write = floorplan.write_rotate_0(chip_name[j], chip_layer[j],count[j], chip_x[j], chip_y[j])
					#print str(to_write)
					file.write(to_write)
					#tmp_floorplan = floorplan.get_floorplan(str(chip_name[j]))
					#print "floorplan going to write "+str(tmp_)
					#os.system("cat FLOORPLAN/"+str(chip_name[j]) +".flp | awk '{OFMT = \"%.8f\"}{print \""+ str(chip_layer[j])+ "_"  + str(count[j])  + "\"$1,$2,$3,$4+"+str(chip_x[j]) +",$5+"+str(chip_y[j]) +"}' >> test" + str(i) + ".flp  ")
					#print"cat FLOORPLAN/"+str(chip_name[j]) +".flp | awk '{OFMT = \"%.8f\"}{print \""+ str(chip_layer[j])+ "_"  + str(count[j])  + "\"$1,$2,$3,$4+"+str(chip_x[j]) +",$5+"+str(chip_y[j]) +"}' >> test" + str(i) + ".flp  "
					#print"count is "+str(count[j])+" chipt x is "+str(chip_x[j])+" chip y is "+str(chip_y[j])
				elif rotate[j] == 90:
					to_write = floorplan.write_rotate_90(chip_name[j], chip_layer[j],count[j], chip_x[j], chip_y[j], chip_xlen[j], chip_ylen[j])
					#print str(to_write)
					file.write(to_write)
					#os.system("cat FLOORPLAN/"+str(chip_name[j]) +".flp | awk '{OFMT = \"%.8f\"}{print \""+ str(chip_layer[j])+ "_"  + str(count[j])  + "\"$1,$3,$2,$5+"+str(chip_x[j]) +"," +str(chip_xlen[j])+"-$4-$2+"+str(chip_y[j]) +"}' >> test" + str(i) + ".flp  ")
					#print "cat FLOORPLAN/"+str(chip_name[j]) +".flp | awk '{OFMT = \"%.8f\"}{print \""+ str(chip_layer[j])+ "_"  + str(count[j])  + "\"$1,$3,$2,$5+"+str(chip_x[j]) +"," +str(chip_xlen[j])+"-$4-$2+"+str(chip_y[j]) +"}' >> test" + str(i) + ".flp  "
				elif rotate[j] == 180:
					to_write = floorplan.write_rotate_180(chip_name[j], chip_layer[j],count[j], chip_x[j], chip_y[j], chip_xlen[j], chip_ylen[j])
					#print str(to_write)
					file.write(to_write)
					#os.system("cat FLOORPLAN/"+str(chip_name[j]) +".flp | awk '{OFMT = \"%.8f\"}{print \""+ str(chip_layer[j])+ "_"  + str(count[j])  + "\"$1,$2,$3,"+str(chip_xlen[j])+"-$4-$2+"+str(chip_x[j]) +","+str(chip_ylen[j])+"-$5-$3+"+str(chip_y[j])+"}' >> test" + str(i) + ".flp  ")
					#print "cat FLOORPLAN/"+str(chip_name[j]) +".flp | awk '{OFMT = \"%.8f\"}{print \""+ str(chip_layer[j])+ "_"  + str(count[j])  + "\"$1,$2,$3,"+str(chip_xlen[j])+"-$4-$2+"+str(chip_x[j]) +","+str(chip_ylen[j])+"-$5-$3+"+str(chip_y[j])+"}' >> test" + str(i) + ".flp  "
				elif rotate[j] == 270:
					to_write = floorplan.write_rotate_270(chip_name[j], chip_layer[j],count[j], chip_x[j], chip_y[j], chip_xlen[j], chip_ylen[j])
					#print str(to_write)
					file.write(to_write)
					#os.system("cat FLOORPLAN/"+str(chip_name[j]) +".flp | awk '{OFMT = \"%.8f\"}{print \""+ str(chip_layer[j])+ "_"  + str(count[j])  + "\"$1,$3,$2,"+str(chip_ylen[j])+"-$5-$3+"+str(chip_x[j]) +",$4+"+str(chip_y[j]) +"}' >> test" + str(i) + ".flp  ")
					#print "cat FLOORPLAN/"+str(chip_name[j]) +".flp | awk '{OFMT = \"%.8f\"}{print \""+ str(chip_layer[j])+ "_"  + str(count[j])  + "\"$1,$3,$2,"+str(chip_ylen[j])+"-$5-$3+"+str(chip_x[j]) +",$4+"+str(chip_y[j]) +"}' >> test" + str(i) + ".flp  "
					
		write_null = ""
		for k in xrange(0, len(nulldatall.get_null_layer())):	#use null class func
			if int(nulldatall.get_null_layer()[k]) == i:
				write_null += nulldatall.get_name()[k]+" "+str(nulldatall.get_null_x()[k])+" "+str(nulldatall.get_null_y()[k])+" "+str(nulldatall.get_null_x_len()[k])+" "+str(nulldatall.get_null_y_len()[k])+" " + str(material_capacity[material])+" "+str(material_resistance[material])+"\n"
				#os.system("echo " +str(name[k])+" " +str(null_x[k])+" "+ str(null_y[k])+" "+ str(null_x_len[k])+" "+str(null_y_len[k])+" " + str(material_capacity[material])+" "+str(material_resistance[material])+"  >> test"+str(i) + ".flp ")
				#print "echo " +str(name[k])+" " +str(null_x[k])+" "+ str(null_y[k])+" "+ str(null_x_len[k])+" "+str(null_y_len[k])+" " + str(material_capacity[material])+" "+str(material_resistance[material])+"  >> test"+str(i) + ".flp "
		file.write(write_null)
		#print "wrote file name "+ file_name
		file.close()	
			


