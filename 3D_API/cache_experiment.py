#!/usr/bin/python

import sys
import subprocess
import multiprocessing

def parse_perf_data(perf_out,perf_err):
    perf_out
    tokens = perf_err.split()
    #remove commas from values if they exist
    #print perf_out
    #print tokens
    l1_cache = float(tokens[9].replace(",", ""))
    llc_cache = float(tokens[11].replace(",", ""))
    time = float(tokens[13].replace(",", ""))

    return [l1_cache, llc_cache, time]

num_cores = multiprocessing.cpu_count()
num_cores = 4
power = int(num_cores**.5)
try:
    raw_results = open("./results_LL/raw_cache_test_results.txt","w+")
    avg_results = open("./results_LL/avg_cache_test_results.txt","w+")
    raw_results.write("core\ttrial\tL1-dcache-load-misses\tLLC-load-misses\ttime\n")
    avg_results.write("core\tL1-dcache-load-misses\tLLC-load-misses\ttime\n")
    for n in range(power,-1,-1):
        command = "perf stat -e L1-dcache-load-misses -e LLC-load-misses python ./hotspot_LL.py test.data air --no_images"
        commands = [command]*(2**n)
        l1_to_avg = []
        llc_to_avg = []
        time_to_avg = []

        for trial in range(0,2**(power-n)):
            procs = [ subprocess.Popen(i, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) for i in commands ]

            for p in procs:
                p.wait()
                perf_out, perf_err = p.communicate()
                raw_l1, raw_llc, raw_time = parse_perf_data(perf_out, perf_err)
                raw_results.write(str(2**n)+"\t"+str(trial+1)+"\t"+str(raw_l1)+"\t"+str(raw_llc)+"\t"+str(raw_time)+"\n")
                l1_to_avg.append((raw_l1))
                llc_to_avg.append((raw_llc))
                time_to_avg.append((raw_time))

        l1_avg = sum((l1_to_avg))/len(l1_to_avg)
        llc_avg = sum((llc_to_avg))/len(llc_to_avg)
        time_avg = sum((time_to_avg))/len(time_to_avg)
        avg_results.write(str(2**n)+"\t"+str(l1_avg)+"\t"+str(llc_avg)+"\t"+str(time_avg)+"\n")
    raw_results.close()
    avg_results.close()
except IOError:
    print "IOError\nExiting"
