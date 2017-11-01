#!/usr/bin/python

import os
import sys
import subprocess
import random
import operator

class floorplan(object):

	def __init__(self):
	
		self.__base1 = [
		('CORE0_0', 0.004, 0.004, 0, 0),
		('CORE0_1', 0.004, 0.004, 0, 0.004),
		('CORE1_0', 0.004, 0.004, 0, 0.008),
		('CORE1_1', 0.004, 0.004, 0, 0.012),
		('CORE2_0', 0.004, 0.004, 0.012, 0),
		('CORE2_1', 0.004, 0.004, 0.012, 0.004),
		('CORE3_0', 0.004, 0.004, 0.012, 0.008),
		('CORE3_1', 0.004, 0.004, 0.012, 0.012),
		('LLC0', 0.004, 0.004, 0.004, 0.004),
		('LLC1', 0.004, 0.004, 0.004, 0.008),
		('LLC2', 0.004, 0.004, 0.008, 0.004),
		('LLC3', 0.004, 0.004, 0.008, 0.008),
		('NULL0', 0.004, 0.004, 0.004, 0),
		('NULL1', 0.004, 0.004, 0.004, 0.012),
		('NULL2', 0.004, 0.004, 0.008, 0),
		('NULL3', 0.004, 0.004, 0.008, 0.012)
		]

		self.__base2 = [
		('L2C0', 0.00325, 0.00325, 0, 0),
		('L2C1', 0.00325, 0.00325, 0.00325, 0),
		('L2C2', 0.00325, 0.00325, 0.0065, 0),
		('L2C3', 0.00325, 0.00325, 0.00975, 0),
		('L2C4', 0.00325, 0.00325, 0, 0.00325),
		('L2C5', 0.00325, 0.00325, 0.00325, 0.00325),
		('L2C6', 0.00325, 0.00325, 0.0065, 0.00325),
		('L2C7', 0.00325, 0.00325, 0.00975, 0.00325),
		('L2C8', 0.00325, 0.00325, 0, 0.0065),
		('L2C9',0.00325, 0.00325, 0.00325, 0.0065),
		('L2C10', 0.00325, 0.00325, 0.0065, 0.0065),
		('L2C11', 0.00325, 0.00325, 0.00975, 0.0065),
		('CORE0', 0.00325, 0.00325, 0, 0.00975),
		('CORE1', 0.00325, 0.00325, 0.00325, 0.00975),
		('CORE2', 0.00325, 0.00325, 0.0065, 0.00975),
		('CORE3', 0.00325, 0.00325, 0.00975, 0.00975)
		]
		
		self.__e5_2667v4 = [
		('NULL0', 0.0126307, 0.00343128, 0, 0),
		('NULL1', 0.0126307, 0.00257346, 0, 0.0115954),
		('NULL2', 0.0002958, 0.00816408, 0, 0.00343128),
		('NULL3', 0.0013311, 0.00816408, 0.0112996, 0.00343128),
		('0_CORE', 0.00337212, 0.00204102, 0.0002958, 0.00343128),
		('1_CORE', 0.00337212, 0.00204102, 0.0002958, 0.0054723),
		('2_CORE', 0.00337212, 0.00204102, 0.0002958, 0.00751332),
		('3_CORE', 0.00337212, 0.00204102, 0.0002958, 0.00955434),
		('4_CORE', 0.00337212, 0.00204102, 0.00792744, 0.00343128),
		('5_CORE', 0.00337212, 0.00204102, 0.00792744, 0.0054723),
		('6_CORE', 0.00337212, 0.00204102, 0.00792744, 0.00751332),
		('7_CORE', 0.00337212, 0.00204102, 0.00792744, 0.00955434),
		('0_LL', 0.00212976, 0.00204102, 0.00366792, 0.00343128),
		('1_LL', 0.00212976, 0.00204102, 0.00366792, 0.0054723),
		('2_LL', 0.00212976, 0.00204102, 0.00366792, 0.00751332),
		('3_LL', 0.00212976, 0.00204102, 0.00366792, 0.00955434),
		('4_LL', 0.00212976, 0.00204102, 0.00579768, 0.00343128),
		('5_LL', 0.00212976, 0.00204102, 0.00579768, 0.0054723),
		('6_LL', 0.00212976, 0.00204102, 0.00579768, 0.00751332),
		('7_LL', 0.00212976, 0.00204102, 0.00579768, 0.00955434),
		]
		
		self.__phi7250 = [
		('EDGE_0', 0.031500, 0.001809, 0.000000, 0.000000),
		('EDGE_1', 0.031500, 0.001809, 0.000000, 0.018691),
		('EDGE_2', 0.001432, 0.016882, 0.000000, 0.001809),
		('EDGE_3', 0.001432, 0.016882, 0.030068, 0.001809),
		('0_NULL_0', 0.004748, 0.001306, 0.001432, 0.001809),
		('0_NULL_1', 0.001396, 0.001105, 0.003107, 0.003115),
		('0_CORE_0', 0.001676, 0.001105, 0.001432, 0.003115),
		('0_CORE_1', 0.001676, 0.001105, 0.004504, 0.003115),
		('1_NULL_0', 0.004748, 0.001306, 0.006179, 0.001809),
		('1_NULL_1', 0.001396, 0.001105, 0.007855, 0.003115),
		('1_CORE_0', 0.001676, 0.001105, 0.006179, 0.003115),
		('1_CORE_1', 0.001676, 0.001105, 0.009251, 0.003115),
		('2_NULL_0', 0.004748, 0.001306, 0.010927, 0.001809),
		('2_NULL_1', 0.001396, 0.001105, 0.012603, 0.003115),
		('2_CORE_0', 0.001676, 0.001105, 0.010927, 0.003115),
		('2_CORE_1', 0.001676, 0.001105, 0.013999, 0.003115),
		('3_NULL_0', 0.004748, 0.001306, 0.015675, 0.001809),
		('3_NULL_1', 0.001396, 0.001105, 0.017350, 0.003115),
		('3_CORE_0', 0.001676, 0.001105, 0.015675, 0.003115),
		('3_CORE_1', 0.001676, 0.001105, 0.018747, 0.003115),
		('4_NULL_0', 0.004748, 0.001306, 0.020422, 0.001809),
		('4_NULL_1', 0.001396, 0.001105, 0.022098, 0.003115),
		('4_CORE_0', 0.001676, 0.001105, 0.020422, 0.003115),
		('4_CORE_1', 0.001676, 0.001105, 0.023494, 0.003115),
		('5_NULL_0', 0.004748, 0.001306, 0.025170, 0.001809),
		('5_NULL_1', 0.001396, 0.001105, 0.026845, 0.003115),
		('5_CORE_0', 0.001676, 0.001105, 0.025170, 0.003115),
		('5_CORE_1', 0.001676, 0.001105, 0.028242, 0.003115),
		('6_NULL_0', 0.004748, 0.001306, 0.001432, 0.004221),
		('6_NULL_1', 0.001396, 0.001105, 0.003107, 0.005527),
		('6_CORE_0', 0.001676, 0.001105, 0.001432, 0.005527),
		('6_CORE_1', 0.001676, 0.001105, 0.004504, 0.005527),
		('7_NULL_0', 0.004748, 0.001306, 0.006179, 0.004221),
		('7_NULL_1', 0.001396, 0.001105, 0.007855, 0.005527),
		('7_CORE_0', 0.001676, 0.001105, 0.006179, 0.005527),
		('7_CORE_1', 0.001676, 0.001105, 0.009251, 0.005527),
		('8_NULL_0', 0.004748, 0.001306, 0.010927, 0.004221),
		('8_NULL_1', 0.001396, 0.001105, 0.012603, 0.005527),
		('8_CORE_0', 0.001676, 0.001105, 0.010927, 0.005527),
		('8_CORE_1', 0.001676, 0.001105, 0.013999, 0.005527),
		('9_NULL_0', 0.004748, 0.001306, 0.015675, 0.004221),
		('9_NULL_1', 0.001396, 0.001105, 0.017350, 0.005527),
		('9_CORE_0', 0.001676, 0.001105, 0.015675, 0.005527),
		('9_CORE_1', 0.001676, 0.001105, 0.018747, 0.005527),
		('10_NULL_0', 0.004748, 0.001306, 0.020422, 0.004221),
		('10_NULL_1', 0.001396, 0.001105, 0.022098, 0.005527),
		('10_CORE_0', 0.001676, 0.001105, 0.020422, 0.005527),
		('10_CORE_1', 0.001676, 0.001105, 0.023494, 0.005527),
		('11_NULL_0', 0.004748, 0.001306, 0.025170, 0.004221),
		('11_NULL_1', 0.001396, 0.001105, 0.026845, 0.005527),
		('11_CORE_0', 0.001676, 0.001105, 0.025170, 0.005527),
		('11_CORE_1', 0.001676, 0.001105, 0.028242, 0.005527),
		('12_NULL_0', 0.004748, 0.001306, 0.001432, 0.006632),
		('12_NULL_1', 0.001396, 0.001105, 0.003107, 0.007939),
		('12_CORE_0', 0.001676, 0.001105, 0.001432, 0.007939),
		('12_CORE_1', 0.001676, 0.001105, 0.004504, 0.007939),
		('13_NULL_0', 0.004748, 0.001306, 0.006179, 0.006632),
		('13_NULL_1', 0.001396, 0.001105, 0.007855, 0.007939),
		('13_CORE_0', 0.001676, 0.001105, 0.006179, 0.007939),
		('13_CORE_1', 0.001676, 0.001105, 0.009251, 0.007939),
		('14_NULL_0', 0.004748, 0.001306, 0.010927, 0.006632),
		('14_NULL_1', 0.001396, 0.001105, 0.012603, 0.007939),
		('14_CORE_0', 0.001676, 0.001105, 0.010927, 0.007939),
		('14_CORE_1', 0.001676, 0.001105, 0.013999, 0.007939),
		('15_NULL_0', 0.004748, 0.001306, 0.015675, 0.006632),
		('15_NULL_1', 0.001396, 0.001105, 0.017350, 0.007939),
		('15_CORE_0', 0.001676, 0.001105, 0.015675, 0.007939),
		('15_CORE_1', 0.001676, 0.001105, 0.018747, 0.007939),
		('16_NULL_0', 0.004748, 0.001306, 0.020422, 0.006632),
		('16_NULL_1', 0.001396, 0.001105, 0.022098, 0.007939),
		('16_CORE_0', 0.001676, 0.001105, 0.020422, 0.007939),
		('16_CORE_1', 0.001676, 0.001105, 0.023494, 0.007939),
		('17_NULL_0', 0.004748, 0.001306, 0.025170, 0.006632),
		('17_NULL_1', 0.001396, 0.001105, 0.026845, 0.007939),
		('17_CORE_0', 0.001676, 0.001105, 0.025170, 0.007939),
		('17_CORE_1', 0.001676, 0.001105, 0.028242, 0.007939),
		('18_NULL_0', 0.004748, 0.001306, 0.001432, 0.009044),
		('18_NULL_1', 0.001396, 0.001105, 0.003107, 0.010350),
		('18_CORE_0', 0.001676, 0.001105, 0.001432, 0.010350),
		('18_CORE_1', 0.001676, 0.001105, 0.004504, 0.010350),
		('19_NULL_0', 0.004748, 0.001306, 0.006179, 0.009044),
		('19_NULL_1', 0.001396, 0.001105, 0.007855, 0.010350),
		('19_CORE_0', 0.001676, 0.001105, 0.006179, 0.010350),
		('19_CORE_1', 0.001676, 0.001105, 0.009251, 0.010350),
		('20_NULL_0', 0.004748, 0.001306, 0.010927, 0.009044),
		('20_NULL_1', 0.001396, 0.001105, 0.012603, 0.010350),
		('20_CORE_0', 0.001676, 0.001105, 0.010927, 0.010350),
		('20_CORE_1', 0.001676, 0.001105, 0.013999, 0.010350),
		('21_NULL_0', 0.004748, 0.001306, 0.015675, 0.009044),
		('21_NULL_1', 0.001396, 0.001105, 0.017350, 0.010350),
		('21_CORE_0', 0.001676, 0.001105, 0.015675, 0.010350),
		('21_CORE_1', 0.001676, 0.001105, 0.018747, 0.010350),
		('22_NULL_0', 0.004748, 0.001306, 0.020422, 0.009044),
		('22_NULL_1', 0.001396, 0.001105, 0.022098, 0.010350),
		('22_CORE_0', 0.001676, 0.001105, 0.020422, 0.010350),
		('22_CORE_1', 0.001676, 0.001105, 0.023494, 0.010350),
		('23_NULL_0', 0.004748, 0.001306, 0.025170, 0.009044),
		('23_NULL_1', 0.001396, 0.001105, 0.026845, 0.010350),
		('23_CORE_0', 0.001676, 0.001105, 0.025170, 0.010350),
		('23_CORE_1', 0.001676, 0.001105, 0.028242, 0.010350),
		('24_NULL_0', 0.004748, 0.001306, 0.001432, 0.011456),
		('24_NULL_1', 0.001396, 0.001105, 0.003107, 0.012762),
		('24_CORE_0', 0.001676, 0.001105, 0.001432, 0.012762),
		('24_CORE_1', 0.001676, 0.001105, 0.004504, 0.012762),
		('25_NULL_0', 0.004748, 0.001306, 0.006179, 0.011456),
		('25_NULL_1', 0.001396, 0.001105, 0.007855, 0.012762),
		('25_CORE_0', 0.001676, 0.001105, 0.006179, 0.012762),
		('25_CORE_1', 0.001676, 0.001105, 0.009251, 0.012762),
		('26_NULL_0', 0.004748, 0.001306, 0.010927, 0.011456),
		('26_NULL_1', 0.001396, 0.001105, 0.012603, 0.012762),
		('26_CORE_0', 0.001676, 0.001105, 0.010927, 0.012762),
		('26_CORE_1', 0.001676, 0.001105, 0.013999, 0.012762),
		('27_NULL_0', 0.004748, 0.001306, 0.015675, 0.011456),
		('27_NULL_1', 0.001396, 0.001105, 0.017350, 0.012762),
		('27_CORE_0', 0.001676, 0.001105, 0.015675, 0.012762),
		('27_CORE_1', 0.001676, 0.001105, 0.018747, 0.012762),
		('28_NULL_0', 0.004748, 0.001306, 0.020422, 0.011456),
		('28_NULL_1', 0.001396, 0.001105, 0.022098, 0.012762),
		('28_CORE_0', 0.001676, 0.001105, 0.020422, 0.012762),
		('28_CORE_1', 0.001676, 0.001105, 0.023494, 0.012762),
		('29_NULL_0', 0.004748, 0.001306, 0.025170, 0.011456),
		('29_NULL_1', 0.001396, 0.001105, 0.026845, 0.012762),
		('29_CORE_0', 0.001676, 0.001105, 0.025170, 0.012762),
		('29_CORE_1', 0.001676, 0.001105, 0.028242, 0.012762),
		('30_NULL_0', 0.004748, 0.001306, 0.001432, 0.013868),
		('30_NULL_1', 0.001396, 0.001105, 0.003107, 0.015174),
		('30_CORE_0', 0.001676, 0.001105, 0.001432, 0.015174),
		('30_CORE_1', 0.001676, 0.001105, 0.004504, 0.015174),
		('31_NULL_0', 0.004748, 0.001306, 0.006179, 0.013868),
		('31_NULL_1', 0.001396, 0.001105, 0.007855, 0.015174),
		('31_CORE_0', 0.001676, 0.001105, 0.006179, 0.015174),
		('31_CORE_1', 0.001676, 0.001105, 0.009251, 0.015174),
		('32_NULL_0', 0.004748, 0.001306, 0.010927, 0.013868),
		('32_NULL_1', 0.001396, 0.001105, 0.012603, 0.015174),
		('32_CORE_0', 0.001676, 0.001105, 0.010927, 0.015174),
		('32_CORE_1', 0.001676, 0.001105, 0.013999, 0.015174),
		('33_NULL_0', 0.004748, 0.001306, 0.015675, 0.013868),
		('33_NULL_1', 0.001396, 0.001105, 0.017350, 0.015174),
		('33_CORE_0', 0.001676, 0.001105, 0.015675, 0.015174),
		('33_CORE_1', 0.001676, 0.001105, 0.018747, 0.015174),
		('34_NULL_0', 0.004748, 0.001306, 0.020422, 0.013868),
		('34_NULL_1', 0.001396, 0.001105, 0.022098, 0.015174),
		('34_CORE_0', 0.001676, 0.001105, 0.020422, 0.015174),
		('34_CORE_1', 0.001676, 0.001105, 0.023494, 0.015174),
		('35_NULL_0', 0.004748, 0.001306, 0.025170, 0.013868),
		('35_NULL_1', 0.001396, 0.001105, 0.026845, 0.015174),
		('35_CORE_0', 0.001676, 0.001105, 0.025170, 0.015174),
		('35_CORE_1', 0.001676, 0.001105, 0.028242, 0.015174),
		('36_NULL_0', 0.004748, 0.001306, 0.001432, 0.016279),
		('36_NULL_1', 0.001396, 0.001105, 0.003107, 0.017586),
		('36_CORE_0', 0.001676, 0.001105, 0.001432, 0.017586),
		('36_CORE_1', 0.001676, 0.001105, 0.004504, 0.017586),
		('37_NULL_0', 0.004748, 0.001306, 0.006179, 0.016279),
		('37_NULL_1', 0.001396, 0.001105, 0.007855, 0.017586),
		('37_CORE_0', 0.001676, 0.001105, 0.006179, 0.017586),
		('37_CORE_1', 0.001676, 0.001105, 0.009251, 0.017586),
		('38_NULL_0', 0.004748, 0.001306, 0.010927, 0.016279),
		('38_NULL_1', 0.001396, 0.001105, 0.012603, 0.017586),
		('38_CORE_0', 0.001676, 0.001105, 0.010927, 0.017586),
		('38_CORE_1', 0.001676, 0.001105, 0.013999, 0.017586),
		('39_NULL_0', 0.004748, 0.001306, 0.015675, 0.016279),
		('39_NULL_1', 0.001396, 0.001105, 0.017350, 0.017586),
		('39_CORE_0', 0.001676, 0.001105, 0.015675, 0.017586),
		('39_CORE_1', 0.001676, 0.001105, 0.018747, 0.017586),
		('40_NULL_0', 0.004748, 0.001306, 0.020422, 0.016279),
		('40_NULL_1', 0.001396, 0.001105, 0.022098, 0.017586),
		('40_CORE_0', 0.001676, 0.001105, 0.020422, 0.017586),
		('40_CORE_1', 0.001676, 0.001105, 0.023494, 0.017586),
		('41_NULL_0', 0.004748, 0.001306, 0.025170, 0.016279),
		('41_NULL_1', 0.001396, 0.001105, 0.026845, 0.017586),
		('41_CORE_0', 0.001676, 0.001105, 0.025170, 0.017586),
		('41_CORE_1', 0.001676, 0.001105, 0.028242, 0.017586)
		]
		
		self.__tulsa = [
		('CORE_0', 0.00825244, 0.00487644, 0.000250074, 0.00212563),
		('CORE_1', 0.00825244, 0.00487644, 0.000250074, 0.0148794),
		('L2_0', 0.00825244, 0.00220899, 0.000250074, 0.00700207),
		('L2_1', 0.00825244, 0.00220899, 0.000250074, 0.0126704),
		('L3', 0.0107115, 0.0176302, 0.00954449, 0.00212563),
		('AIR_0', 0.0218398, 0.00212563, 0, 0),
		('AIR_1', 0.0218398, 0.00208395, 0, 0.0197558),
		('AIR_2', 0.000250074, 0.0176302, 0, 0.00212563),
		('AIR_3', 0.00104197, 0.0176302, 0.00850252, 0.00212563),
		('AIR_4', 0.0015838, 0.0176302, 0.020256, 0.00212563),
		('AIR_5', 0.00825244, 0.00345936, 0.000250074, 0.00921106)
		]
		
		self.__spreader = [
		('SPREADER', 0.06, 0.06, 0, 0)
		]
	
	def get_floorplan(self, name):
		if (name == 'base1'):
			return self.__base1
		elif (name == 'base2'):
			return self.__base2
		elif (name == 'e5-2667v4'):
			return self.__e5_2667v4
		elif (name == 'phi7250'):
			return self.__phi7250
		elif (name == 'tulsa'):
			return self.__tulsa
		else:
			print "Chip Type Not Valid"
			
	def write_rotate_0(self, chip_name, chip_layer, count, chip_x, chip_y):
	#String chip_name, int chip_layer, int count, float chip_x, float chip_y
		string_to_write = ""
		floorplan = self.get_floorplan(chip_name)
		for lines in floorplan:
			string_to_write+=(str(chip_layer)+'_'+str(count)+lines[0]+" "+str(format(lines[1],'.8f'))+" "+str(format(lines[2],'.8f'))+" "+str(format(lines[3]+chip_x,'.8f'))+" "+str(format(lines[4]+chip_y,'.8f'))+'\n' )
		return string_to_write
		
	def write_rotate_90(self, chip_name, chip_layer, count, chip_x, chip_y, chip_xlen, chip_ylen):
	#String chip_name, int chip_layer, int count, float chip_x, float chip_y, float chip_xlen, float chip_ylen
		string_to_write
		floorplan = self.get_floorplan(chip_name)
		for lines in floorplan:
			string_to_write+=(str(chip_layer)+'_'+str(count)+lines[0]+" "+str(format(lines[2],'.8f'))+" "+str(format(lines[1],'.8f'))+" "+str(format(lines[4]+chip_x,'.8f'))+" "+str(format(chip_x, '.8f'))+" "+str(format(chip_xlen-lines[3]-lines[1]+chip_y,'.8f'))+"\n" )
		return string_to_write
		
	def write_rotate_180(self, chip_name, chip_layer, count, chip_x, chip_y, chip_xlen, chip_ylen):
	#String chip_name, int chip_layer, int count, float chip_x, float chip_y, float chip_xlen, float chip_ylen
		array_to_write = []
		floorplan = self.get_floorplan(chip_name)
		for lines in floorplan:
			array_to_write.append(str(chip_layer)+'_'+str(count)+lines[0]+" "+str(format(lines[1],'.8f'))+" "+str(format(lines[2],'.8f'))+" "+str(format(chip_xlen,'.8f'))+" "+str(format(chip_xlen-lines[3]+lines[1]+chip_x,'.8f'))+" "+str(format(chip_ylen-lines[4]-lines[2]+chip_y,'.8f'))+'\n' )
		return array_to_write
		
	def write_rotate_270(self, chip_name, chip_layer, count, chip_x, chip_y, chip_xlen, chip_ylen):
	#String chip_name, int chip_layer, int count, float chip_x, float chip_y, float chip_xlen, float chip_ylen
		array_to_write = []
		floorplan = self.get_floorplan(chip_name)
		for lines in floorplan:
			array_to_write.append(str(chip_layer)+'_'+str(count)+lines[0]+" "+str(format(lines[2],'.8f'))+" "+str(format(lines[1],'.8f'))+" "+str(format(chip_ylen-lines[4]-lines[2]+chip_x,'.8f'))+" "+str(format(lines[3]+chip_y,'.8f'))+'\n' )
		return array_to_write
