#!/usr/bin/python
import os


freq1 = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]
freq2 = [1000, 1100, 1200, 1300, 1400, 1500, 1600] 
apps = ["bc","cg","dc","ep","ft","is","lu","mg","sp","ua","stress"] 

os.system("rm -f ptrace/*.ptrace")
#def out(s):
#	print s
#os.system = out

for i in xrange(0, len(freq1)):
	f = open("freq"+str(freq1[i]) +".csv")
	tmp = f.readlines()
	watt = []
	for line in tmp:
		data = line[:-1].split('\t')
		watt += [float(data[10])]
 
	for j in xrange(0, len(apps)):
		tmp_watt = watt[j+1]/68
		os.system("cat base.ptrace | sed s/CORE_WATT/"+str(tmp_watt)+"/g >>ptrace/phi7250-" +str(apps[j])+str(freq2[i])+ ".ptrace")


	 
		
		


