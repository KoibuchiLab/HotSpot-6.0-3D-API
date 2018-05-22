#!/usr/bin/python

import sys
import random

argv = None

def abort(message):
      	sys.stderr.write("Error: " + message + "\n")
       	sys.exit(1)

def info(verbosity, message):
	if (argv.verbose >= verbosity):
		sys.stderr.write(message + "\n")

def pick_random_element(array):
       	return array[random.randint(0, len(array) - 1)]

