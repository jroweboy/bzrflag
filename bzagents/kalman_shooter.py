import sys
import math
import time

from random import randint
from bzrc import BZRC, Command
from potential_field import GoalField, ObstacleField, TangentialField, PerpendicularField, RandomField
class Point():
    def __init__(self,x,y):
        self.x = x
        self.y = y

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.obstacles = self.bzrc.get_obstacles()
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
            else:
                continue
                

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