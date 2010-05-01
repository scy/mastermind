#!/usr/bin/env python2.6

import re
import json

class StateChangeError(StandardError):
	"""Invalid state change."""

class Parser(object):
	"""Parses an input stream."""

	def __init__(self, handle):
		"""
		Create a new parser.
		
		Pass an already open file handle.
		"""
		self._handle = handle #TODO: Type checking.
		self._masterbuf = ''
		self._state = 0
		self._continues = False
		self._commentchars = r'[#;]'
		self._masterchars = r'[+]'
		self._ignorelines = re.compile(r'^\s*(?:|' + self._commentchars +
		                               r'(?!' + self._masterchars + r').*)$')
		self._masterlines = re.compile(r'^\s*' + self._commentchars +
		                               self._masterchars + r'(.*)$')
		self._contlines = re.compile(r' ?\\$')

	def _setstate(self, state):
		"""
		Set a new parsing state.
		
		Valid states are:
		0 - reading remind commands
		1 - reading masterlines
		"""
		if state == self._state:
			return state
		if state == 0:
			if self._state == 1: # From masterlines to remind.
				self._masterdata = json.loads(self._masterbuf)
				print self._rembuf
				print self._masterdata
			else:
				raise StateChangeError()
		elif state == 1:
			if self._state == 0: # From remind to masterlines.
				pass
			else:
				raise StateChangeError()
		oldstate = self._state
		self._state = state
		return oldstate

	def run(self):
		"""Parse the file, apply filters and transformations."""
		h = self._handle
		eof = False
		h.seek(0)
		inline = 0
		# Note that we're not using "for line in h" intentionally: We want a
		# complete iteration _after_ the last line as well.
		while not eof:
			inline += 1
			line = h.readline()
			stripped = line.rstrip('\r\n')
			# If the line is completely empty, we've hit EOF.
			eof = line == ""
			if eof:
				# Finalize a possible masterline read.
				self._setstate(0)
			# Match for masterlines.
			mastermatch = self._masterlines.search(line)
			# Ignore comments and empty lines.
			if self._ignorelines.search(line) is not None:
				pass
			# If it's a masterline, append it to the buffer.
			elif mastermatch is not None:
				self._setstate(1)
				self._masterbuf += mastermatch.group(1)
			# Else it's a remind line, set/append it to its buffer.
			else:
				# First set the state to finish masterline parsing.
				self._setstate(0)
				# If the line ends in a backslash, it will continue on the next.
				willcontinue = stripped[-1] == '\\'
				if willcontinue:
					# Remove backslash and a possibly leading space. (Yes,
					# singular. That's how remind does it.)
					stripped = self._contlines.sub('', stripped)
				# If the last line continued, append, else set.
				if self._continues:
					self._rembuf += stripped
				else:
					self._rembuf = stripped
				self._continues = willcontinue
