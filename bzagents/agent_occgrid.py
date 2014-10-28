import sys
import math
import time

import urllib
import urllib2

from random import randint
from bzrc import BZRC, Command
from potential_field import GoalField, ObstacleField, TangentialField, PerpendicularField, RandomField



class Point():
    def __init__(self,x,y):
        self.x = x
        self.y = y

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""
    # TODO figure out how to make the tank(s) move
    # TODO figure out how to plot

    def __init__(self, bzrc):
        self.bzrc = bzrc

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
        self.setup_common_potential_fields()

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

        self.grid = []
        prior = 0.25
        for i in range(0, 800):
            self.grid.append([])
            for j in range(0, 800):
                self.grip[i].append(prior)

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]

        self.commands = []
        self.setup_potential_fields()

        for idx, tank in enumerate(mytanks):
            field = self.mytanks[idx].field
            role = self.mytanks[idx].role
            goal = self.mytanks[idx].goal
            self.mytanks[idx] = tank
            self.mytanks[idx].role = role
            self.mytanks[idx].field = field
            self.mytanks[idx].goal = goal
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

    def recalculate_grid(self, idx):
        # I believe this should work
        # apparently the bottom left of the map is -400,-400
        # TODO does the grid start topleft visually or is it like the map starting from bottom left
        pos,occgrid = bzrc.get_occgrid(idx)
        worldsize = int(self.contstants['worldsize']
        pos[0] += int(worldsize / 2)
        pos[1] += int(worldsize / 2)
        for i in range(0, size(occgrid)):
            row = int(worldsize - pos[1] # ???
            for j in range(0, len(occgrid[row])):
                col = pos[0] + j
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
                else
                    self.grid[row][col] = (self.notObsOcc * self.grid[row][col]) / (self.notObsOcc * self.grid[row][col] + self.notObsNotOcc * (1-self.grid[row][col]))

    def assign_role(self, idx):
        r = randint(0, len(self.fields['goal']) - 1)
        self.mytanks[idx].role = self.search
        self.mytanks[idx].goal = r

    def setup_common_potential_fields(self):
        self.fields = {}
        self.fields['obstacle'] = []
        alpha = 2.5
        radius = 30
        self.fields['obstacle'].append(RandomField(-0.03, 0.03))

    def setup_potential_fields(self):
        self.fields['goal'] = []
        for flag in self.flags:
            self.fields['goal'].append(GoalField(flag.x, flag.y, 15, 70, 0.15))

    def calculate_field(self, tank):
        dx, dy = tank.field.calc(tank)
        for field in self.fields['obstacle']:
            r = field.calc(tank);
            dx += r[0]
            dy += r[1]
        return dx, dy

    def search(self, tank):
        pass

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
        print self.color


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