#!/usr/bin/python
import os
import sys

chip_names = ["base2", "base2CPU", "base2DRAM", "base2L2", "base2L2DRAM"]
freqs = [1000, 1200, 1400, 1600, 1800, 2000]
block_size = 13000/4  #um
row = 4 #block num of row
col = 4 #block num of col

for chip_name in xrange(0, len(chip_names)): 
    for freq in xrange(0, len(freqs)):  
        os.system("rm FLOOR/"+str(chip_names[chip_name])+"-" +str(freqs[freq])+".flp")
        os.system("touch FLOOR/"+str(chip_names[chip_name])+ "-"+str(freqs[freq])+".flp")
        for x in xrange(0, row):
            for y in xrange(0, col):
                os.system("echo 'Core"+str(x*row+y)+":\n' >> FLOOR/"+str(chip_names[chip_name])+"-" + str(freqs[freq])+".flp")
                os.system("echo '\tposition\t "+ str(y*block_size)+", "+str(x*block_size)+ ";' >> FLOOR/"+str(chip_names[chip_name])+"-" +str(freqs[freq])+ ".flp")
                os.system("echo '\tdime:qnsion\t "+ str(block_size)+", "+str(block_size)+ ";' >> FLOOR/"+str(chip_names[chip_name])+"-" +str(freqs[freq])+ ".flp")
                power = open("PTRACE/"+str(chip_names[chip_name])+"-"+str(freqs[freq])+".ptrace").readlines()[1].strip().split()[x*row+y]
                os.system("echo '\tpower values\t "+ str(power)+";' >> FLOOR/"+str(chip_names[chip_name])+"-" +str(freqs[freq])+ ".flp")


chip_names = ["base3"]
freqs = [1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600]
for chip_name in xrange(0, len(chip_names)): 
    for freq in xrange(0, len(freqs)):  
        os.system("rm FLOOR/"+str(chip_names[chip_name])+"-" +str(freqs[freq])+".flp")
        os.system("touch FLOOR/"+str(chip_names[chip_name])+ "-"+str(freqs[freq])+".flp")
        for x in xrange(0, row):
            for y in xrange(0, col):
                os.system("echo 'Core"+str(x*row+y)+":\n' >> FLOOR/"+str(chip_names[chip_name])+"-" + str(freqs[freq])+".flp")
                os.system("echo '\tposition\t "+ str(y*block_size)+", "+str(x*block_size)+ ";' >> FLOOR/"+str(chip_names[chip_name])+"-" +str(freqs[freq])+ ".flp")
                os.system("echo '\tdime:qnsion\t "+ str(block_size)+", "+str(block_size)+ ";' >> FLOOR/"+str(chip_names[chip_name])+"-" +str(freqs[freq])+ ".flp")
                power = open("PTRACE/"+str(chip_names[chip_name])+"-"+str(freqs[freq])+".ptrace").readlines()[1].strip().split()[x*row+y]
                os.system("echo '\tpower values\t "+ str(power)+";' >> FLOOR/"+str(chip_names[chip_name])+"-" +str(freqs[freq])+ ".flp")
