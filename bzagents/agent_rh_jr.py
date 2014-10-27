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

    def assign_role(self, idx):
        # randomly assign a role and field
        # self.mytanks[idx].role = self.attack
        # r = randint(0, 2)
        # if r == 0: # attack role
        #     self.mytanks[idx].role = self.attack
        #     self.mytanks[idx].field = None
        # else:
        # #elif r == 1 or r ==2: # combined defend and seek for now
        #     r2 = randint(0, len(self.fields['goal']) - 1)
        #     self.mytanks[idx].role = self.seek
        #     self.mytanks[idx].field = self.fields['goal'][r2]
        r = randint(0, len(self.fields['goal']) - 1)
        self.mytanks[idx].role = self.seek
        self.mytanks[idx].goal = r

    def setup_common_potential_fields(self):
        self.fields = {}
        self.fields['obstacle'] = []
        alpha = 2.5
        radius = 30
        self.fields['obstacle'].append(RandomField(-0.03, 0.03))
        for a in self.obstacles:
            first_point = a[0]
            last_point = a[0]
            self.fields['obstacle'].append(ObstacleField(first_point[0], first_point[1], radius*0.05, radius*0.95, alpha*0.2))
            for cur_point in a[1:]:
                # obstacles are rectangles so only dx or dy will be nonzero
                self.fields['obstacle'].append(
                    PerpendicularField(Point(last_point[0],last_point[1]), Point(cur_point[0],cur_point[1]), radius, alpha*0.25)
                )
                self.fields['obstacle'].append(
                    PerpendicularField(Point(last_point[0],last_point[1]), Point(cur_point[0],cur_point[1]), radius, alpha, True)
                )
                self.fields['obstacle'].append(ObstacleField(cur_point[0], cur_point[1], radius*0.05, radius*0.95, alpha*0.2))
                last_point = cur_point
            self.fields['obstacle'].append(PerpendicularField(Point(last_point[0],last_point[1]), Point(first_point[0],first_point[1]), radius, alpha*0.25))
            self.fields['obstacle'].append(PerpendicularField(Point(last_point[0],last_point[1]), Point(first_point[0],first_point[1]), radius, alpha, True))

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

    def attack(self, tank):
        """Find the closest enemy and chase it, shooting as you go."""
        best_enemy = None
        best_dist = 2 * float(self.constants['worldsize'])
        for enemy in self.enemies:
            if enemy.status != 'alive':
                continue
            dist = math.sqrt((enemy.x - tank.x)**2 + (enemy.y - tank.y)**2)
            if dist < best_dist:
                best_dist = dist
                best_enemy = enemy
        if best_enemy is None:
            command = Command(tank.index, 0, 0, False)
            self.commands.append(command)
        else:
            self.move_to_position(tank, best_enemy.x, best_enemy.y)

    def defend(self, tank):
        """Defend the base and chase enemy flag bearer."""
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