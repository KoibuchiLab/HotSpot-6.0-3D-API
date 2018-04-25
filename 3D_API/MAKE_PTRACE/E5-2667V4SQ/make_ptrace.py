#!/usr/bin/python
import os
import sys

#def out(s):
#	print s
#os.system = out

##rate = 1.0 ### row:0.012634, col=0.014172 -> row:0.014172, col=0.014172   
rate = 0.014172/0.012634


lcc_watt3600 = 4.0 * 25 / 32 ##reffering when 32MB cashe, 4Watt
lcc_watt = 3.125  
freq1 = [1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6]
freq2 = [1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600] 
apps = ["bc","cg","dc","ep","ft","is","lu","mg","sp","ua","stress"] 

os.system("rm -f ptrace/*.ptrace")

for i in xrange(0, len(freq1)):
	for j in xrange(0, len(apps)):
		os.system("touch ptrace/e5-2667v4sq-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		os.system("echo  'NULL0 NULL1 NULL2 NULL3 0_CORE 1_CORE 2_CORE 3_CORE 4_CORE 5_CORE 6_CORE 7_CORE 0_LL 1_LL 2_LL 3_LL 4_LL 5_LL 6_LL 7_LL ' >> ptrace/e5-2667v4sq-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		os.system("echo -n '0 0 0 0 ' >> ptrace/e5-2667v4sq-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		freq_3600 = open("pkgwatt/pkgwatt-freq3.6.csv").readlines()[j+1].strip().split()[6]
		freq_Compared = open("pkgwatt/pkgwatt-freq" +str(freq1[i])+".csv").readlines()[j+1].strip().split()[6] 
		lcc_watt = float(lcc_watt3600) * float(freq_Compared) / float(freq_3600) * rate
		print lcc_watt
		for k in xrange(0, 8):
			os.system("cat pkgwatt/pkgwatt-freq"+str(freq1[i]) +".csv | awk 'NR=="+str(j+2)+"{printf $7/8/2*"+str(rate)+"-"+str(lcc_watt)+"\" \"}' >>ptrace/e5-2667v4sq-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		for k in xrange(0, 8):
			os.system("echo -n '"+str(lcc_watt) + " '>>ptrace/e5-2667v4sq-" +str(apps[j])+str(freq2[i])+ ".ptrace")

		#os.system("echo '0 0 0 0 0 0 0 0' >> ptrace/e5-2667v4-" +str(apps[j])+str(freq2[i])+ ".ptrace")

	 
		
		


