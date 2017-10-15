#!/usr/bin/python

import os
import sys
import subprocess
import random
import operator
import re

class input_file(object):

	def __init__(self, input_file_name):
		
		#self.__input_file_array = []
		self.__sorted_input = []
		#self.__sorted_input = self.process_file(input_file_name);
		#print "self. sorted input "+str(self.__sorted_input)
		
		#all the following were populated after main sort
		self.__chip_name = []
		self.__layer_array = []
		self.__chip_x = []
		self.__chip_y = []
		self.__chip_freq = []
		self.__chip_rotate = []
		self.__ptrace_count = []
		#self.test = 1234
		self.process_file(input_file_name)
		self.set_all()
		#self.sorted_to_file()
		#*******call a write to file func so cell can use sorted data file
		
	def get_sorted_file(self):
		return self.__sorted_input
		
	def get_chip_name(self):
		return self.__chip_name
		
		
	def get_layer_array(self):
		return self.__layer_array
		
	def get_chip_x(self):
		return self.__chip_x
		
	def get_chip_y(self):
		return self.__chip_y
		
	def get_chip_freq(self):
		return self.__chip_freq
		
	def get_chip_rotate(self):
		return self.__chip_rotat
		
	def get_chip_name(self):
		return self.__chip_name
		
	def get_ptrace_count(self):
		return self.__ptrace_count
		
	
	def process_file(self, input_file_name):
		read = open(input_file_name)
		input_object = read.readlines()
		read.close
		
		line_number = 1
		to_sort = []
		sortedarray = []
		for line in input_object:
			#print "input line is "+ str(line)
			line = line[:-1].split(' ')
			#print "after line split "+str(line)
			line.append(line_number)
			line_number += 1
			to_sort.append(tuple(line))
			#self.__layer_array.append(int(line[1]))
		
		#print"to sort is "+str(to_sort)	
		self.__layer_array.sort()
		self.__sorted_input =  sorted(to_sort, key=operator.itemgetter(1,0))
		#sortedarray = sorted(to_sort, key=operator.itemgetter(1,0))
		#print "sorted is "+str(sortedarray)
		#return sorted
		
	def set_all(self):
		for data in self.__sorted_input:
			self.__chip_name += [str(data[0])]
			self.__layer_array += [int(data[1])]
			self.__chip_x += [float(data[2])]
			self.__chip_y += [float(data[3])]
			self.__chip_freq += [str(data[4])]
			self.__chip_rotate += [int(data[5])]
		
	def sorted_to_file(self):
		file_name = "sorted_LL.data"
		file = open(file_name,"w")
		to_write = ""
		for tup in self.__sorted_input:
			#s = str(tup).strip(",")
			#s = s.strip("(")
			#s = s.strip(")")
			#s = s.strip("'")
			to_write+=re.sub('[()\',]', "", str(tup))+"\n"
		#print to_write
		file.write(to_write)
		file.close()
			
	def ptrace_count(self):
		layer_tmp = 0;
		count_tmp = 0;
		for data in self.__layer_array:
			#print "data is "+str(int(data))+" and layer tmp is "+str(layer_tmp)
			if int(data)== layer_tmp:
				count_tmp +=1
				layer_tmp = int(data)
			else:	
				count_tmp = 1
				layer_tmp = int(data)
			self.__ptrace_count += [count_tmp]
		
"""
input = input_file('test.data')
input.ptrace_count()
print(input.__dict__)
"""
#print "sorted input from test.data is "+str(input.get_sorted_file())