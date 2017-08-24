#!/usr/bin/python
import os

#def out(s):
#	print s
#os.system = out

watt_ratio = 0.5 ## ramwatt is off-chip memory power consumption, so we have to calculate on-chip memory power consumption by using the ratio, on-chip vs off-chip.   

freq1 = [1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.6]
freq2 = [1200, 1600, 2000, 2400, 2800, 3200, 3600] 
apps = ["bc","cg","dc","ep","ft","is","lu","mg","sp","ua","stress"] 

os.system("rm -f ptrace/*.ptrace")

for i in xrange(0, len(freq1)):
	for j in xrange(0, len(apps)):
		os.system("touch ptrace/e5-2667v4-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		os.system("echo  'NULL0 NULL1 NULL2 NULL3 0_CORE 1_CORE 2_CORE 3_CORE 4_CORE 5_CORE 6_CORE 7_CORE 0_LL 1_LL 2_LL 3_LL 4_LL 5_LL 6_LL 7_LL ' >> ptrace/e5-2667v4-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		os.system("echo -n '0 0 0 0 ' >> ptrace/e5-2667v4-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		for k in xrange(0, 8):
			os.system("cat pkgwatt/pkgwatt-freq"+str(freq1[i]) +".csv | awk 'NR=="+str(j+2)+"{printf $5/8\" \"}' >>ptrace/e5-2667v4-" +str(apps[j])+str(freq2[i])+ ".ptrace")
		for k in xrange(0, 8):
			os.system("cat ramwatt/ramwatt-freq"+str(freq1[i]) +".csv | awk 'NR=="+str(j+2)+"{printf $5/8*"+str(watt_ratio)+"\" \"}' >>ptrace/e5-2667v4-" +str(apps[j])+str(freq2[i])+ ".ptrace")

		#os.system("echo '0 0 0 0 0 0 0 0' >> ptrace/e5-2667v4-" +str(apps[j])+str(freq2[i])+ ".ptrace")

	 
		
		


