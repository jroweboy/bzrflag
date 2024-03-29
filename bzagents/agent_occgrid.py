import sys
import math
import time

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
        self.positive_threshold = .9999999
        self.negative_threshold = .0000001
        self.add_obstacle_counter = 0
        self.vision_range = 75

        self.commands = []
        self.mytanks = [tank for tank in self.bzrc.get_mytanks()]

        self.init_common_potential_fields()
        self.get_mycolor()

        for idx, tank in enumerate(self.mytanks):
            self.mytanks[idx].role = None
            self.mytanks[idx].field = None

        self.grid = numpy.array([[0.25 for x in range(0,800)] for y in range(0,800)])

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]

        self.commands = []

        for idx, tank in enumerate(mytanks):
            field = self.mytanks[idx].field
            role = self.mytanks[idx].role
            self.mytanks[idx] = tank
            self.mytanks[idx].role = role
            self.mytanks[idx].field = field

            # get the occgrid for only alive tanks
            if tank.status == self.constants['tankalive']:
                self.recalculate_grid(idx)
            if tank.status == self.constants['tankdead']:
                print 'tankdead'
                self.mytanks[idx].role = None
                self.mytanks[idx].field = None
            else:
                if self.mytanks[idx].role == None:
                    self.assign_role(idx)
                self.mytanks[idx].role(self.mytanks[idx])

        results = self.bzrc.do_commands(self.commands)
        update_grid(self.grid)
        draw_grid()


    def recalculate_grid(self, idx):
        # TODO does the grid start topleft visually or is it like the map starting from bottom left
        
        # TODO add try catch to all occgrid to work for dead tanks
        pos, occgrid = self.bzrc.get_occgrid(idx)
        pos = list(pos)
        worldsize = int(self.constants['worldsize'])
        pos[0] += int(worldsize / 2)
        pos[1] += int(worldsize / 2)
        for i in range(0, len(occgrid)):
            # row = pos[1] + i
            # row = pos[1] - len(occgrid) / 2 + i
            col = pos[0] + i
            # print "row %r" %row
            for j in range(0, len(occgrid[i])):
                # col = pos[0] + j
                # col = pos[0] - len(occgrid[i]) / 2 + j
                row = pos[1] + j
                # print "row: %d, col: %d" % (row, col)
                if row >= 800 or col >= 800:
                    continue
                elif self.grid[row][col] == 1:
                    continue
                elif self.grid[row][col] == 0:
                    continue
                elif self.grid[row][col] >= self.positive_threshold:
                    self.grid[row][col] = 1
                    self.add_obstacle(Point(col,row))
                    continue
                elif self.grid[row][col] <= self.negative_threshold:
                    self.grid[row][col] = 0
                    continue
                if occgrid[i][j] == 1:
                    self.grid[row][col] = (self.obsOcc * self.grid[row][col]) / (self.obsOcc * self.grid[row][col] + self.obsNotOcc * (1-self.grid[row][col]))
                else:
                    self.grid[row][col] = (self.notObsOcc * self.grid[row][col]) / (self.notObsOcc * self.grid[row][col] + self.notObsNotOcc * (1-self.grid[row][col]))

    def assign_role(self, idx):
        ''' Contains logic to determine what role a tank should get based on what is needed'''
        self.mytanks[idx].role = self.scout

    def init_common_potential_fields(self):
        ''' Called only once to initialize the random field '''
        self.fields = {}
        self.fields['scout_points'] = []
        self.fields['obstacle'] = []
        worldsize = int(self.constants['worldsize'])
        half_world = int(worldsize / 2)

        # snake method
        i = 0
        step_size = 50
        for x in range(-half_world, half_world+1, step_size):
            if i % 2 == 0:
                r = range(-half_world, half_world+1, step_size)
            else:
                r = range(half_world, -half_world-1, -step_size)
            for y in r:
                self.fields['scout_points'].append(Point(x,y))
            i += 1
        # spiral method
        # i = 1
        # inside = 0
        # step_size = 100
        # while inside < half_world:
        #     if i % 1 == 0:
        #         point = Point(-half_world + inside, -half_world + inside)
        #     if i % 2 == 0:
        #         point = Point(half_world - inside, -half_world + inside)
        #     if i % 3 == 0:
        #         point = Point(half_world - inside, half_world - inside)
        #     if i % 4 == 0:
        #         point = Point(-half_world + inside, half_world - inside)
        #         inside += step_size
        #         i = 0
        #     i += 1
        #     self.fields['scout_points'].append(point)
        print "%r" %self.fields['scout_points']
        self.fields['obstacle'].append(RandomField(-0.03, 0.03))

    def add_obstacle(self, point):
        self.add_obstacle_counter += 1
        if self.add_obstacle_counter % 50 != 0:
            return
        alpha = 0.5
        radius = 50
        spread = 25
        self.fields['obstacle'].append(TangentialField(point.x - 400, point.y- 400, radius, spread, alpha))
        # self.fields['obstacle'].append(ObstacleField(point.x - 400, point.y - 400, radius, spread, alpha / 2))

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
        if tank.field != None and \
            tank.field.x + self.vision_range > tank.x and tank.field.x - self.vision_range < tank.x and \
            tank.field.y + self.vision_range > tank.y and tank.field.y - self.vision_range < tank.y:
            print "Made it to the point"
            tank.field = None
        elif tank.field != None:
            if self.grid[tank.field.y - 400][tank.field.x - 400] == 0 or \
                self.grid[tank.field.y - 400][tank.field.x - 400] == 1:
                print "Point is already discovered"
                tank.field = None
        # if we don't have a field, lets get one unless there are none to get
        if tank.field == None:
            if len(self.fields['scout_points']) > 0:
                if tank.index == 0:
                    r = 0
                elif tank.index == 1:
                    r = -1
                else:
                    r = randint(0, len(self.fields['scout_points']) - 1)
                point = self.fields['scout_points'][r]
                print "Assigning point: %d,%d" % (point.x,point.y)
                tank.field = GoalField(point.x, point.y, 25, 75, 0.15)
                del self.fields['scout_points'][r]
            else:
                no_points = True
        if no_points:
            # we have searched all the base points, now we need to see where we haven't fulled searched
            # check the grid to see if there are any non resolved points
            # once we are out of unresolved points we are all good and can call it quits
            self.vision_range = 50
            print "explored all points"
            print "grid %r " % self.grid.shape[0]
            for i in range(0, self.grid.shape[0]):
                for j in range(0, self.grid.shape[1]):
                    if tank.index == 0:
                        point = Point(j - 400, i - 400)
                    else:
                        point = Point(400 - j - 1, 400 - i - 1)
                    if self.grid[point.y + 400][point.x + 400] != 0 and \
                        self.grid[point.y + 400][point.x + 400] != 1:
                        self.fields['scout_points'].append(point)
                        break

            if len(self.fields['scout_points']) == 0:
                print "no uncertainty remains"
            return
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