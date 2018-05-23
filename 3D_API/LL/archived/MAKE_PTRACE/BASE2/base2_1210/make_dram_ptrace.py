#!/usr/bin/python
import os
import sys

total_dram_watt = 13.28
block_watt = total_dram_watt / 16

freq1 = [2000,1900,1800,1700,1600,1500,1400,1300,1200,1100,1000]

os.system("rm -f ptrace/base2DRAM*.ptrace")

for i in xrange(0, len(freq1)):
	os.system("touch ptrace/base2DRAM-" +str(freq1[i])+ ".ptrace")
	os.system("echo  'DRAM0 DRAM1 DRAM2 DRAM3 DRAM4 DRAM5 DRAM6 DRAM7 DRAM8 DRAM9 DRAM10 DRAM11 DRAM12 DRAM13 DRAM14 DRAM15' >> ptrace/base2DRAM-" +str(freq1[i])+ ".ptrace")
	for k in xrange(0, 16):
		os.system("cat watt.data | awk 'NR=="+str(i+1)+"{printf "+str(block_watt)+"\" \"}' >>ptrace/base2DRAM-" +str(freq1[i])+ ".ptrace")

	 
		
		


