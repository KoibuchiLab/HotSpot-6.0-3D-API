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

	def __init__(self, population_size=20, num_generation=100,survival=.2):
		LayoutOptimizer()
		LayoutBuilder()
		PowerOptimizer()
		self.__population_size = population_size
		self.__generations = num_generation
		self.__survival = survival
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
		rand_ind = self.__individuals[random.randint(int(len(self.__individuals)*self.__survival),len(self.__individuals)-1)]
		tmp_list = self.__individuals[:int(len(self.__individuals)*self.__survival)]
		tmp_list.append(rand_ind)
		return tmp_list

	def crossover(self):
		while len(self.__individuals) < self.__population_size:
			parent_pool = self.__individuals
			parent1 = random.choice(parent_pool)
			parent2 = random.choice(parent_pool)
			split = random.randint(0,utils.argv.num_chips-1)
			p1_lvl = parent1.get_positions()[split][0]
			p2_lvl = parent2.get_positions()[split][0]
			while (p1_lvl != p2_lvl) and split < len(parent2.get_positions())-1:
				split+=1
				p2_lvl = parent2.get_positions()[split][0]
				print p2_lvl
				utils.abort("testing")
		print 'crossover'


	def mutation(self):
		print 'mutiation'

	def show_list_fitness(self):
		tmp = []
		for i in self.__individuals:
			tmp.append(i.get_fitness())
		print tmp