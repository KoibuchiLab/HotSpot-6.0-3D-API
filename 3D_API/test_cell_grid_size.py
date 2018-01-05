#!/usr/bin/python

import sys
import subprocess
import multiprocessing
import os

def parse_perf_data(perf_out,perf_err):
    perf_out
    tokens = perf_err.split()
    #remove commas from values if they exist
    #print perf_out

    #print 'token 0 is ',tokens[0]
    #print tokens
    l1_cache = float(tokens[-8].replace(",", ""))
    llc_cache = float(tokens[-6].replace(",", ""))
    time = float(tokens[-4].replace(",", ""))
    #print l1_cache, llc_cache, time

    return [l1_cache, llc_cache, time]
max_expo = 13
min_expo = -1
max_trials = 10
try:

#Leong

    print 'Leong'
    raw_results = open("./results_LL/raw_gird_size_test_results_LL.txt","w+")
    raw_results.write("LL_version\ntrial\tgrid_size\toutput\ttime\tL1-dcache-load-misses\tLLC-load-misses\n")
    for expo in range(max_expo,min_expo,-1):
        grid_size = 2**expo
        os.system("gcc -Ofast cell_LL.c -o cell_LL -DGRID_SIZE=" + str(grid_size))
        for trial in range(0,max_trials):
            command = "perf stat -e L1-dcache-load-misses -e LLC-load-misses python ./hotspot_LL.py test.data air --no_images"
            procs = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            perf_out, perf_err = procs.communicate()
            perf_out = perf_out.rstrip()
            raw_l1, raw_llc, raw_time = parse_perf_data(perf_out, perf_err)
            raw_results.write(str(trial+1)+"\t"+str(grid_size)+"\t"+str(perf_out)+"\t"+str(raw_time)+"\t"+str(raw_l1)+"\t"+str(raw_llc)+"\n")
            print 'expo ',2**expo,' trial ',trial
    raw_results.close()

#totoki's
    print 'totoki'
    raw_results2 = open("./results_LL/raw_gird_size_test_results.txt","w+")
    raw_results2.write("totoki_version\ntrial\tgrid_size\toutput\ttime\tL1-dcache-load-misses\tLLC-load-misses\n")
    for expo in range(max_expo,min_expo,-1):
        grid_size = 2**expo
        os.system("gcc -Ofast cell.c -o cell -DGRID_SIZE=" + str(grid_size))
        for trial in range(0,max_trials):
            command = "perf stat -e L1-dcache-load-misses -e LLC-load-misses python ./hotspot.py test.data air --no_images"
            procs = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            perf_out, perf_err = procs.communicate()
            perf_out = perf_out.rstrip()
            raw_l1, raw_llc, raw_time = parse_perf_data(perf_out, perf_err)
            raw_results2.write(str(trial+1)+"\t"+str(grid_size)+"\t"+str(perf_out)+"\t"+str(raw_time)+"\t"+str(raw_l1)+"\t"+str(raw_llc)+"\n")
            print 'expo ',2**expo,' trial ',trial
    raw_results2.close()

except IOError:
    print "IOError\nExiting"
