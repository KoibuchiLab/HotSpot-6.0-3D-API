#!/usr/bin/python

import sys
import random

class argv(object):
	global argv
    	argv = None

	global abort
	def abort(message):
        	sys.stderr.write("Error: " + message + "\n")
        	sys.exit(1)

	global info
	def info(verbosity, message):
		if (argv.verbose >= verbosity):
			sys.stderr.write(message + "\n")

	global pick_random_element
	def pick_random_element(array):
        	return array[random.randint(0, len(array) - 1)]

