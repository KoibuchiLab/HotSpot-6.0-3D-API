# edited by totoki
# last edit date: 2019/03/09
#
# HotSpot need power trace file.
# ptrace.py create XXX.ptrace including power trace data of every chip by reffering PTRACE/XXX.ptrace. 
# when you add a new chip, you have to add PTRACE/XXX.ptrace.
# 
#
# (example) XXX.ptrace
#1_1DRAM0 1_1DRAM1 1_1DRAM2 1_1DRAM3 1_1L2C0 1_1L2C1 1_1L2C2 1_1L2C3 1_1L2C4 1_1L2C5 1_1L2C6 1_1L2C7 1_1CORE0 1_1CORE1 1_1CORE2 1_1CORE3 NULL2 2_1DRAM0 2_1DRAM1 2_1DRAM2 2_1DRAM3 2_1L2C0 2_1L2C1 2_1L2C2 2_1L2C3 2_1L2C4 2_1L2C5 2_1L2C6 2_1L2C7 2_1CORE0 2_1CORE1 2_1CORE2 2_1CORE3 NULL3 3_1DRAM0 3_1DRAM1 3_1DRAM2 3_1DRAM3 3_1L2C0 3_1L2C1 3_1L2C2 3_1L2C3 3_1L2C4 3_1L2C5 3_1L2C6 3_1L2C7 3_1CORE0 3_1CORE1 3_1CORE2 3_1CORE3 NULL4 4_1DRAM0 4_1DRAM1 4_1DRAM2 4_1DRAM3 4_1L2C0 4_1L2C1 4_1L2C2 4_1L2C3 4_1L2C4 4_1L2C5 4_1L2C6 4_1L2C7 4_1CORE0 4_1CORE1 4_1CORE2 4_1CORE3 NULL5
#0.83 0.83 0.83 0.83 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 4.8923 4.8923 4.8923 4.8923 0 0.83 0.83 0.83 0.83 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 4.8923 4.8923 4.8923 4.8923 0 0.83 0.83 0.83 0.83 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 4.8923 4.8923 4.8923 4.8923 0 0.83 0.83 0.83 0.83 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 2.2934 4.8923 4.8923 4.8923 4.8923 0
#
# Each block is renamed to [layer number]+"_"+[block name]
# floor.py outputs the information of each layer as a separate file, but ptrace.py collectively outputs the information of all layers.
#
###############################################################################################

#!/usr/bin/python
import os

import sys

def ptrace(input, null_data, pid):

	input.ptrace_count()

	freqll = input.get_chip_freq()
	chip_layerll = input.get_layer_array()
	chip_namell = input.get_chip_name()
	countll = input.get_ptrace_count()

	null_layerll = null_data.get_null_layer()
	null_namell = null_data.get_name()

	string1 = ""
	string2 = ""

	for i in xrange(0, len(freqll)):
		for j in xrange(0, len(chip_layerll)):
			if i == chip_layerll[j]-1:
				read = open("PTRACE/"+ str(chip_namell[j]) +"-" + str(freqll[j]) + ".ptrace")
				ptrace_file = read.readlines()
				read.close
				ptrace_file[0] = ptrace_file[0].strip(" \n") #to catch when files have spaces before newline like in e5-2667v4-cg2400.ptrace
				ptrace_file[1] = ptrace_file[1].strip(" \n")
				ptrace_file[0] = ptrace_file[0].split(' ')
				ptrace_file[1] = ptrace_file[1].split(' ')

				for k in xrange(0, len(ptrace_file[0])):
					string1+=(str(chip_layerll[j]) + "_" + str(countll[j]) + ptrace_file[0][k] + " ")

				for stuff in ptrace_file[1]:
					string2+=(stuff+" ")

		for j in xrange(0, len(null_layerll)):
			if i == null_layerll[j]-1:
				string1+=(str(null_namell[j])+" ")
				string2+=("0 ")

	string1+=("\n"+string2+"\n")
	file = open("test_"+str(pid)+".ptrace","w+")
	file.write(string1)
	file.close
