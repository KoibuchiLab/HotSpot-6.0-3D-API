#!/usr/bin/python
import os
import sys

#def out(s):
#	print s
#os.system = out

lcc_watt3600 = 4.0 * 25 / 32 ##reffering when 32MB cashe, 4Watt
lcc_watt = 3.125 
freq1 = [1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.6]
freq2 = [1200, 1600, 2000, 2400, 2800, 3200, 3600] 
apps = ["bc","cg","dc","ep","ft","is","lu","mg","sp","ua","stress"] 

os.system("rm -f ptrace/*.ptrace")

for i in xrange(0, len(freq1)):
	for j in xrange(0, len(apps)):
		os.system("touch ptrace/base1-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		os.system("echo  'CORE0_0 CORE0_1 CORE1_0 CORE1_1 CORE2_0 CORE2_1 CORE3_0 CORE3_1 LLC0 LLC1 LLC2 LLC3 NULL0 NULL1 NULL2 NULL3' >> ptrace/base1-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		freq_3600 = open("pkgwatt/pkgwatt-freq3.6.csv").readlines()[j+1].strip().split()[6]
		freq_Compared = open("pkgwatt/pkgwatt-freq" +str(freq1[i])+".csv").readlines()[j+1].strip().split()[6] 
		lcc_watt = float(lcc_watt3600) * float(freq_Compared) / float(freq_3600)
		for k in xrange(0, 8):
			os.system("cat pkgwatt/pkgwatt-freq"+str(freq1[i]) +".csv | awk 'NR=="+str(j+2)+"{printf $7/8/2-"+str(lcc_watt)+"\" \"}' >>ptrace/base1-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		for k in xrange(0, 4):
			os.system("echo -n '"+str(2*lcc_watt) + " '>>ptrace/base1-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		os.system("echo -n '0 0 0 0 ' >> ptrace/base1-" +str(apps[j])+str(freq2[i])+ ".ptrace")

	 
		
		


