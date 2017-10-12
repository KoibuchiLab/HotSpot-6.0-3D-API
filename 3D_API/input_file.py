#!/usr/bin/python

import os
import sys
import subprocess
import random
import operator

class input_file(object):

	def __init__(self, input_file_name):
		
		#self.__input_file_array = []
		self.__sorted_input = []
		self.process_file(input_file_name)
		#self.__sorted_input = self.process_file(input_file_name);
		#print "self. sorted input "+str(self.__sorted_input)
		self.__layer_array = []
		#self.test = 1234
		
	def get_sorted_file(self):
		return self.__sorted_input
		
	def get_layer_array(self):
		return self.__layer_array
	
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
			self.__layer_array.append(int(line[1])
		
		#print"to sort is "+str(to_sort)	
		self.__layer_array.sort()
		self.__sorted_input =  sorted(to_sort, key=operator.itemgetter(1,0))
		#sortedarray = sorted(to_sort, key=operator.itemgetter(1,0))
		#print "sorted is "+str(sortedarray)
		#return sorted

#input = input_file('test.data')
#print(input.__dict__)
#print "sorted input from test.data is "+str(input.get_sorted_file())