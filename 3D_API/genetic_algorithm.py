#!/usr/bin/python

import networkx as nx
import os
import random
import math
import subprocess
import sys
from math import sqrt
#from numba import jit
import os
import sys
import argparse
from argparse import RawTextHelpFormatter
from chip import Chip
from layout_optimizer import LayoutOptimizer
from layout_optimizer import optimize_layout
import utils
from layout import *
from power_optimizer import *
import utils

class Individual(object):
	def __init__(self,Layout=None):

		self.__layout = self.init_individual(Layout)
		self.__fitness = -1
		self.__diameter = self.__layout.get_diameter()
		self.__ASPL = self.__layout.get_ASPL()
		self.__edges = self.__layout.get_num_edges()
		self.__power = []
		self.__temperature = -1
		self.__density = -1

	def get_layout(self):
		return self.__layout

	def get_fitness(self):
		return self.__fitness

	def get_positions(self):
		return self.__layout.get_chip_positions()

	def get_diameter(self):
		return self.__diameter

	def get_ASPL(self):
		return self.__ASPL

	def get_edges(self):
		return self.__edges

	def get_power(self):
		return self.__power

	def get_temperature(self):
		return self.__temperature

	def get_density(self):
		return self.__density

	def set_positions(self,layout_positions):
		self.__layout.__chip_positions = layout_positions

	def set_fitness(self,fitness_score):
		self.__fitness = fitness_score

	def set_diameter(self,diameter):
		self.__diameter = diameter

	def set_ASPL(self,ASPL):
		self.__ASPL = ASPL

	def set_edges(self,edges):
		self.__edges = edges

	def set_power(self,power):
		self.__power = power

	def set_temperature(self,temperature):
		self.__temperature = temperature

	def set_density(self,density):
		self.__density = density

	def init_individual(self, Layout):
		### create classes for individuals and store classes in list below###
		#list_of_individuals = []
		#while len(list_of_individuals) < self.__population_size:
		if Layout == None:
			layout = LayoutBuilder.compute_cradle_layout(3)
			while layout.get_num_chips()<utils.argv.num_chips:
				random_chip = utils.pick_random_element(range(0, layout.get_num_chips()))
				try:
					layout.add_new_chip(layout.get_random_feasible_neighbor_position(random_chip))
					#print 'layout size =',layout.get_num_chips()
				except:
					utils.info(1,"Adding in ga init_individual failed")
					continue
			if layout.get_num_chips() < utils.argv.num_chips:
				print 'layout = ',layout.get_num_chips(),' num chips suppose to be ',utils.argv.num_chips
				utils.abort("in ga init individuals")
		else:
			layout = Layout
		#layout.draw_in_3D(None, True)
		#individual = inidividual(layout)
		#print 'layout is \n',layout.get_chip_positions()
		#list_of_individuals.append(individual)
		#print 'inidividual layout is \n', individual.get_layout().get_chip_positions()
		#tmp = individual.get_layout()
		#utils.abort("testing")
		return layout

