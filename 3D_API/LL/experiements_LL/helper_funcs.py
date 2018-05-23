#!/usr/bin/python
import os
import sys
import operator

#class helpers(object):
def read_file_to_array(file_name):
	f2 = open(file_name)
	file = f2.readlines()
	f2.close
	
	array = []
	for lines in file:
		#lines = lines[:-1].split
		array.append(lines)
	return array