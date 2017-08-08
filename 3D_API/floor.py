#!/usr/bin/python
import os

os.system("rm -f tmp")
os.system("cat test.data | sort -n -k2 > tmp")

material = 0  # 0:tim 1:metal 2:air

material_capacity = [0.25, 4e6, 4e6]
material_resistance = [2e-5, 0.0025, 0.25]

f = open('tmp')
test_data_lines = f.readlines()
f.close

f2 = open('null.data')
null_data_lines = f2.readlines()
f2.close

os.system("rm -f test*.flp")


layer_tmp = 0;
count_tmp = 0;

layer, count, rotate = [], [], []
chip_x, chip_y = [], []

for line in test_data_lines:
	data = line[:-1].split(' ')
	layer += [int(data[1])]
	rotate += [int(data[5])]
	chip_x += [float(data[2])]
	chip_y += [float(data[3])]
	if int(data[1])== layer_tmp:
		count_tmp +=1
		layer_tmp = int(data[1])
	else:	
		count_tmp = 1
		layer_tmp = int(data[1])
	count += [count_tmp]

layer2, name, null_x, null_y, null_x_len, null_y_len = [],[],[],[],[],[] 
for line2 in null_data_lines:
	data2 = line2[:-1].split(' ')
	layer2 += [int(data2[0])]
	name += [str(data2[1])]
	null_x += [float(data2[2])]
	null_y += [float(data2[3])]
	null_x_len += [float(data2[4])]
	null_y_len += [float(data2[5])]
	

layer_num = layer[len(layer)-1]+1;
h = 0.02184 #default Xeon Trusa size 
for i in xrange(1, layer_num):
	os.system("touch test" + str(i) + ".flp")
	for j in xrange(0, len(layer)):
		if layer[j] == i:
			if rotate[j] == 0: 
				os.system("cat FLOORPLAN/tulsa.flp | awk '{print \""+ str(layer[j])+ "_"  + str(count[j])  + "\"$1,$2,$3,$4+"+str(chip_x[j]) +",$5+"+str(chip_y[j]) +"}' >> test" + str(i) + ".flp  ")
			elif rotate[j] == 90:
				os.system("cat FLOORPLAN/tulsa.flp | awk '{print \""+ str(layer[j])+ "_"  + str(count[j])  + "\"$1,$3,$2,$5+"+str(chip_x[j]) +",h-$4+"+str(chip_y[j]) +"}' >> test" + str(i) + ".flp  ")
			elif rotate[j] == 180:
				os.system("cat FLOORPLAN/tulsa.flp | awk '{print \""+ str(layer[j])+ "_"  + str(count[j])  + "\"$1,$2,$3,h-$4+"+str(chip_x[j]) +",h-$5+"+str(chip_y[j]) +"}' >> test" + str(i) + ".flp  ")
			elif rotate[j] == 270:
				os.system("cat FLOORPLAN/tulsa.flp | awk '{print \""+ str(layer[j])+ "_"  + str(count[j])  + "\"$1,$3,$2,h-$5+"+str(chip_x[j]) +",$4+"+str(chip_y[j]) +"}' >> test" + str(i) + ".flp  ")
	for k in xrange(0, len(layer2)):
		if layer2[k] == i:
			os.system("echo " +str(name[k])+" " +str(null_x[k])+" "+ str(null_y[k])+" "+ str(null_x_len[k])+" "+str(null_y_len[k])+" " + str(material_capacity[material])+" "+str(material_resistance[material])+"  >> test"+str(i) + ".flp ")


	 
		
		


