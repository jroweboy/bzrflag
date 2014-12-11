import sys
import math
import time
import pygame

import matplotlib
from pylab import *
import matplotlib.pyplot as plt
import matplotlib.animation as animation 
from matplotlib.lines import Line2D

from random import randint
from bzrc import BZRC, Command
from potential_field import GoalField, ObstacleField, TangentialField, PerpendicularField, RandomField
from kalman_shooter import KalmanTank, FIXED_TIME_STEP

class Point():
    def __init__(self,x,y):
        self.x = x
        self.y = y

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        # self.obstacles = self.bzrc.get_obstacles()
        self.bases = self.bzrc.get_bases()
        self.commands = []
        self.mytanks = [tank for tank in self.bzrc.get_mytanks()]
        self.othertanks = [tank for tank in self.bzrc.get_othertanks()]
        self.setup_common_potential_fields()

        self.kalmantanks = [KalmanTank(tank) for tank in self.bzrc.get_othertanks()]
        self.lines = []

        fig = plt.figure()
        axis = plt.axes(xlim=(-400, 400), ylim=(-400, 400))

        for idx, tank in enumerate(self.othertanks):
            self.lines.append(axis.plot([], [],lw=2)[0])
            # add another line for the Kalman line
            self.lines.append(axis.plot([], [],lw=1)[0])

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
            else:
                continue

        anim = animation.FuncAnimation(fig, self.tick, init_func=self.init_graph, interval=100, blit=True)
        plt.show()

    def init_graph(self):
        for i, line in enumerate(self.lines):
            line.set_data([self.othertanks[i/2].x], [self.othertanks[i/2].y])
        return self.lines

    def tick(self, frame_num):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]

        self.commands = []
        self.setup_potential_fields()

        for idx, tank in enumerate(othertanks):
            # update the main tank line and the kalman line
            xdata, ydata = self.lines[idx*2].get_data()
            xdata.append(tank.x)
            ydata.append(tank.y)
            self.lines[idx*2].set_data(xdata, ydata)
            self.kalmantanks[idx].tick(tank)
            # update the kalman lines as well
            xdata, ydata = self.lines[idx*2+1].get_data()
            kalmat = self.kalmantanks[idx].getKalmanMatrix()
            # print kalmat
            kal_x, kal_y = kalmat[0,0], kalmat[3,0]
            xdata.append(kal_x)
            ydata.append(kal_y)
            self.lines[idx*2+1].set_data(xdata, ydata)

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
        # for idx, line in enumerate(self.lines):
        #     if idx % 2 == 0:
        #         print "tank line %s: %r" %(idx, line.get_data())
        #     else:
        #         print "kalman line %s: %r" %(idx, line.get_data())

        return self.lines

    def assign_role(self, idx):
        self.mytanks[idx].role = self.stand_n_shoot

    def stand_n_shoot(self, tank):
        # find the closest tank to me amongst all the KalmanTanks
        pass



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

    # the plotting library is calling the tick function now lol so no need to do this

    # prev_time = time.time()
    # dt = FIXED_TIME_STEP

    # # Run the agent
    # accumulator = 0
    # try:
    #     while True:
    #         while accumulator < dt:
    #             time_diff = time.time() - prev_time
    #             prev_time = time.time()
    #             accumulator += time_diff;
    #         agent.tick(accumulator)
    #         accumulator = 0
    # except KeyboardInterrupt:
    #     print "Exiting due to keyboard interrupt."
    #     bzrc.close()


if __name__ == '__main__':
    main()