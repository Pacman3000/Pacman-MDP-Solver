# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api

# Taken from mapAgents.py lab solutions on keats
# Draws up a grid for the map
class Grid:

	def __init__(self, width, height):
		subgrid = []
		self.width = width
		self.height = height
		for m in range(self.height):
			row = []
			for n in range(self.width):
				row.append(0)
			subgrid.append(row)

		self.grid = subgrid

	# Sets value of (m,n)
	def setVal(self, m, n, value):
		self.grid[n][m] = value

	# Returns value of (m,n)
	def getVal(self, m, n):
		return self.grid[n][m]

	def getHeight(self):
		return self.height

	def getWidth(self):
		return self.width

	# Prints the grid
	def display(self):
		for m in range(self.height):
			for n in range(self.width):
				print self.grid[self.height - m - 1][n],
			print
		print

# Finds the best move for pacman at each of pacman's states by calculating their utilities
class MDPAgent(Agent):

	# Constructor: this gets run when we first invoke pacman.py
	def __init__(self):
		print("Starting up MDPAgent!")

		self.VisitedCoords = []  # stores a list of visited spaces on the map
		self.MapOfFood = []  # stores a list of food coordinates
		self.MapOfCaps = []  # stores a list of capsules' coordinates
		self.MapOfWalls = []  # stores a list of wall coordinates

	# Gets run after MDPAgent object is created and once there is game state to access
	def registerInitialState(self, state):
		print("Running registerInitialState for MDPAgent!")
		print("I'm at:")
		print(api.whereAmI(state))

		#Taken from mapAgents lab solutions on keats, makes the map
		self.makeMap(state)
		self.addWalls(state)
		self.map.display()

	# This is what gets run between multiple games
	def final(self, state):
		print("Looks like the game just ended!")

		# When the game ends the arrays should be emptied so the next game can start fresh
		self.VisitedCoords = []
		self.MapOfFood = []
		self.MapOfCaps = []
		self.MapOfWalls = []


	# Make a map by creating a grid of the right size
	# Taken from mapAgents lab solutions on keats
	def makeMap(self, state):
		corners = api.corners(state)
		height = self.heightOfLayout(corners)
		width = self.widthOfLayout(corners)
		self.map = Grid(width, height)

	# Function will give the height of the layout
	def heightOfLayout(self, corners):
		array= []
		for m in range(len(corners)):
			array.append(corners[m][1])
		return max(array) + 1   # the +1 is because the indexes of the array start at 0

	# Function will give the width of the layout
	def widthOfLayout(self, corners):
		array = []
		for m in range(len(corners)):
			array.append(corners[m][0])
		return max(array) + 1  # the +1 is because the indexes of the array start at 0

	# Adds and shows walls on map grid as the character 'W'
	def addWalls(self, state):
		walls = api.walls(state)
		for m in range(len(walls)):
			self.map.setVal(walls[m][0], walls[m][1], "W")

	def makeMapWithValues(self, state):
		# This will return all coordinates on the map along with the values they have
		# food and capsules get the value of 10 and empty coordinates get the value 0

		pacLoc = api.whereAmI(state)  # Location of pacman
		food = api.food(state)  # Location of food
		caps = api.capsules(state)  # Location of capsules
		corners = api.corners(state)  # Location of corners
		walls = api.walls(state)  # Location of walls
		ghosts = api.ghosts(state) # Location of ghosts

		# if pacman's current location hasn't be visited before, add to list of previously visited locations
		if pacLoc not in self.VisitedCoords:
			self.VisitedCoords.append(pacLoc)

		# adds food to the food map, if not already there
		for m in food:
			if m not in self.MapOfFood:
				self.MapOfFood.append(m)

		# adds capsules to the capsules map, if not already there
		for m in caps:
			if m not in self.MapOfCaps:
				self.MapOfCaps.append(m)

		# adds walls to the wall map, if not already there
		for m in walls:
			if m not in self.MapOfWalls:
				self.MapOfWalls.append(m)

		# Dictionaries will store all the coordinates of food/capsules/walls and assign the corresponding values to them
		# Map will then be initialised with these values
		mapWithValues = {}
		mapWithValues.update(dict.fromkeys(self.MapOfFood, 100))
		mapWithValues.update(dict.fromkeys(self.MapOfCaps, 100))
		mapWithValues.update(dict.fromkeys(self.MapOfWalls, 'W'))

		# This will give pacman's initial coord the value 0
		for i in range(self.widthOfLayout(corners) - 1):
			for j in range(self.heightOfLayout(corners) - 1):
				if (i, j) not in mapWithValues.keys():
					mapWithValues[(i, j)] = 0

		# if a coord on the map contains a ghost, its value is changed to -100
		for m in mapWithValues.keys():
			for n in range(len(ghosts)):
				if ((int(ghosts[n][0])), (int(ghosts[n][1]))) == m:
					mapWithValues[m] = -100 # Negative value for coordinates containing ghosts

		# if pacman has visited a coordinate and it no longer has food/capsules, its value is set to 0
		for i in self.MapOfFood:
			if i in self.VisitedCoords:
				mapWithValues[i] = 0
		for i in self.MapOfCaps:
			if i in self.VisitedCoords:
				mapWithValues[i] = 0

		return mapWithValues

	# following function will calculate, and assign as values, the meu of the coords on the map
	# used as transition model value in value iteration
	def transition(self, m, n, mapWithValues):
		# Dictionary will store the utilities
		self.utilityDictionary = {"NorthUtility": 0.0, "EastUtility": 0.0, "SouthUtility": 0.0, "WestUtility": 0.0}

		self.mapWithValues = mapWithValues #Contains values of every coord

		self.m = m
		self.n = n
		CurrentPosition = (self.m, self.n)
		North = (self.m, self.n + 1)
		East = (self.m + 1, self.n)
		South = (self.m, self.n - 1)
		West = (self.m - 1, self.n)

		# If north of pacman is a wall, the value of pacman's current coord is multiplied by the expected utility
		# If it is not a wall, the value of the coord is multiplied by the expected utility
		# Same is done for east and west of pacman as there is a 10% chance (each) pacman will move in those directions
		if self.mapWithValues[North] == "W":
			NorthUtility = self.mapWithValues[CurrentPosition] * 0.8
		else:
			NorthUtility = self.mapWithValues[North] * 0.8

		if self.mapWithValues[East] == "W":
			NorthUtility += self.mapWithValues[CurrentPosition] * 0.1
		else:
			NorthUtility += self.mapWithValues[East] * 0.1

		if self.mapWithValues[West] == "W":
			NorthUtility += self.mapWithValues[CurrentPosition] * 0.1
		else:
			NorthUtility += self.mapWithValues[West] * 0.1

		# If east of pacman is a wall, the value of pacman's current coord is multiplied by the expected utility
		# If it is not a wall, the value of the coord is multiplied by the expected utility
		# Same is done for north and south of pacman as there is a 10% chance (each) pacman will move in those directions
		if self.mapWithValues[East] == "W":
			EastUtility = self.mapWithValues[CurrentPosition] * 0.8
		else:
			EastUtility = self.mapWithValues[East] * 0.8

		if self.mapWithValues[North] == "W":
			EastUtility += self.mapWithValues[CurrentPosition] * 0.1
		else:
			EastUtility += self.mapWithValues[North] * 0.1

		if self.mapWithValues[South] == "W":
			EastUtility += self.mapWithValues[CurrentPosition] * 0.1
		else:
			EastUtility += self.mapWithValues[South] * 0.1

		# If south of pacman is a wall, the value of pacman's current coord is multiplied by the expected utility
		# If it is not a wall, the value of the coord is multiplied by the expected utility
		# Same is done for east and west of pacman as there is a 10% chance (each) pacman will move in those directions
		if self.mapWithValues[South] == "W":
			SouthUtility = self.mapWithValues[CurrentPosition] * 0.8
		else:
			SouthUtility = self.mapWithValues[South] * 0.8

		if self.mapWithValues[East] == "W":
			SouthUtility += self.mapWithValues[CurrentPosition] * 0.1
		else:
			SouthUtility += self.mapWithValues[East] * 0.1

		if self.mapWithValues[West] == "W":
			SouthUtility += self.mapWithValues[CurrentPosition] * 0.1
		else:
			SouthUtility += self.mapWithValues[West] * 0.1

		# If west of pacman is a wall, the value of pacman's current coord is multiplied by the expected utility
		# If it is not a wall, the value of the coord is multiplied by the expected utility
		# Same is done for north and south of pacman as there is a 10% chance (each) pacman will move in those directions
		if self.mapWithValues[West] == "W":
			WestUtility = self.mapWithValues[CurrentPosition] * 0.8
		else:
			WestUtility = self.mapWithValues[West] * 0.8

		if self.mapWithValues[North] == "W":
			WestUtility += self.mapWithValues[CurrentPosition] * 0.1
		else:
			WestUtility += self.mapWithValues[North] * 0.1

		if self.mapWithValues[South] == "W":
			WestUtility += self.mapWithValues[CurrentPosition] * 0.1
		else:
			WestUtility += self.mapWithValues[South] * 0.1

		# Assign the new utilities for each direction
		self.utilityDictionary["NorthUtility"] = NorthUtility
		self.utilityDictionary["EastUtility"] = EastUtility
		self.utilityDictionary["SouthUtility"] = SouthUtility
		self.utilityDictionary["WestUtility"] = WestUtility

		# find the largest utility value in the dictionary and set it as
		self.mapWithValues[CurrentPosition] = max(self.utilityDictionary.values())
		# Return the map with the new values
		return self.mapWithValues[CurrentPosition]

	# Function will do value iteration for the small map using the Bellman equation
	def valueIterationForSmallGrid(self, state, reward, discountFunction, mapWithValues):

		food = api.food(state)  					# Location of food
		caps = api.capsules(state)  				# Location of capsules
		corners = api.corners(state)  				# Location of corners
		walls = api.walls(state)  					# Location of walls
		ghosts = api.ghosts(state)  				# Location of ghosts
		Width = self.widthOfLayout(corners) - 1  	# Width of the layout
		Height = self.heightOfLayout(corners) - 1  	# Height of the layout

		# Bellman equation implementation
		iterations = 100
		while 0 < iterations :
			for m in range(Width):
				for n in range(Height):
					if (m, n) not in food and (m, n) not in caps and (m, n) not in walls and (m, n) not in ghosts:
						mapOrig = mapWithValues.copy()  # Stores all previous values
						mapWithValues[(m, n)] = reward + discountFunction * self.transition(m, n, mapOrig) # Bellman equation
			iterations -= 1  # decrement the iteration variable so the while loop repeats 200 times

	# Function will do value iteration for the medium classic map using the Bellman equation
	def valueIterationForMediumClassic(self, state, reward, discountFunction, mapWithValues):

		food = api.food(state)  					# Location of food
		caps = api.capsules(state)  				# Location of capsules
		corners = api.corners(state)  				# Location of corners
		walls = api.walls(state)  					# Location of walls
		ghosts = api.ghosts(state)  				# Location of ghosts
		Width = self.widthOfLayout(corners) - 1  	# Width of the layout
		Height = self.heightOfLayout(corners) - 1  	# Height of the layout

		# Following code performs value iteration on coords 5 or less away from ghosts in any direction
		# Makes sure that pacman doesn't avoid food just because it's near a ghost
		foodUtilities = []
		for m in range(0, 5): #iterated 5 times
			for n in range(len(ghosts)):
				if (int(ghosts[n][0]), int(ghosts[n][1] + 1)) not in foodUtilities:  # 5 or less North of the ghost
					foodUtilities.append((int(ghosts[n][0]), int(ghosts[n][1] + m)))
				if (int(ghosts[n][0] + m), int(ghosts[n][1])) not in foodUtilities:  # 5 or less East of the ghost
					foodUtilities.append((int(ghosts[n][0] + m), int(ghosts[n][1])))
				if (int(ghosts[n][0]), int(ghosts[n][1] - 1)) not in foodUtilities:  # 5 or less South of the ghost
					foodUtilities.append((int(ghosts[n][0]), int(ghosts[n][1] - m)))
				if (int(ghosts[n][0] - m), int(ghosts[n][1])) not in foodUtilities:  # 5 or less West of the ghost
					foodUtilities.append((int(ghosts[n][0] - m), int(ghosts[n][1])))

		# When food is not eaten and is more than 5 spaces away from a ghost it does not need to be calculated
		# The following array will store these coords
		XCalc = []
		for m in food:
			if m not in foodUtilities:
				XCalc.append(m)

		# Bellman equation implementation
		iterations = 100  # only 100 iterations so time isn't wasted by computing more iterations than necessary
		while 0 < iterations:
			for m in range(Width):
				for n in range(Height):
					if (m, n) not in ghosts and (m, n) not in caps and (m, n) not in walls and (m, n) not in XCalc:
						mapOrig = mapWithValues.copy()  # store all the previous values
						mapWithValues[(m, n)] = reward + (discountFunction * self.transition(m, n, mapOrig)) # Bellman equation
			iterations -= 1  # decrement the iteration variable so the while loop repeats 100 times


	def policy(self, state, iterationMap):
	
		pac = api.whereAmI(state)  # Location of pacman
		self.mapWithValues = iterationMap # Map that has been through a value iteration function

		# Dictionary will store the utility values
		self.utilityDictionary = {"NorthUtility": 0.0, "EastUtility": 0.0, "SouthUtility": 0.0, "WestUtility": 0.0}

		# Directions with respect to pacman's location
		CurrentLocation = (pac[0], pac[1])
		North = (pac[0], pac[1] + 1)
		East = (pac[0] + 1, pac[1])
		South = (pac[0], pac[1] - 1)
		West = (pac[0] - 1, pac[1])

		# If north of pacman is a wall, the value of pacman's current coord is multiplied by the expected utility
		# If it is not a wall, the value of the coord is multiplied by the expected utility
		# Same is done for east and west of pacman as there is a 10% chance (each) pacman will move in those directions
		if self.mapWithValues[North] == "W":
			NorthUtility = self.mapWithValues[CurrentLocation] * 0.8
		else:
			NorthUtility = self.mapWithValues[North] * 0.8

		if self.mapWithValues[East] == "W":
			NorthUtility += self.mapWithValues[CurrentLocation] * 0.1
		else:
			NorthUtility += self.mapWithValues[East] * 0.1

		if self.mapWithValues[West] == "W":
			NorthUtility += self.mapWithValues[CurrentLocation] * 0.1
		else:
			NorthUtility += self.mapWithValues[West] * 0.1

		# If east of pacman is a wall, the value of pacman's current coord is multiplied by the expected utility
		# If it is not a wall, the value of the coord is multiplied by the expected utility
		# Same is done for north and south of pacman as there is a 10% chance (each) pacman will move in those directions
		if self.mapWithValues[East] == "W":
			EastUtility = self.mapWithValues[CurrentLocation] * 0.8
		else:
			EastUtility = self.mapWithValues[East] * 0.8

		if self.mapWithValues[North] == "W":
			EastUtility += self.mapWithValues[CurrentLocation] * 0.1
		else:
			EastUtility += self.mapWithValues[North] * 0.1

		if self.mapWithValues[South] == "W":
			EastUtility += self.mapWithValues[CurrentLocation] * 0.1
		else:
			EastUtility += self.mapWithValues[South] * 0.1

		# If south of pacman is a wall, the value of pacman's current coord is multiplied by the expected utility
		# If it is not a wall, the value of the coord is multiplied by the expected utility
		# Same is done for east and west of pacman as there is a 10% chance (each) pacman will move in those directions
		if self.mapWithValues[South] == "W":
			SouthUtility = self.mapWithValues[CurrentLocation] * 0.8
		else:
			SouthUtility = self.mapWithValues[South] * 0.8

		if self.mapWithValues[East] == "W":
			SouthUtility += self.mapWithValues[CurrentLocation] * 0.1
		else:
			SouthUtility += self.mapWithValues[East] * 0.1

		if self.mapWithValues[West] == "W":
			SouthUtility += self.mapWithValues[CurrentLocation] * 0.1
		else:
			SouthUtility += self.mapWithValues[West] * 0.1

		# If west of pacman is a wall, the value of pacman's current coord is multiplied by the expected utility
		# If it is not a wall, the value of the coord is multiplied by the expected utility
		# Same is done for north and south of pacman as there is a 10% chance (each) pacman will move in those directions
		if self.mapWithValues[West] == "W":
			WestUtility = self.mapWithValues[CurrentLocation] * 0.8
		else:
			WestUtility = self.mapWithValues[West] * 0.8

		if self.mapWithValues[North] == "W":
			WestUtility += self.mapWithValues[CurrentLocation] * 0.1
		else:
			WestUtility += self.mapWithValues[North] * 0.1

		if self.mapWithValues[South] == "W":
			WestUtility += self.mapWithValues[CurrentLocation] * 0.1
		else:
			WestUtility += self.mapWithValues[South] * 0.1

		# Dictionary tuples are given the new values calculated
		self.utilityDictionary["NorthUtility"] = NorthUtility
		self.utilityDictionary["EastUtility"] = EastUtility
		self.utilityDictionary["SouthUtility"] = SouthUtility
		self.utilityDictionary["WestUtility"] = WestUtility

		# Maximum expected utility
		meu = max(self.utilityDictionary.values())

		# Return the move that has the highest maximum expected utility
		return self.utilityDictionary.keys()[self.utilityDictionary.values().index(meu)]

	def getAction(self, state):

		self.map.display()
		legal = api.legalActions(state)
		corners = api.corners(state)
		Width = self.widthOfLayout(corners) - 1
		Height = self.heightOfLayout(corners) - 1
		mapOfValues = self.makeMapWithValues(state) # Map will be updated whenever an action is performed

		# makes sure the correct value iteration is performed depending on the map
		if Width < 10 and Height < 10:
			self.valueIterationForSmallGrid(state, (-0.5), 1, mapOfValues)
		else:
			self.valueIterationForMediumClassic(state, (-0.7), 1, mapOfValues)

		# Updates the map with iterated values
		for i in range(self.map.getWidth()):
			for j in range(self.map.getHeight()):
				if self.map.getVal(i, j) != "W":
					self.map.setVal(i, j, mapOfValues[(i, j)])

		# Return the best direction
		if self.policy(state, mapOfValues) == "NorthUtility":
			return api.makeMove(Directions.NORTH, legal)

		if self.policy(state, mapOfValues) == "EastUtility":
			return api.makeMove(Directions.EAST, legal)

		if self.policy(state, mapOfValues) == "SouthUtility":
			return api.makeMove(Directions.SOUTH, legal)

		if self.policy(state, mapOfValues) == "WestUtility":
			return api.makeMove(Directions.WEST, legal)
