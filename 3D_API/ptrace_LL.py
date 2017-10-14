#!/usr/bin/python
import os

import sys

def ptrace(input, null_data):
	
	"""
	if (len(sys.argv) != 2):
			sys.stderr.write("Usage: " + sys.argv[0] + " <input file (.dat)>\n")
			sys.exit(1)

	input_file = sys.argv[1]
	if not os.access(input_file, os.R_OK):
			sys.stderr.write("Can't read file '"+input_file+"'\n")
			sys.exit(1)

	"""

	f = open('sorted.data')
	chip_lines = f.readlines()
	f.close

	f2 = open('null.data')
	null_lines = f2.readlines()
	f2.close

	os.system("rm -f test.ptrace")
	os.system("touch test.ptrace") 

	layer_tmp = 0;
	count_tmp = 0;

	chip_layer, count, freq, chip_name = [], [], [], []

	for line in chip_lines:
		data = line[:-1].split(' ')
		chip_name += [str(data[0])]
		chip_layer += [int(data[1])]
		freq += [str(data[4])]
		#print "data[1] is "+str(int(data[1]))+" and layer tmp is "+str(layer_tmp)
		if int(data[1])== layer_tmp:
			count_tmp +=1
			layer_tmp = int(data[1])
		else:	
			count_tmp = 1
			layer_tmp = int(data[1])
		count += [count_tmp]
		
	input.ptrace_count()
	"""
	print "ptrace count "+str(count)
	print "input object count "+str(input.get_ptrace_count())
	print "ptrace layers "+str(chip_layer)
	print "input object layer "+str(input.get_layer_array())
	"""
	null_layer, null_name= [],[] 
	for line3 in null_lines:
		data2 = line3[:-1].split(' ')
		null_layer += [int(data2[0])]
		null_name += [str(data2[1])]

	for i in xrange(0, len(freq)):
		for j in xrange(0, len(chip_layer)):
			if i == chip_layer[j]-1:
				os.system("cat PTRACE/"+ str(chip_name[j]) +"-" + str(freq[j]) + ".ptrace | awk 'NR==1{for(i=1;i<=NF;i++){printf \"" +str(chip_layer[j]) + "_" + str(count[j]) + "\"$i\" \" }}' >> test.ptrace")
				#print "cat PTRACE/"+ str(chip_name[j]) +"-" + str(freq[j]) + ".ptrace | awk 'NR==1{for(i=1;i<=NF;i++){printf \"" +str(chip_layer[j]) + "_" + str(count[j]) + "\"$i\" \" }}' >> test.ptrace"
		for j in xrange(0, len(null_layer)):
			if i == null_layer[j]-1:
				os.system("echo -n \""+ str(null_name[j])+" \" >> test.ptrace")
				#print "echo -n \""+ str(null_name[j])+" \" >> test.ptrace"

	os.system("echo '' >> test.ptrace")
	for i in xrange(0, len(freq)):	 
		for j in xrange(0, len(freq)):
			if i == chip_layer[j]-1:
				os.system("cat PTRACE/" + str(chip_name[j]) +"-" + str(freq[j]) + ".ptrace | awk 'NR==2{for(i=1;i<=NF;i++){printf $i\" \" }}' >> test.ptrace")
		for j in xrange(0, len(null_layer)):
			if i == null_layer[j]-1:
				os.system("echo -n \"0 \" >> test.ptrace") 
	os.system("echo '' >> test.ptrace")

		 
			
			


