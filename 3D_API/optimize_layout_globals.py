#!/usr/bin/python

import sys

class argv(object):
	global argv
    	argv = None

	global abort
	def abort(message):
        	sys.stderr.write("Error: " + message + "\n")
        	sys.exit(1)