class GeneticAlgorithm(object):

	def __init__(self, population_size=50, num_generation=500,survival=.25, mutation_rate = .4):
		LayoutOptimizer()
		LayoutBuilder()
		PowerOptimizer()
		self.__population_size = population_size
		self.__generations = num_generation
		self.__survival = survival
		self.__mutation_rate = mutation_rate
		self.__individuals = self.init_population(self.__population_size)
		#print len(self.__individuals)

	def init_population(self,size):
		inidividuals = []
		while len(inidividuals) < size:
			individual = Individual()
			inidividuals.append(individual)
			#print individual.get_layout()
		return inidividuals

	def simple_ga(self):
		count = 0
		for generation in xrange(self.__generations):
			count += 1
			print count
			self.fitness()
			#self.show_list_fitness()
			#print 'indi list len pre is ',len(self.__individuals)
			self.__individuals = self.selection()
			#self.show_list_fitness()
			#print 'indi list len POST is ',len(self.__individuals)
			#print 'individuals is ', self.__individuals
			#self.show_ind_lengths()
			self.crossover()
			#self.show_ind_lengths()
			self.mutation()
			#self.show_ind_lengths()
		self.__individuals = self.selection()
		top = self.__individuals[0]
		layout = top.get_layout()
		power = top.get_power()
		temp = top.get_temperature()
		#utils.abort("simple ga")
		return [layout, power, temp]


	def fitness(self):
		#print 'fitness'
		for individual in self.__individuals:
			result = find_maximum_power_budget(individual.get_layout())
			power = result[0]
			#print power
			#utils.abort("power")
			temp = result[-1]
			ASPL = individual.get_ASPL()
			diameter = individual.get_diameter()
			edges = individual.get_edges()
			individual.set_power(power)
			individual.set_temperature(temp)
			individual.set_fitness((ASPL+diameter+temp-(power[0])-(edges)))
			#print individual.get_fitness()
		return

	def selection(self):
		#print 'selection'
		#print self.__individuals
		if not None in self.__individuals:
			self.__individuals = sorted(self.__individuals, key=lambda individual: individual.get_fitness())
		"""
		for i in self.__individuals:
			print i.get_fitness()
		"""
		tmp_list = self.__individuals[:int(len(self.__individuals)*self.__survival)]
		if int(len(self.__individuals)*self.__survival)%2 !=0:
			rand_ind = self.__individuals[random.randint(int(len(self.__individuals)*self.__survival),len(self.__individuals)-1)]
			tmp_list.append(rand_ind)

		return tmp_list

	def crossover(self):
		#print 'crossover'

		"""
		for individual in self.__individuals:
			print individual.get_positions()
		"""

		#parent_pool = self.__individuals
		max_parent_index = len(self.__individuals)-1
		#print max_parent_index
		#print "individuals = ",len(self.__individuals)
		attempts = 0
		found_all = False
		while len(self.__individuals) < self.__population_size and attempts<0:
			attempts += 1
			#parent1 = random.choice(parent_pool).get_positions()
			#parent2 = random.choice(parent_pool).get_positions()
			ran_index1 = random.randint(0,max_parent_index)
			ran_index2 = random.randint(0,max_parent_index)
			parent1 = self.__individuals[ran_index1].get_positions()
			parent2 = self.__individuals[ran_index2].get_positions()
			#print 'p1 index = ', ran_index1,' p2 index = ',ran_index2
			#utils.abort("HOLD")
			if len(parent1) != len(parent2):
				#print 'parent1 len = ',len(parent1),' parent2 len = ',len(parent2)
				#print 'p1 index = ', ran_index1,' p2 index = ',ran_index2
				utils.abort("GA crossover, serious error, parents should be the same length")
			child = []
			parent1 = sorted(parent1, key=lambda chip: chip[1])
			parent2 = sorted(parent2, key=lambda chip: chip[1])

			"""
			get center of mass of two layouts
			- check values and see if they are equal
			 - if not find index where values are equal
			- parent with the higher index value makes the first part of child
			- parent with smaller value makes the last part of child
			"""
			orient = random.randint(1,2)
			#orient = 1
			utils.info(3,"GA crossover, orientation =  "+str( orient))

			middle = int(len(parent1)*.5)
			center1 = parent1[middle][orient]
			center2 = parent2[middle][orient]
			new_mid = middle
			new_parent = True
			check_other = True
			#print 'centers are ',center1, center2
			if center1 != center2:
			#	print 'in if centers are ',center1, center2
				utils.info(3,"ga crossover: rebalancing")
				for i, chip in enumerate(parent2):
					if chip[orient] != center1:
						continue
					new_mid = i
					center2 = chip[orient]
					new_parent=False
					check_other = False
				if check_other == False:
					for j, chip in enumerate(parent1):
						if chip[orient] != center2:
							continue
						new_mid = i
						center1 = chip[orient]
						new_parent=False
						check_other = False

					#catch not in parent2
			if new_parent:
				utils.info(3,"ga crossover: new parent needed")
				continue
			new_mid+=1
			if middle > new_mid:
			#	print 'parent 1 = ',len(parent1[:middle]),'parent 2 = ',len(parent2[new_mid:])
			#	print 'parent 1 = ',(parent1[middle]),'parent 2 = ',(parent2[new_mid])
				child = parent1[:middle]+parent2[new_mid:]
			elif middle < new_mid:
				#print '!!!!!!!!!!!!else if'
			#	print 'parent 1 = ',len(parent1[:middle]),'parent 2 = ',len(parent2[new_mid:])
			#	print 'parent 1 = ',(parent1[middle]),'parent 2 = ',(parent2[new_mid])
				child = parent2[:new_mid]+parent1[middle:]
			else:
				#print "mid = ",middle, ' new mid = ',new_mid
				continue
			#print 'child len ', len(child)
			child = child[:len(parent1)]
			#print 'child len is now ', len(child)

			if utils.argv.num_chips != len(child) or utils.argv.num_chips != len(child):
				utils.abort("GA crossover, children are smaller than parents")
				continue
			if len(parent1) != len(child) or len(parent2) != len(child):
				utils.abort("GA crossover, children are smaller than parents")
				continue
			try:
				tmp1 = Layout(utils.argv.chip, child, utils.argv.medium, utils.argv.overlap,[])
				#tmp2 = Layout(utils.argv.chip, child, utils.argv.medium, utils.argv.overlap,[])
			except:
				#utils.abort("add error")
				continue
			#print 'tmp len ',len(tmp1.get_chip_positions())
			self.__individuals.append(Individual(tmp1))
			#print "now individuals = ",len(self.__individuals)
		#tmp1.draw_in_3D(None,True)
		if len(self.__individuals) != self.__population_size:
			#print "current pop size = ",len(self.__individuals)
			remaining = self.__population_size-len(self.__individuals)
			#print "remaining is ",remaining
			new_ind = self.init_population(remaining)
			self.__individuals += new_ind
			#print "ga cross over ind size = ",len(self.__individuals)
			#utils.abort("GA crossover, ran out of crossover attemps")

	def mutation(self):
		#print 'mutiation'
		added = False
		attemps = 0
		count = 0
		new_add = None
		original_len = -1
		chip_to_remove = None
		for k, individual in enumerate(self.__individuals):
			if random.uniform(0.0,1.0)<= self.__mutation_rate:
				layout = individual.get_layout()
				tmp = Layout(utils.argv.chip, layout.get_chip_positions(), utils.argv.medium, utils.argv.overlap,[])
				articulation_list = list(nx.articulation_points(tmp.get_graph()))
				#print 'articulation points are = ',articulation_list
				original_len = len(tmp.get_chip_positions())
				mutant_index = random.randint(1,utils.argv.num_chips-1)
				mutant_chip = tmp.get_chip_positions()[mutant_index]
				removed = False
				#print 'indi mut index = ',k
				if mutant_index in articulation_list:
					continue
				try:
					tmp.remove_chip(mutant_index)
					removed = True
				#	print "chip removed"
					#layout.add_new_chip(mutant_index)
					#individual.get_layout().remove_chip(mutant_index)
				except:
					#print "pre add remove layout len = ",len(layout.get_chip_positions())
					#layout.add_new_chip(mutant_chip)
				#	print "remove layout len = ",len(tmp.get_chip_positions())
					continue

				while removed and attemps<100:
					attemps += 1
					try:
						new_chip_neighbor = random.randint(0,len(self.__individuals)-1)
						new_add = tmp.get_random_feasible_neighbor_position(new_chip_neighbor)
						tmp.add_new_chip(new_add)
						removed=False
				#		print "chip added"
					except:
				#		print "ADD ERROR"
				#		print 'removed is ',removed
						continue
				#print "removed is what ",removed

				#print 'mutation len = ', len(tmp.get_chip_positions())
				if utils.argv.num_chips != len(tmp.get_chip_positions()):
					continue
					#utils.abort("GA mutation, mutation error, lengths diff")
				layout = tmp
				# find bridge
				#new_chip = layout.get_random_feasible_neighbor_position(new_chip_neighbor)
		#print self.__individuals

	def show_list_fitness(self):
		tmp = []
		for i in self.__individuals:
			tmp.append(i.get_fitness())
		print tmp

	def show_ind_lengths(self):
		show = ""
		for i, chip in enumerate(self.__individuals):
			show += "["+str(i)+"] = "+str(len(chip.get_positions()))+", "
		print show