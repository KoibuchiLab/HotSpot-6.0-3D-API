#!~/local/bin/python
import os
import multiprocessing as mp
import time

local_config_dir = "local"
proc = 16 
i = 0
j = 0
#g = 0.002184
#flp_list = ["tulsa"] #only support one chio now
#flp_list = ["base3"]
#freq_list = [1200,1400,1600,1800,2000,2200,2400,2600,2800,3000,3200,3400,3600]

#flp_list = ["phi7250"]
#freq_list = [1000,1100,1200,1300,1400,1500,1600]

#flp_list = ["base2"]
#freq_list = [1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000]

flp_list = ["phi7250"]
freq_list = [1000,1100,1200,1300,1400,1500,1600]


#flp_list = ["e5-2667v4"]
#freq_list = ["stress1200","stress1400","stress1600","stress1800","stress2000","stress2200","stress2400","stress2600","stress2800","stress3000","stress3200","stress3400","stress3600"]

mat = ["arumi","oil","fluori","water"] 
#mat = ["air"]


#config file generation

#count = 0
#for i in range(0,10):
#    for j in range(0,10):
#           os.system("cat base.data |\
#                    sed s/__XXX__/"+str(g*i)+"/ |\
#                    sed s/__YYY__/"+str(g*j)+"/ > "+local_config_dir+"/local"+str(count)+".data")
#           count += 1
count = 0
for k in range(0,len(mat)):
	for i in range(0,len(flp_list)):
		for j in range(0,len(freq_list)):
			os.system("cat eval1.data |\
						sed s/__CHIP__/"+str(flp_list[i])+"/g |\
						sed s/__FREQ__/"+str(freq_list[j])+"/g > "+local_config_dir+"/local"+str(count)+".data")
			count += 1
if proc > count:
    proc = count

os.system("rm -f "+local_config_dir+"/result.tmp*")


#subprocess command
def exec_sim(p):
    ini = count * p / proc
    fin = count * (p+1) / proc
    for i in xrange(ini, fin):
		print i
		mat_num = i / len(freq_list)
		print mat[mat_num]
		os.system("python hotspot_JK2.py "+local_config_dir+"/local"+str(i)+".data "+str(mat[mat_num])+ " --no_images  "+str(i)+" > "+local_config_dir+"/result.tmp"+str(i))
    return

#parallel exection
pool = mp.Pool(proc)
callback = pool.map(exec_sim, range(proc))


os.system("rm *test*")
os.system("rm tmp.*")
os.system("rm *]_*.flp")
os.system("rm *,")
os.system("rm sorted*")
os.system("rm null*")


print "finish" 
