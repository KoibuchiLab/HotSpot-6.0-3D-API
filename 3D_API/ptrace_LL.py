#!/usr/bin/python
import os

import sys

def ptrace(input, null_data):
	
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
	file = open("test_LL.ptrace","w+")
	file.write(string1)
	file.close
		 
			
			


