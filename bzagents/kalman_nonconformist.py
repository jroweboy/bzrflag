import sys
import math
import time

from bzrc import BZRC, Command
from potential_field import GoalField
class Point():
    def __init__(self,x,y):
        self.x = x
        self.y = y
    def __repr__(self):
        return "Point (%s,%s)" % (self.x, self.y)

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []
        self.fields = {}
        self.mytanks = [tank for tank in self.bzrc.get_mytanks()]
        self.get_mycolor()

        bases = self.bzrc.get_bases()

        for base in bases:
            if base.color == self.color:
                x = base.corner1_x + base.corner2_x + base.corner3_x + base.corner4_x
                y = base.corner1_y + base.corner2_y + base.corner3_y + base.corner4_y
                x = x / 4.0
                y = y / 4.0
                self.base_pos = Point(x , y)
                break
            else:
                continue

        self.setup_potential_fields()
        for idx, tank in enumerate(self.mytanks):
            self.mytanks[idx].field = None

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()

        self.commands = []

        for idx, tank in enumerate(mytanks):
            field = self.mytanks[idx].field
            self.mytanks[idx] = tank
            self.mytanks[idx].field = field
            if tank.status == self.constants['tankdead']:
                self.mytanks[idx].field = None
            elif tank.status == self.constants['tankalive'] and self.mytanks[idx].field == None:
                self.assign_field(self.mytanks[idx])
                self.break_kalman(self.mytanks[idx])
            else:
                self.break_kalman(self.mytanks[idx])

        results = self.bzrc.do_commands(self.commands)

    def setup_potential_fields(self):
        self.fields['goal'] = []
        n = 25
        sx = 1
        sy = 1
        f = True

        # TODO add in differences so that it doesn't try to turn around after first point
        if self.base_pos.x > 0.0:
            sx = -1
        #elif self.base_pox.x < 0.0

        for t in range(0,12):
            if t % 3 == 0:
                x, y = 0, 0
            if t % 3 == 1:
                if f:
                    x, y = n * 3 * sx, n * sy
                else:
                    x, y = n * sx, n * 3 * sy
            if t % 3 == 2 :
                if f:
                    x, y = n * sx, n * 3 * sy
                else:
                    x, y = n * 3 * sx, n * sy
                f = not f
            if t == 3:
                sy *= -1
            if t == 6:
                sx *= -1
            if t == 9:
                sy *= -1
            self.fields['goal'].append(GoalField(x, y, 5, 30, 0.2))

    def assign_field(self, tank):
        tank.field = 0

    def calculate_field(self, tank):
        dx, dy = self.fields['goal'][tank.field].calc(tank)
        return dx, dy

    def break_kalman(self, tank):
        """Get the flag and defend own flag bearer."""
        field = self.fields['goal'][tank.field]
        d = math.sqrt((tank.x - field.x) * (tank.x - field.x) + (tank.y - field.y) * (tank.y - field.y))
        if d < 10:
            tank.field = (tank.field + 1) % len(self.fields['goal'])
            field = self.fields['goal'][tank.field]
            # print "Seeking field at (%s,%s)" % (field.x,field.y)
        dx, dy = self.calculate_field(tank)
        self.move_to_position(tank, dx+tank.x, dy+tank.y)

    def move_to_position(self, tank, target_x, target_y):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        # Don't want them to shoot so I set it to false
        command = Command(tank.index, 1, 2 * relative_angle, False)
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
            t = time.time()
            time_diff = t - prev_time
            prev_time = t
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()