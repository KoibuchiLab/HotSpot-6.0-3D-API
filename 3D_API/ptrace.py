#!/usr/bin/python
import os

os.system("rm -f tmp")
os.system("cat test.data | sort -n -k2 > tmp")

f = open('tmp')
lines2 = f.readlines()
f.close

f2 = open('null.data')
line4 = f2.readlines()
f2.close

os.system("rm -f test.ptrace")
os.system("touch test.ptrace") 

layer_tmp = 0;
count_tmp = 0;

layer, count, freq = [], [], []

for line in lines2:
	data = line[:-1].split(' ')
	layer += [int(data[1])]
	freq += [int(data[4])]
	if int(data[1])== layer_tmp:
		count_tmp +=1
		layer_tmp = int(data[1])
	else:	
		count_tmp = 1
		layer_tmp = int(data[1])
	count += [count_tmp]


layer2, name= [],[] 
for line3 in line4:
	data2 = line3[:-1].split(' ')
	layer2 += [int(data2[0])]
	name += [str(data2[1])]

for i in xrange(0, len(freq)):
	for j in xrange(0, len(layer)):
		if i == layer[j]-1:
			os.system("cat PTRACE/tulsa-" + str(freq[j]) + ".ptrace | awk 'NR==1{for(i=1;i<=NF;i++){printf \"" +str(layer[j]) + "_" + str(count[j]) + "\"$i\" \" }}' >> test.ptrace")
	for j in xrange(0, len(layer2)):
		if i == layer2[j]-1:
			os.system("echo -n \""+ str(name[j])+" \" >> test.ptrace")
os.system("echo '' >> test.ptrace")

for i in xrange(0, len(freq)):	 
	for j in xrange(0, len(freq)):
		if i == layer[j]-1:
			os.system("cat PTRACE/tulsa-" + str(freq[j]) + ".ptrace | awk 'NR==2{for(i=1;i<=NF;i++){printf $i\" \" }}' >> test.ptrace")
	for j in xrange(0, len(layer2)):
		if i == layer2[j]-1:
			os.system("echo -n \"0 \" >> test.ptrace") 
os.system("echo '' >> test.ptrace")

	 
		
		


