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
import random
import game
import util


# Taken from mapAgents.py lab solutions on keats to graw up a grid for the map
class Grid:

    def __init__(self, height, width):
        subgrid = []
        self.height = height
        self.width = width
        for m in range(self.height):
            row = []
            for n in range(self.width):
                row.append(0)
            subgrid.append(row)
        self.grid = subgrid

    def setVal(self, m, n, val):  # sets the value of (m,n) to a specific value
        self.grid[n][m] = val

    def retVal(self, m, n):  # returns value of (m,n)
        return self.grid[n][m]

    def display(self):  # prints the grid
        for m in range(self.width):
            for n in range(self.height):
                print(self.grid[self.height - m - 1][n])
            print()
        print()

    def getWidth(self):
        return self.width

    def getHeight(self):
        return self.height


class MDPAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):

        print("Starting up MDPAgent!")

        self.VisitedCoords = []  # stores a list of visited spaces on the map
        self.MapOfCapsules = []  # stores a list of capsules' coordinates
        self.MapOfFood = []  # stores a list of food coordinates
        self.MapOfWalls = []  # stores a list of wall coordinates

    # Gets run after an MDPAgent object is created and once there is game state to access.
    def registerInitialState(self, state):
        print("Running registerInitialState for MDPAgent!")
        print("I'm at:")
        print(api.whereAmI(state))

        # Taken from mapAgents.py lab solutions:
        self.makeMap(state)
        self.addWalls(state)
        self.map.display()

    # This is what gets run in between multiple games
    def final(self):
        print("Looks like the game just ended!")

        self.VisitedCoords = []
        self.MapOfCapsules = []
        self.MapOfFood = []
        self.MapOfWalls = []

    # Make a map by creating a grid of the right size
    # Taken from mapAgents.py lab solutions
    def makeMap(self, state):
        corners = api.corners(state)
        height = self.heightOfLayout(corners)
        width = self.widthOfLayout(corners)
        self.map = Grid(width, height)

    # Following code will help to make up a valued map for pacman
    def widthOfLayout(self, corners):  # Function will give the width of the layout
        array = []
        for i in range(len(corners)):
            array.append(corners[i][1])
        return max(array) + 1  # the +1 is because the indexes of the array start at 0

    def heightOfLayout(self, corners):  # Function will give the height of the layout
        array = []
        for i in range(len(corners)):
            array.append(corners[i][0])
        return max(array) + 1  # the +1 is because the indexes of the array start at 0

    def addWalls(self, state):  # adds and shows walls on the map table as the character #
        walls = api.walls(state)
        for i in range(len(walls)):
            self.map.setVal(walls[i][0], walls[i][1], "#")

    def makeMapWithValues(self, state):
        # This will give all coordinates on the table and the values they represent
        # I give food and capsules the value of 10 and empty coordinates 0
        pacLoc = api.whereAmI(state)  # Location of pacman
        food = api.food(state)  # Location of food
        caps = api.capsules(state)  # Location of capsules
        corners = api.corners(state)  # Location of corners
        walls = api.walls(state)  # Location of walls

        # if pacman's current location hasn't be visited before, add to list of previously visited locations
        if pacLoc not in self.VisitedCoords:
            self.VisitedCoords.append(pacLoc)

        for i in food:  # adds food that pacman can 'see' to the food map if it is not already there
            if i not in self.MapOfFood:
                self.MapOfFood.append(i)

        for i in caps:  # adds capsules that pacman can 'see' to the capsules map if it is not already there
            if i not in self.MapOfCapsules:
                self.MapOfCapsules.append(i)

        for i in walls:  # adds walls that pacman can 'see' to the wall map if not already there
            if i not in self.MapOfWalls:
                self.MapOfWalls.append(i)

        # Dictionaries will store all the coordinates of food/capsules/walls and assign the corresponding values to them
        # Map will then be initialised with these coordinates and values
        mapWithValues = {}
        mapWithValues.update(dict.fromkeys(self.MapOfFood, 10))
        mapWithValues.update(dict.fromkeys(self.MapOfCapsules, 10))
        mapWithValues.update(dict.fromkeys(self.MapOfWalls, "#"))

        # this will give pacman's initial coord the value 0
        for m in range(self.widthOfLayout(corners) - 1):
            for n in range(self.heightOfLayout(corners) - 1):
                if (m, n) not in mapWithValues.keys():
                    mapWithValues[(m, n)] = 0

        # if pacman has visited a coordinate set its value to 0 as well
        for i in self.MapOfFood:
            if i in self.VisitedCoords:
                mapWithValues[i] = 0
        for i in self.MapOfCapsules:
            if i in self.VisitedCoords:
                mapWithValues[i] = 0

        # if there's a ghost at a coord that's contained in the map, value of it is changed to -10, otherwise no change
        ghosts = api.ghosts(state)
        for m in mapWithValues.keys():
            for n in range(0, len(ghosts)):
                ghostTimes = api.ghostStatesWithTimes(state)[n][1]
                if (int(ghosts[n][0]), int(ghosts[n][1])) == m and ghostTimes < 5:
                    mapWithValues[m] = -10  # negative value for coordinate containing ghost

        return mapWithValues

    # following function will calculate, and assign as values, the meu of the coords on the map
    # used as transition model value in value iteration
    def MEU(self, i, j, mapWithValues):
        # dictionary will store the utilities
        self.utilityDictionary = {"NorthUtility": 0, "EastUtility": 0, "SouthUtility": 0, "WestUtility": 0}

        self.mapWithValues = mapWithValues  # contains values of every coord

        self.i = i
        self.j = j
        CurrentPosition = (self.i, self.j)
        North = (self.i, self.j + 1)
        East = (self.i + 1, self.j)
        South = (self.i, self.j - 1)
        West = (self.i - 1, self.j)

        # if the direction pacman is taking is not a wall, the value of the coord is multiplied by the expected utility
        if self.mapWithValues[North] == "#":
            NorthUtility = self.mapWithValues[CurrentPosition] * 0.8
        else:
            NorthUtility = self.mapWithValues[North] * 0.8

        if self.mapWithValues[East] == "#":
            NorthUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            NorthUtility += self.mapWithValues[East] * 0.1

        if self.mapWithValues[West] == "#":  # when attempting to go north, there's a 0.1 chance pacman will go west
            NorthUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            NorthUtility += self.mapWithValues[West] * 0.1
        self.utilityDictionary["NorthUtility"] = NorthUtility

        if self.mapWithValues[South] == "#":
            SouthUtility = self.mapWithValues[CurrentPosition] * 0.8
        else:
            SouthUtility = self.mapWithValues[South] * 0.8

        if self.mapWithValues[West] == "#":  # when attempting to go south, there's a 0.1 chance pacman will go west
            SouthUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            SouthUtility += self.mapWithValues[West] * 0.1

        if self.mapWithValues[East] == "#":  # when attempting to go south, there's a 0.1 chance pacman will go east
            SouthUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            SouthUtility += self.mapWithValues[East] * 0.1
        self.utilityDictionary["SouthUtility"] = SouthUtility

        if self.mapWithValues[East] != "#":
            EastUtility = self.mapWithValues[East] * 0.8
        else:
            EastUtility = self.mapWithValues[CurrentPosition] * 0.8

        if self.mapWithValues[South] == "#":  # when attempting to go east, there's a 0.1 chance pacman will go south
            EastUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            EastUtility += self.mapWithValues[South] * 0.1

        if self.mapWithValues[North] == "#":  # when attempting to go east, there's a 0.1 chance pacman will go north
            EastUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            EastUtility += self.mapWithValues[North] * 0.1
        self.utilityDictionary["EastUtility"] = EastUtility

        if self.mapWithValues[West] == "#":
            WestUtility = self.mapWithValues[CurrentPosition] * 0.8
        else:
            WestUtility = self.mapWithValues[West] * 0.8

        if self.mapWithValues[North] == "#":  # when attempting to go west, there's a 0.1 chance pacman will go north
            WestUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            WestUtility += self.mapWithValues[North] * 0.1

        if self.mapWithValues[South] == "#":  # when attempting to go west, there's a 0.1 chance pacman will go south
            WestUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            WestUtility += self.mapWithValues[South] * 0.1
        self.utilityDictionary["WestUtility"] = WestUtility

        # gives the current position the maximum utility that has been stored
        self.mapWithValues[CurrentPosition] = max(self.utilityDictionary.values())
        # updates the map with the new values
        return self.mapWithValues[CurrentPosition]

    # Function will do value iteration for the small map using the Bellman equation
    def valIterationForSmallGrid(self, state, reward, discountFunction, mapWithValues):

        food = api.food(state)  # Location of food
        caps = api.capsules(state)  # Location of capsules
        corners = api.corners(state)  # Location of corners
        walls = api.walls(state)  # Location of walls
        ghosts = api.ghosts(state)  # Location of ghosts
        Width = self.widthOfLayout(corners) - 1  # Width of the layout
        Height = self.heightOfLayout(corners) - 1  # Height of the layout

        # Bellman equation implementation
        iteration = 100
        while 0 < iteration:
            for m in range(0, Width):
                for n in range(0, Height):
                    if (m, n) not in ghosts and (m, n) not in food and (m, n) not in caps and (m, n) not in walls:
                        mapOrig = mapWithValues.copy()  # stores all the previous values
                        mapWithValues[(m, n)] = reward + discountFunction * self.MEU(m, n, mapOrig)  # Bellman equation
            iteration -= 1  # decrement the iteration variable so the while loop repeats 100 times

    # Function will do value iteration for the medium classic map using the Bellman equation
    def valIterationForMediumClassic(self, state, reward, discountFunction, mapWithValues):

        caps = api.capsules(state)  # Location of capsules
        corners = api.corners(state)  # Location of corners
        walls = api.walls(state)  # Location of walls
        ghosts = api.ghosts(state)  # Location of ghosts
        Width = self.widthOfLayout(corners) - 1  # Width of the layout
        Height = self.heightOfLayout(corners) - 1  # Height of the layout

        foodUtilities = []  # array to store utilities that'll be calculated for food 5 or less spaces away from ghosts
        for m in range(0, 5):
            for n in range(0, len(ghosts)):  # iterated 5 times
                if (ghosts[n][0], ghosts[n][1] + 1) not in foodUtilities:  # 5 or less North of the ghost
                    foodUtilities.append((ghosts[n][0], ghosts[n][1] + 1))
                if (ghosts[n][0], ghosts[n][1] - 1) not in foodUtilities:  # 5 or less South of the ghost
                    foodUtilities.append((ghosts[n][0], ghosts[n][1] - 1))
                if (ghosts[n][0] + 1, ghosts[n][1]) not in foodUtilities:  # 5 or less East of the ghost
                    foodUtilities.append((ghosts[n][0] + 1, ghosts[n][1]))
                if (ghosts[n][0] - 1, ghosts[n][1]) not in foodUtilities:  # 5 or less West of the ghost
                    foodUtilities.append((ghosts[n][0] - 1, ghosts[n][1]))

        # Bellman equation implementation
        iteration = 100
        while 0 < iteration:
            for m in range(0, Width):
                for n in range(0, Height):
                    if (m, n) not in ghosts and (m, n) not in caps and (m, n) not in walls and (m, n) in foodUtilities:
                        mapOrig = mapWithValues.copy()  # stores all the previous values
                        mapWithValues[(m, n)] = reward + discountFunction * self.MEU(m, n, mapOrig)  # Bellman equation
            iteration -= 1  # decrement the iteration variable so the while loop repeats 100 times

    def policy(self, state, iMap):

        pac = api.whereAmI(state)  # Location of pacman
        self.mapWithValues = iMap  # Map that has been through a value iteration function

        self.utilityDictionary = {"NorthUtility": 0, "EastUtility": 0, "SouthUtility": 0,
                                  "WestUtility": 0, }  # dictionary will store the utility values

        # Directions with respect to pacman's location
        North = (pac[0], pac[1] + 1)
        East = (pac[0] + 1, pac[1])
        South = (pac[0], pac[1] - 1)
        West = (pac[0] - 1, pac[1])
        CurrentPosition = (pac[0], pac[1])

        if self.mapWithValues[North] == '#':
            NorthUtility = self.mapWithValues[CurrentPosition] * 0.8
        else:
            NorthUtility = self.mapWithValues[North] * 0.8

        if self.mapWithValues[East] == "#":
            NorthUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            NorthUtility += self.mapWithValues[East] * 0.1

        if self.mapWithValues[West] == "#":
            NorthUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            NorthUtility += self.mapWithValues[West] * 0.1
        self.utilityDictionary["NorthUtility"] = NorthUtility

        if self.mapWithValues[East] == "#":
            EastUtility = self.mapWithValues[CurrentPosition] * 0.8
        else:
            EastUtility = self.mapWithValues[East] * 0.8

        if self.mapWithValues[North] == "#":
            EastUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            EastUtility += self.mapWithValues[North] * 0.1

        if self.mapWithValues[South] == "#":
            EastUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            EastUtility += self.mapWithValues[South] * 0.1
        self.utilityDictionary["EastUtility"] = EastUtility

        if self.mapWithValues[South] == "#":
            SouthUtility = self.mapWithValues[CurrentPosition] * 0.8
        else:
            SouthUtility = self.mapWithValues[South] * 0.8

        if self.mapWithValues[West] == "#":
            SouthUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            SouthUtility += self.mapWithValues[West] * 0.1

        if self.mapWithValues[East] == "#":
            SouthUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            SouthUtility += self.mapWithValues[East] * 0.1
        self.utilityDictionary["SouthUtility"] = SouthUtility

        if self.mapWithValues[West] == "#":
            WestUtility = self.mapWithValues[CurrentPosition] * 0.8
        else:
            WestUtility = self.mapWithValues[West] * 0.8

        if self.mapWithValues[North] == "#":
            WestUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            WestUtility += self.mapWithValues[North] * 0.1

        if self.mapWithValues[South] == "#":
            WestUtility += self.mapWithValues[CurrentPosition] * 0.1
        else:
            WestUtility += self.mapWithValues[South] * 0.1
        self.utilityDictionary["WestUtility"] = WestUtility

        MEU = max(self.utilityDictionary.values())  # max expected utility
        # Gives the move that has the highest max expected utility
        return self.utilityDictionary.keys()[self.utilityDictionary.values().index(MEU)]

    def getAction(self, state):

        self.map.display()
        legal = api.legalActions(state)
        corners = api.corners(state)
        Width = self.widthOfLayout(corners)
        Height = self.heightOfLayout(corners)
        mapOfValues = self.makeMapWithValues(state)  # map will be updated whenever an action is performed

        # If
        if Width > 9 and Height > 9:
            self.valIterationForMediumClassic(state, 0, 0.6, mapOfValues)
        else:
            self.valIterationForSmallGrid(state, 0.2, 0.7, mapOfValues)

        # updates the map with iterated values
        for m in range(0, self.map.getWidth()):
            for n in range(0, self.map.getHeight()):
                if self.map.retVal(m, n) != "#":
                    self.map.setVal(m, n, mapOfValues[(m, n)])

        # Return the best direction
        if self.policy(state, mapOfValues) == "NorthUtility":
            return api.makeMove(Directions.NORTH, legal)

        if self.policy(state, mapOfValues) == "EastUtility":
            return api.makeMove(Directions.EAST, legal)

        if self.policy(state, mapOfValues) == "SouthUtility":
            return api.makeMove(Directions.SOUTH, legal)

        if self.policy(state, mapOfValues) == "WestUtility":
            return api.makeMove(Directions.WEST, legal)
