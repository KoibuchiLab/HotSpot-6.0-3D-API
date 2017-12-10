#!/usr/bin/python
import os
import sys

num_of_division = 4 ##base2 default 4

freq1 = [2000,1900,1800,1700,1600,1500,1400,1300,1200,1100,1000]

os.system("rm -f ptrace/base2CPU*.ptrace")

for i in xrange(0, len(freq1)):
	os.system("touch ptrace/base2CPU-" +str(freq1[i])+ ".ptrace")
	os.system("echo  'CORE0 CORE1 CORE2 CORE3 CORE4 CORE5 CORE6 CORE7 CORE8 CORE9 CORE10 CORE11 CORE12 CORE13 CORE14 CORE15' >> ptrace/base2CPU-" +str(freq1[i])+ ".ptrace")
	for k in xrange(0, 16):
		os.system("cat watt.data | awk 'NR=="+str(i+1)+"{printf $1/"+str(num_of_division)+"\" \"}' >>ptrace/base2CPU-" +str(freq1[i])+ ".ptrace")

	 
		
		


