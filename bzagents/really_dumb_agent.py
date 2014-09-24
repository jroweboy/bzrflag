import sys
import math
import time

from bzrc import BZRC, Command
from random import randint

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []
        self.mytanks = [tank for tank in self.bzrc.get_mytanks()]
        for idx, tank in enumerate(self.mytanks):
            self.mytanks[idx].move_timer = 0

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]

        self.commands = []

#     Move forward for 3-8 seconds

        for idx, tank in enumerate(mytanks):
            move_timer = self.mytanks[idx].move_timer
            move_timer -= time_diff
            self.mytanks[idx].move_timer = move_timer
            if move_timer > 0:
                self.commands.append(Command(idx, 10, 0, 0))
            else:
# Turn left about 60 degrees and then start going straight again
                self.commands.append(Command(idx, 0, 3, 0))
                move_timer = randint(3,8)
            if int(move_timer) % 2 == 0:
                self.commands.append(Command(idx, 10, 0, 1))

# In addition to this movement your really dumb agent should also shoot every 2 seconds (random between 1.5 and 2.5 seconds) or so.

# Once you have one tank doing this, create a team that has two such agents.
        # for tank in mytanks:
        #     self.attack_enemies(tank)

        results = self.bzrc.do_commands(self.commands)

    def act(self, tank):
        relative_angle = self.normalize_angle(target_angle - tank.angle)

    def attack_enemies(self, tank):
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