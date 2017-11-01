#!/usr/bin/python

import os
import sys
import subprocess
import random
import operator

class nulldata_file(object):

	def __init__(self, null_data):
		
		self.__null_data = []
		self.__null_layer = []
		self.__name = []
		self.__null_x = []
		self.__null_y = []
		self.__null_x_len = []
		self.__null_y_len = []
		self.process_file(null_data)
		
	def get_null_data(self):
		return self.__null_data
		
	def get_null_layer(self):
		return self.__null_layer
		
	def get_name(self):
		return self.__name
		
	def get_null_x(self):
		return self.__null_x
		
	def get_null_y(self):
		return self.__null_y
		
	def get_null_x_len(self):
		return self.__null_x_len
		
	def get_null_y_len(self):
		return self.__null_y_len
		
	def process_file(self, null_data):
		read = open(null_data)
		null_object = read.readlines()
		read.close
		
		for line in null_object:
			data2 = line[:-1].split(' ')
			#print "data2 is " + str(data2)
			#print "data2[0] is " + str(int(data2[0]))
			self.__null_layer += [int(data2[0])]
			self.__name += [str(data2[1])]
			self.__null_x += [float(data2[2])]
			self.__null_y += [float(data2[3])]
			self.__null_x_len += [float(data2[4])]
			self.__null_y_len += [float(data2[5])]
			