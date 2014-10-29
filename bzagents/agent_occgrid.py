import sys
import math
import time

import urllib
import urllib2
import numpy 
from random import randint
from bzrc import BZRC, Command
from potential_field import GoalField, ObstacleField, TangentialField, PerpendicularField, RandomField
from grid_filter_gl import draw_grid, update_grid, init_window

class Point(object):
    def __init__(self,x,y):
        self.x = x
        self.y = y
    def __str__(self):
        return "(%r, %r)" %(self.x, self.y)
    def __repr__(self):
        return "(%r, %r)" %(self.x, self.y)

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""
    # TODO figure out how to make the tank(s) move
    # TODO figure out how to plot

    def __init__(self, bzrc):
        self.bzrc = bzrc
        init_window(800, 800)
        self.constants = self.bzrc.get_constants()
        self.obsOcc = float(self.constants['truepositive'])
        self.notObsNotOcc = float(self.constants['truenegative'])
        self.obsNotOcc = 1 - self.notObsNotOcc
        self.notObsOcc = 1 - self.obsOcc
        self.positive_threshold = .9
        self.negative_threshold = .1
        self.url = "http://localhost:8080/"

        self.bases = self.bzrc.get_bases()
        self.commands = []
        self.mytanks = [tank for tank in self.bzrc.get_mytanks()]
        self.init_common_potential_fields()

        for idx, tank in enumerate(self.mytanks):
            self.mytanks[idx].role = None
            self.mytanks[idx].field = None
            self.mytanks[idx].goal = None
        self.get_mycolor()
        for base in self.bases:
            if base.color == self.color:
                x = base.corner1_x + base.corner2_x + base.corner3_x + base.corner4_x
                y = base.corner1_y + base.corner2_y + base.corner3_y + base.corner4_y
                x = x / 4.0
                y = y / 4.0
                self.fields['base'] = GoalField(x, y, 15, 70, 0.15)

        self.grid = numpy.array([[0.25 for x in range(0,800)] for y in range(0,800)])
        # prior = 0.25
        # for i in range(0, 800):
        #     self.grid.append([])
        #     for j in range(0, 800):
        #         self.grid[i].append(prior)

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]

        self.commands = []
        self.update_potential_fields()

        for idx, tank in enumerate(mytanks):
            field = self.mytanks[idx].field
            role = self.mytanks[idx].role
            goal = self.mytanks[idx].goal
            self.mytanks[idx] = tank
            self.mytanks[idx].role = role
            self.mytanks[idx].field = field
            self.mytanks[idx].goal = goal

            # get the occgrid for only alive tanks
            if tank.status == self.constants['tankalive']:
                self.recalculate_grid(idx)

            if tank.status == self.constants['tankdead']:
                self.mytanks[idx].role = None
                self.mytanks[idx].field = None
                self.mytanks[idx].goal = None
            elif tank.status == self.constants['tankalive'] and self.mytanks[idx].role == None:
                self.assign_role(idx)
                self.mytanks[idx].role(self.mytanks[idx])
            else:
                self.mytanks[idx].role(self.mytanks[idx])
        results = self.bzrc.do_commands(self.commands)
        update_grid(self.grid)
        draw_grid()


    def recalculate_grid(self, idx):
        # I believe this should work
        # apparently the bottom left of the map is -400,-400
        # TODO does the grid start topleft visually or is it like the map starting from bottom left
        print idx
        pos, occgrid = self.bzrc.get_occgrid(idx)
        pos = list(pos)
        worldsize = int(self.constants['worldsize'])
        pos[0] += int(worldsize / 2)
        pos[1] += int(worldsize / 2)
        for i in range(0, len(occgrid)):
            row = pos[1] - len(occgrid) / 2 + i
            # row = int(worldsize - pos[1]) # ???
            # print "row %r" %row
            for j in range(0, len(occgrid)):
                # col = pos[0] + j
                col = pos[0] - len(occgrid) / 2 + j
                if self.grid[row][col] == 1:
                    continue
                if self.grid[row][col] == 0:
                    continue
                if self.grid[row][col] >= self.positive_threshold:
                    self.grid[row][col] = 1
                    continue
                if self.grid[row][col] <= self.negative_threshold:
                    self.grid[row][col] = 0
                    continue
                if occgrid[i][j] == 0:
                    self.grid[row][col] = (self.obsOcc * self.grid[row][col]) / (self.obsOcc * self.grid[row][col] + self.obsNotOcc * (1-self.grid[row][col]))
                else:
                    self.grid[row][col] = (self.notObsOcc * self.grid[row][col]) / (self.notObsOcc * self.grid[row][col] + self.notObsNotOcc * (1-self.grid[row][col]))

    def assign_role(self, idx):
        ''' Contains logic to determine what role a tank should get based on what is needed'''
        scout_points = self.fields['scout_points']
        r = randint(0, len(scout_points) - 1)
        goal_field = GoalField(scout_points[r].x, scout_points[r].y, 15, 70, 0.15)
        self.mytanks[idx].role = self.scout
        self.mytanks[idx].field = goal_field

    def init_common_potential_fields(self):
        ''' Called only once to initialize the random field '''
        self.fields = {}
        self.fields['scout_points'] = [Point(x,y) for x in range(50, 800, 50) for y in range(50, 800, 50)]
        # print self.fields['scout_points']
        self.fields['obstacle'] = [RandomField(-0.03, 0.03)]

    def update_potential_fields(self):
        '''Called once every tick to update the fields'''
        alpha = 2.5
        radius = 30
        # reset the obstacle locations and add obstacles at each point that we have resolved
        # terribly inefficient way to do this but hehehe 
        self.fields['obstacle'] = [RandomField(-0.03, 0.03)]
        for i in range(0,800):
            for j in range(0,800):
                if self.grid[i][j] == 1:
                    self.fields['obstacle'].append(ObstacleField(i, j, radius*0.05, radius*0.95, alpha*0.2))

    def calculate_field(self, tank):
        dx, dy = tank.field.calc(tank)
        for field in self.fields['obstacle']:
            r = field.calc(tank);
            dx += r[0]
            dy += r[1]
        return dx, dy

    def scout(self, tank):
        no_points = False
        # check to see if we've made it to our scout point
        if tank.field.x + 10 > tank.x and tank.field.x - 10 < tank.x and \
            tank.field.y + 10 > tank.y and tank.field.y - 10 < tank.y:
            # remove this scout_point from the fields and get another
            print "Removing a point from scout points cause we got there?"
            self.fields['scout_points'].remove(Point(tank.field.x, tank.field.y))
            tank.field = None
        # if we don't have a field, lets get one unless there are none to get
        if tank.field == None:
            scout_points = self.fields['scout_points']
            if len(scout_points) > 0:
                r = randint(0, len(scout_points) - 1)
                tank.field = GoalField(scout_points[r].x, scout_points[r].y, 15, 70, 0.15)
            else:
                no_points = True
        if no_points:
            # we have searched all the base points, now we need to see where we haven't fulled searched
            # check the grid to see if there are any non resolved points
            # once we are out of unresolved points we are all good and can call it quits
            print "no scout_points remain"
            return
        dx, dy = self.calculate_field(tank)
        self.move_to_position(tank, dx+tank.x, dy+tank.y)

    def seek(self, tank):
        """Get the flag and defend own flag bearer."""
        if tank.flag != "-":
            tank.field = self.fields['base']
        else:
            tank.field = self.fields['goal'][tank.goal]
        dx, dy = self.calculate_field(tank)
        self.move_to_position(tank, dx+tank.x, dy+tank.y)

    def move_to_position(self, tank, target_x, target_y):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        command = Command(tank.index, 1, 2 * relative_angle, True)
        self.commands.append(command)

    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

    def get_mycolor(self):
        self.color = self.mytanks[0].callsign[:-1]
        # print self.color


def main():
    # Process CLI arguments.
    try:
        execname, host, port = sys.argv
    except ValueError:
        execname = sys.argv[0]
        print >>sys.stderr, '%s: incorrect number of arguments' % execname
        print >>sys.stderr, 'usage: %s hostname port' % sys.argv[0]
        sys.exit(-1)

    # Connect.
    #bzrc = BZRC(host, int(port), debug=True)
    bzrc = BZRC(host, int(port))

    agent = Agent(bzrc)

    prev_time = time.time()

    # Run the agent
    try:
        while True:
            time_diff = time.time() - prev_time
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()