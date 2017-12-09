#!/usr/bin/python
import os
import sys

num_of_division = 16 ##base2 default: 12

freq1 = [2000,1900,1800,1700,1600,1500,1400,1300,1200,1100,1000]

os.system("rm -f ptrace/base2L2*.ptrace")

for i in xrange(0, len(freq1)):
	os.system("touch ptrace/base2L2-" +str(freq1[i])+ ".ptrace")
	os.system("echo  'L2C0 L2C1 L2C2 L2C3 L2C4 L2C5 L2C6 L2C7 L2C8 L2C9 L2C10 L2C11 L2C12 L2C13 L2C14 L2C15' >> ptrace/base2L2-" +str(freq1[i])+ ".ptrace")
	for k in xrange(0, 16):
		os.system("cat watt.data | awk 'NR=="+str(i+1)+"{printf $2/"+str(num_of_division)+"\" \"}' >>ptrace/base2L2-" +str(freq1[i])+ ".ptrace")

	 
		
		


