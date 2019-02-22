#!/usr/bin/python
import os
import sys
import math

num = 7 #13
n = 6 #3

for j in range(0, n):
	print ""
	for i in range(0+j*num, num+j*num):
		#print "material:" + str(j) + " freq:" + str(i%num)
		os.system("cat local/result.tmp"+str(i))
#		os.system("tr -d \"\n\" <  local/result.tmp"+str(i))
#		os.system("echo -n \"\t\"")
print "" 
