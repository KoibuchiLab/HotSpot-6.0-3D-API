#!/usr/bin/python
import os

os.system("rm -f tmp")
os.system("cat test.data | sort -n -k2 > tmp")

f = open('tmp')
lines2 = f.readlines()
f.close

os.system("rm -f test.lcf")
os.system("touch test.lcf") 


layer = []

for line in lines2:
	data = line[:-1].split(' ')
	layer += [int(data[1])]
layer_num = layer[len(layer)-1]

for i in xrange(0, layer_num):
	os.system("echo  \"" +str(2*i)+"\"  >> test.lcf")
	os.system("echo  \"Y\nY\n1.75e6\n0.01\n0.00015\"  >> test.lcf")
	os.system("echo  \"test" +str(i+1)+".flp\n\"  >> test.lcf")
	os.system("echo  \"" +str(2*i+1)+"\"  >> test.lcf")
	os.system("echo  \"Y\nN\n4e6\n0.25\n2.0e-05\"  >> test.lcf")
	os.system("echo  \"testTIM.flp\n\"  >> test.lcf")

	


