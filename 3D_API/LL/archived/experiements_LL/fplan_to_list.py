#!/usr/bin/python
import os
import sys

read = open('FLOORPLAN/phi7250.flp')
input = read.readlines()
read.close

#print str(input)
to_write = ""

file = open('floorplanclassphi','w')
for lines in input:
	line = lines[:-1].split(' ')
	#print str(line)
	
	to_write += "(\'"+line[0]+"\', "+line[1]+", "+line[2]+", "+line[3]+", "+line[4]+"),\n"
	
file.write(to_write)
file.close