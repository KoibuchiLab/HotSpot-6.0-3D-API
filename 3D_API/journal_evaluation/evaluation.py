#!~/local/bin/python
import os
import multiprocessing as mp
import time

local_config_dir = "local"
proc = 3 
i = 0
j = 0


## conventional 3D stacking
#name = ["e5_vertical_1","e5_vertical_2","e5_vertical_3","e5_vertical_4","e5_vertical_5","e5_vertical_6","e5_vertical_7","e5_vertical_8","e5_vertical_9","e5_vertical_10","e5_vertical_11","e5_vertical_12"]

## CoC 2+2 stacking
name = ["e5_coc2_4","e5_coc2_6","e5_coc2_8","e5_coc2_10","e5_coc2_12","e5_coc2_14","e5_coc2_16","e5_coc2_18"]

## CoC 4+5 stacking
#name = ["e5_coc4_5","e5_coc4_9","e5_coc4_14","e5_coc4_18", "e5_coc4_23"]


mat = ["air"]
os.system("rm -f "+local_config_dir+"/result.tmp*")
count = len(name)


os.system("gcc -o cell cell.c")

#subprocess command
def exec_sim(p):
    ini = count * p / proc
    fin = count * (p+1) / proc
    for i in xrange(ini, fin):
		print i
		start = time.time()
#		os.system("python hotspot_JK.py "+str(name[i])+".data air --no_images  "+str(i)+" > "+local_config_dir+"/result.tmp"+str(i))
		os.system("python hotspot_JK.py "+str(name[i])+".data air --no_images  "+str(i))
		elapsed_time = time.time() - start
		print i,name[i], elapsed_time

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

