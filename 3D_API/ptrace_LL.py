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
				#print string1

				#string1.append("\n")
				
				for stuff in ptrace_file[1]:
					string2+=(stuff+" ")
				
				#string2.append("\n")
				
				os.system("cat PTRACE/"+ str(chip_namell[j]) +"-" + str(freqll[j]) + ".ptrace | awk 'NR==1{for(i=1;i<=NF;i++){printf \"" +str(chip_layerll[j]) + "_" + str(countll[j]) + "\"$i\" \" }}' >> test.ptrace")
				#print "cat PTRACE/"+ str(chip_name[j]) +"-" + str(freq[j]) + ".ptrace | awk 'NR==1{for(i=1;i<=NF;i++){printf \"" +str(chip_layer[j]) + "_" + str(count[j]) + "\"$i\" \" }}' >> test.ptrace"
				print "part 1 chip name is "+ str(chip_name[j])+"-" + str(freqll[j])+" "+str(chip_layerll[j]) + "_" + str(countll[j])
		for j in xrange(0, len(null_layerll)):
			if i == null_layerll[j]-1:
				string1+=(str(null_namell[j])+" ")
				string2+=("0 ")
				os.system("echo -n \""+ str(null_namell[j])+" \" >> test.ptrace")
				#print "echo -n \""+ str(null_name[j])+" \" >> test.ptrace"

	os.system("echo '' >> test.ptrace") #newline
	for i in xrange(0, len(freqll)):	 
		for j in xrange(0, len(freqll)):
			if i == chip_layerll[j]-1:
				os.system("cat PTRACE/" + str(chip_namell[j]) +"-" + str(freqll[j]) + ".ptrace | awk 'NR==2{for(i=1;i<=NF;i++){printf $i\" \" }}' >> test.ptrace")
				#print "part 2 chip name is "+ str(chip_name[j])
		for j in xrange(0, len(null_layerll)):
			if i == null_layerll[j]-1:
				os.system("echo -n \"0 \" >> test.ptrace") 
	os.system("echo '' >> test.ptrace") #newline
	
	#append string2 to end of string1 and add newline after both trings thren write
	string1+=("\n"+string2+"\n")
	file = open("test_LL.ptrace","w")
	file.write(string1)
	file.close
		 
			
			


