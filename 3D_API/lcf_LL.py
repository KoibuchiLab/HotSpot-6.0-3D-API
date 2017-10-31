#!/usr/bin/python
import os

import sys

def lcf(input, pid):

	layer = input.get_layer_array()
	
	layer_num = layer[len(layer)-1]
	to_write=""
	
	for i in xrange(0, layer_num):
	
		to_write += str(2*i)+"\nY\nY\n1.75e6\n0.01\n0.00015\n"+"test" +str(i+1)+"_"+str(pid)+".flp\n\n"+str(2*i+1)+"\nY\nN\n4e6\n0.25\n2.0e-05\n"+"testTIM.flp\n\n"	#may need to change file  names to add LL

	file = open("test_"+str(pid)+".lcf","w+")
	file.write(to_write)
	file.close
	