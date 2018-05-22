#!/usr/bin/python
import os
import sys

#def out(s):
#	print s
#os.system = out

freq1 = [2000,1900,1800,1700,1600,1500,1400,1300,1200,1100,1000]

os.system("rm -f ptrace/base2L2DRAM*.ptrace")

for i in xrange(0, len(freq1)):
	os.system("touch ptrace/base2L2DRAM-" +str(freq1[i])+ ".ptrace")
	os.system("echo  'DRAM0 DRAM1 DRAM2 DRAM3 L2C0 L2C1 L2C2 L2C3 L2C4 L2C5 L2C6 L2C7 CORE0 CORE1 CORE2 CORE3' >> ptrace/base2L2DRAM-" +str(freq1[i])+ ".ptrace")
	for k in xrange(0, 4):
		os.system("cat watt.data | awk 'NR=="+str(i+1)+"{printf 0.83\" \"}' >>ptrace/base2L2DRAM-" +str(freq1[i])+ ".ptrace")
	for k in xrange(0, 8):
		os.system("cat watt.data | awk 'NR=="+str(i+1)+"{printf $2/12\" \"}' >>ptrace/base2L2DRAM-" +str(freq1[i])+ ".ptrace")
	for k in xrange(0, 4):
		os.system("cat watt.data | awk 'NR=="+str(i+1)+"{printf $1/4\" \"}' >>ptrace/base2L2DRAM-" +str(freq1[i])+ ".ptrace")

	 
		
		


