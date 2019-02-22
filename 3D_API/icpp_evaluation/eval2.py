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
#data = [
#		["e5-2667v4","stress3400","air",1],
#		["e5-2667v4","stress3400","air",2],
#		["e5-2667v4","stress3400","air",3],
#		["e5-2667v4","stress3400","air",4],
#		["e5-2667v4","stress3400","air",5],
#		["e5-2667v4","stress3400","air",6],
#		["e5-2667v4","stress3400","air",7],
#		["e5-2667v4","stress3400","air",8],
#		["e5-2667v4","stress3400","air",9],
#		["e5-2667v4","stress3400","air",10],
#		["e5-2667v4","stress3400","air",11],
#		["e5-2667v4","stress3400","air",12]
#		]
data = [
        ["e5-2667v4","stress3400","air",1],
        ["e5-2667v4","stress3400","oil",1],
        ["e5-2667v4","stress3400","fluori",1],
        ["e5-2667v4","stress3400","water",1],
        ["e5-2667v4","stress3400","water_pillow",1],
        ["e5-2667v4","stress3400","arumi",1]
        ]


#flp_list = ["base3"]
#freq_list = [1200,1400,1600,1800,2000,2200,2400,2600,2800,3000,3200,"stress3400",3600]
#freq_list = [3600]
#freq_list = [185,541,1004,1380,1787,2191,2578,2990,"stress3400"]
#mat = ["air","oil","fluori","water"]
#mat = ["air"]


#config file generation
os.system("rm -f "+local_config_dir+"/local*.data")

count = 0

for i in range(0, len(data)):
	os.system("touch " +local_config_dir + "/local" + str(count)+".data")
	for j in range(0, data[i][3]):
		os.system("echo "+str(data[i][0])+" "+ str(j+1)+" 0.0 0.0 "+ str(data[i][1]) + " 0 >> " + local_config_dir + "/local" + str(count)+".data")
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
		if data[i][2] == "air":
			os.system("python hotspot_JK2.py "+local_config_dir+"/local"+str(i)+".data air --no_images  "+str(i)+" > "+local_config_dir+"/result_"+str(data[i][0])+"_"+str(data[i][1])+str(data[i][2])+str(data[i][3]))
		elif data[i][2] == "oil":
			os.system("python hotspot_JK2.py "+local_config_dir+"/local"+str(i)+".data oil --no_images  "+str(i)+" > "+local_config_dir+"/result_"+str(data[i][0])+"_"+str(data[i][1])+str(data[i][2])+str(data[i][3]))
		elif data[i][2] == "fluori":
			os.system("python hotspot_JK2.py "+local_config_dir+"/local"+str(i)+".data fluori --no_images  "+str(i)+" > "+local_config_dir+"/result_"+str(data[i][0])+"_"+str(data[i][1])+str(data[i][2])+str(data[i][3]))
		elif data[i][2] == "water":
			os.system("python hotspot_JK2.py "+local_config_dir+"/local"+str(i)+".data water --no_images  "+str(i)+" > "+local_config_dir+"/result_"+str(data[i][0])+"_"+str(data[i][1])+str(data[i][2])+str(data[i][3]))
		elif data[i][2] == "water_pillow":
			os.system("python hotspot_JK2.py "+local_config_dir+"/local"+str(i)+".data water_pillow --no_images  "+str(i)+" > "+local_config_dir+"/result_"+str(data[i][0])+"_"+str(data[i][1])+str(data[i][2])+str(data[i][3]))
		elif data[i][2] == "arumi":
			os.system("python hotspot_JK2.py "+local_config_dir+"/local"+str(i)+".data arumi --no_images  "+str(i)+" > "+local_config_dir+"/result_"+str(data[i][0])+"_"+str(data[i][1])+str(data[i][2])+str(data[i][3]))


    return

#parallel exection
pool = mp.Pool(proc)
callback = pool.map(exec_sim, range(proc))

print "finish" 

