#!/usr/bin/python

import networkx as nx
import os
import random
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
	def __init__(self):

		self.__layout = self.init_individual()
		self.__fitness = -1
		self.__diameter = self.__layout.get_diameter()
		self.__ASPL = self.__layout.get_ASPL()
		self.__edges = self.__layout.get_num_edges()
		self.__power = -1
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

	def init_individual(self):
		### create classes for individuals and store classes in list below###
		#list_of_individuals = []
		#while len(list_of_individuals) < self.__population_size:
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
		#layout.draw_in_3D(None, True)
		#individual = inidividual(layout)
		#print 'layout is \n',layout.get_chip_positions()
		#list_of_individuals.append(individual)
		#print 'inidividual layout is \n', individual.get_layout().get_chip_positions()
		#tmp = individual.get_layout()
		#utils.abort("testing")
		return layout

class GeneticAlgorithm(object):

	def __init__(self, population_size=20, num_generation=100,survival=.2, mutation_rate = .3):
		LayoutOptimizer()
		LayoutBuilder()
		PowerOptimizer()
		self.__population_size = population_size
		self.__generations = num_generation
		self.__survival = survival
		self.__mutation_rate = mutation_rate
		self.__individuals = self.init_population()
		#print len(self.__individuals)

	def init_population(self):
		inidividuals = []
		while len(inidividuals) < self.__population_size:
			individual = Individual()
			inidividuals.append(individual)
			#print individual.get_layout()
		return inidividuals

	def simple_ga(self):
		for generation in xrange(self.__generations):
			self.fitness()
			#self.show_list_fitness()
			#print 'indi list len pre is ',len(self.__individuals)
			self.__individuals = self.selection()
			#self.show_list_fitness()
			#print 'indi list len POST is ',len(self.__individuals)
			#print 'individuals is ', self.__individuals
			self.crossover()
			self.mutation()
			utils.abort("simple ga")
		return [layout, power, temp]


	def fitness(self):
		#print 'fitness'
		for individual in self.__individuals:
			result = find_maximum_power_budget(individual.get_layout())
			power = result[0][0]
			temp = result[-1]
			ASPL = individual.get_ASPL()
			diameter = individual.get_diameter()
			edges = individual.get_edges()
			individual.set_power(power)
			individual.set_temperature(temp)
			individual.set_fitness((ASPL+diameter+temp-(power)-(edges)))
			#print individual.get_fitness()
		return

	def selection(self):
		print 'selection'
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

		"""
		for individual in self.__individuals:
			print individual.get_positions()
		"""

		#parent_pool = self.__individuals
		max_parent_index = len(self.__individuals)-1
		while len(self.__individuals) < self.__population_size:
			#parent1 = random.choice(parent_pool).get_positions()
			#parent2 = random.choice(parent_pool).get_positions()
			parent1 = self.__individuals[random.randint(0,max_parent_index)].get_positions()
			parent2 = self.__individuals[random.randint(0,max_parent_index)].get_positions()

			side_split =utils.pick_random_element([0,1])
			#count = 0
			#for x in xrange(10000):
			child1, child2 = [], []
			side_split = 1
			if side_split == 1:
				x_center = parent1[0][1]

				for chip in parent1:
					if chip[1]>x_center:
						child2.append(chip)
					else:
						child1.append(chip)
				for chip in parent2:
					if chip[1]>x_center:
						child1.append(chip)
					else:
						child2.append(chip)
			else:
				y_center = parent1[0][2]
				for chip in parent1:
					if chip[1]>y_center:
						child2.append(chip)
					else:
						child1.append(chip)
				for chip in parent2:
					if chip[1]>y_center:
						child1.append(chip)
					else:
						child2.append(chip)
			try:
				tmp1 = Layout(utils.argv.chip, child1, utils.argv.medium, utils.argv.overlap,[])
				tmp2 = Layout(utils.argv.chip, child2, utils.argv.medium, utils.argv.overlap,[])
			except:
				continue
			self.__individuals.append(tmp1)
			self.__individuals.append(tmp2)

			"""
			#count+=1
			#print count
			tmp1.draw_in_3D(None,True)
			tmp2.draw_in_3D(None,True)
			split = random.randint(0,utils.argv.num_chips-1)
			#p1_lvl = parent1.get_positions()[split][0]
			#p2_lvl = parent2.get_positions()[split][0]
			chip_list  = parent1[:split]+parent2[split:]
			for i in parent2[split:]:

				tmp1.add_new_chip(i)
			tmp1 = Layout(utils.argv.chip, parent1[:split]+parent2[split:], utils.argv.medium, utils.argv.overlap,[])
			while (p1_lvl != p2_lvl) and split < len(parent2.get_positions())-1:
				split+=1
				p2_lvl = parent2.get_positions()[split][0]
				print p2_lvl
			"""
		print 'crossover'


	def mutation(self):
		for individual in self.__individuals:
			if random.uniform(0.0,1.0)<= self.__mutation_rate:
				mutant_chip = random.randint(1,utils.argv.num_chips-1)
				layout = individual.get_layout()
				layout.remove_chip(mutant_chip)
				new_chip_neighbor = random.randint(0,len(self.__individuals)-1)
				new_chip = layout.get_random_feasible_neighbor_position(new_chip_neighbor)
				print new_chip
				layout.add_new_chip(layout.get_random_feasible_neighbor_position())
				utils.abort("testing")
		print 'mutiation'


	def show_list_fitness(self):
		tmp = []
		for i in self.__individuals:
			tmp.append(i.get_fitness())
		print tmp