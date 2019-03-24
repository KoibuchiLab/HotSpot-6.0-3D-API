# editted by totoki
# last edit date: 2019/03/09
#
# HotSpot need lcf file including length between chips, thickness of chips and so on.
# lcf.py create XXX.lcf.
#
#    * The .lcf file format is the same as the default HotSpot
#        #File Format:
#        <Layer Number>
#        <Lateral heat flow Y/N?>
#        <Power Dissipation Y/N?>
#        <Specific heat capacity in J/(m^3K)>
#        <Resistivity in (m-K)/W>
#        <Thickness in m>
#        <floorplan file>
#
#        #Example
#        0
#        Y
#        Y
#        1.75e6
#        0.01
#        0.00015
#        ev6_3D_core_layer.flp
#
########################################

#!/usr/bin/python
import os
import sys

thickness_of_chip = 0.00004 ## (meter)  default:40um
vertical_distance_between_chips = '1.0e-5' ## (meter) default:10um

def lcf(input, pid):

	layer = input.get_layer_array()

	layer_num = layer[len(layer)-1]
	to_write=""
	#print 'LCF layer num is ', layer_num
	for i in xrange(0, layer_num):

		to_write += str(2*i)+"\nY\nY\n1.75e6\n0.01\n"+str(thickness_of_chip)+"\n"+"test" +str(i+1)+"_"+str(pid)+".flp\n\n"+str(2*i+1)+"\nY\nN\n4e6\n0.25\n"+str(vertical_distance_between_chips)+"\n"+"testTIM_"+str(pid)+".flp\n\n"	#may need to change file  names to add LL

	file = open("test_"+str(pid)+".lcf","w+")
	file.write(to_write)
	file.close
