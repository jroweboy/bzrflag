import sys
import math
import time

from random import randint
from bzrc import BZRC, Command
from potential_field import GoalField, ObstacleField, TangentialField

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.obstacles = self.bzrc.get_obstacles()
        self.bases = self.bzrc.get_bases()
        self.commands = []
        self.mytanks = [tank for tank in self.bzrc.get_mytanks()]
        # self.setup_common_potential_fields()
        for idx, tank in enumerate(self.mytanks):
            self.mytanks[idx].role = None
            self.mytanks[idx].field = None

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
            self.mytanks[idx] = tank
            self.mytanks[idx].role = role
            self.mytanks[idx].field = field
            if tank.status == self.constants['tankdead']:
               self.mytanks[idx].role = None
            elif tank.status == self.constants['tankalive'] and self.mytanks[idx].role == None:
               self.assign_role(idx)
               self.mytanks[idx].role(self.mytanks[idx])
            else:
               self.mytanks[idx].role(self.mytanks[idx])

        results = self.bzrc.do_commands(self.commands)

    def assign_role(self, idx):
        # randomly assign a role and field
        # self.mytanks[idx].role = self.attack
        r = randint(0, 2)
        if r == 0: # attack role
            self.mytanks[idx].role = self.attack
            self.mytanks[idx].field = None
        else:
        #elif r == 1 or r ==2: # combined defend and seek for noe 
            r2 = randint(0, len(self.fields['goal']) - 1)
            self.mytanks[idx].role = self.seek
            print r2, self.fields['goal']

            self.mytanks[idx].field = self.fields['goal'][r2]

    def setup_potential_fields(self):
        self.fields = {}
        self.fields['goal'] = []
        for flag in self.flags:
            self.fields['goal'].append(GoalField(flag.x, flag.y, 25, 50, 0.6))

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
        dx, dy = tank.field.calc(tank)
        self.move_to_position(tank, dx, dy)
        pass

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