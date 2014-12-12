import sys
import math
import time

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
        self.shotspeed = int(self.constants['shotspeed'])
       # {'shotspeed': '100', 'tankalive': 'alive', 'truepositive': '1', 'worldsize': '800', 'explodetime': '5', 'truenegative': '1', 'shotrange': '350', 'flagradius': '2.5', 'tankdead': 'dead', 'tankspeed': '25', 'shotradius': '0.5', 'tankangvel': '0.785398163397', 'linearaccel': '0.5', 'team': 'purple', 'tankradius': '4.32', 'angularaccel': '0.5', 'tankwidth': '2.8', 'tanklength': '6'}
        # self.obstacles = self.bzrc.get_obstacles()
        self.bases = self.bzrc.get_bases()
        self.commands = []
        self.mytanks = {tank.callsign: tank for tank in self.bzrc.get_mytanks()}
        self.othertanks = {tank.callsign: tank for tank in self.bzrc.get_othertanks()}
        self.setup_common_potential_fields()

        self.kalmantanks = {tank.callsign: KalmanTank(tank) for tank in self.bzrc.get_othertanks()}
        self.lines = {}

        fig = plt.figure()
        axis = plt.axes(xlim=(-400, 400), ylim=(-400, 400))

        for callsign, tank in self.othertanks.iteritems():
            self.lines[callsign] = axis.plot([], [],lw=2)[0]
            # add another line for the Kalman line
            self.lines[callsign+"kalman"] = axis.plot([], [],lw=1)[0]
            self.lines[callsign+"estimate"] = axis.plot([], [],lw=1)[0]

        for callsign, tank in self.mytanks.iteritems():
            self.mytanks[callsign].role = None
            self.mytanks[callsign].field = None
            self.mytanks[callsign].goal = None

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

        anim = animation.FuncAnimation(fig, self.tick, init_func=self.init_graph, interval=1000*FIXED_TIME_STEP, blit=True)
        plt.show()

    def init_graph(self):
        for callsign, line in self.lines.iteritems():
            if callsign.endswith("kalman"):
                callsign = callsign[:-6]
            if callsign.endswith("estimate"):
                callsign = callsign[:-8]
            line.set_data([self.othertanks[callsign].x], [self.othertanks[callsign].y])
        return self.lines.values()

    def tick(self, frame_num):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.othertanks = {tank.callsign: tank for tank in othertanks}
        mytanks = {tank.callsign: tank for tank in mytanks}
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]
        # for idx, enemy in enumerate(self.enemies):
        #     enemy.id = idx

        self.commands = []
        self.setup_potential_fields()

        for callsign, tank in self.othertanks.iteritems():
            # update the main tank line and the kalman line
            # tank.id = idx
            xdata, ydata = self.lines[callsign].get_data()
            xdata.append(tank.x)
            ydata.append(tank.y)
            self.lines[callsign].set_data(xdata, ydata)
            self.kalmantanks[callsign].tick(tank)
            # update the kalman lines as well
            xdata, ydata = self.lines[callsign+"kalman"].get_data()
            kalmat = self.kalmantanks[callsign].getKalmanMatrix()
            # print kalmat
            kal_x, kal_y = kalmat[0,0], kalmat[3,0]
            xdata.append(kal_x)
            ydata.append(kal_y)
            self.lines[callsign+"kalman"].set_data(xdata, ydata)

        for callsign, tank in mytanks.iteritems():
            field = self.mytanks[callsign].field
            role = self.mytanks[callsign].role
            goal = self.mytanks[callsign].goal
            self.mytanks[callsign] = tank
            self.mytanks[callsign].role = role
            self.mytanks[callsign].field = field
            self.mytanks[callsign].goal = goal
            if tank.status == self.constants['tankdead']:
               self.mytanks[callsign].role = None
               self.mytanks[callsign].field = None
               self.mytanks[callsign].goal = None
            elif tank.status == self.constants['tankalive'] and self.mytanks[callsign].role == None:
               self.assign_role(callsign)
               self.mytanks[callsign].role(self.mytanks[callsign])
            else:
               self.mytanks[callsign].role(self.mytanks[callsign])

        results = self.bzrc.do_commands(self.commands)
        # for idx, line in enumerate(self.lines):
        #     if idx % 2 == 0:
        #         print "tank line %s: %r" %(idx, line.get_data())
        #     else:
        #         print "kalman line %s: %r" %(idx, line.get_data())
        # extrapolation = self.extrapolate(20)
        self.extrapolate(20)
        return self.lines.values() # + extrapolation

    def extrapolate(self, n):
        for callsign, _ in self.othertanks.iteritems():
            xdata, ydata = self.kalmantanks[callsign].kalman.extrapolate(n)
            # print "xdata: %r \n ydata: %r" %(xdata, ydata)
            self.lines[callsign+"estimate"].set_data(xdata,ydata)
                

    def assign_role(self, idx):
        self.mytanks[idx].role = self.stand_n_shoot
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
        # r = randint(0, len(self.fields['goal']) - 1)
        # self.mytanks[idx].role = self.attack
        # self.mytanks[idx].goal = r

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
            # best_enemy = self.enemies[0]  # fix this later to best enemy
            x, y, shoot = self.acquire(tank, best_enemy)
            # self.move_to_position(tank, best_enemy.x, best_enemy.y, True)
            self.move_to_position(tank, x, y, 0, shoot)

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

    def move_to_position(self, tank, target_x, target_y, velocity, shoot):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)

        command = Command(tank.index, velocity, 2 * relative_angle, shoot)  # Don't shoot automatically
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
        self.color = self.mytanks.keys()[0][:-1]

    def kalman(self, enemy):
        km = self.kalmantanks[enemy.id].getKalmanMatrix()
        # print km
        # print len(km)
        # print len(km.item((0, 0)))
        # print type(km)
        # print type(km.item((0, 0)))
        # print km.item((0, 0))
        # print "--------"
        # print type(enemy)
        # return km.item((0, 0)), km.item((1, 1)), km.item((2, 2)), km.item((3, 3)), km.item((4, 4)), km.item((5, 5))

        # return (0, 0, 0, 0, 0, 0)
        return (enemy.x, .0003, .0001, enemy.y, .0004, .0002)

    def acquire(self, tank, enemy):
        # print self.solve(0, .003, 0.001, 0, .004, 0.002, 395, 50, 395, 100)
        # print self.solve2(0, .003, 0.001, 0, .004, 0.002, 395, 50, 395, 100)

        xpbullet = tank.x
        ypbullet = tank.y

        # vtank = 25  # get this real value
        ang_tank = tank.angle

        # vbullet = self.shotspeed + vtank
        # vbullet = 1
        xvbullet = tank.vx + self.shotspeed * (math.sin(1.57079633 - ang_tank) / math.sin(1.57079633))
        yvbullet = tank.vy + self.shotspeed * (math.sin(ang_tank) / math.sin(1.57079633))

        # print xvbullet
        # print yvbullet
        # print tank.x
        # print tank.y

        xpenemy, xvenemy, xaenemy, ypenemy, yvenemy, yaenemy = self.kalman(enemy)


        shoot = False
        # print enemy.color, (self.othertanks[enemy.id].color)
        # print xpenemy, xvenemy, xaenemy, ypenemy, yvenemy, yaenemy, xpbullet, xvbullet, ypbullet, yvbullet
        x1, y1, te1, tb1, a1 = [1000]*5
        try:
            x1, y1, te1, tb1 = self.solve(xpenemy, xvenemy, xaenemy, ypenemy, yvenemy, yaenemy, xpbullet, xvbullet, ypbullet, yvbullet)
            # print x1, y1, te1, tb1
            a1 = abs(te1 - tb1)
        except ValueError:
            # print "value error"
            # s1 = (0, 0, -1, -1)
            shoot = True

        x2, y2, te2, tb2, a2 = [1000]*5
        try:
            x2, y2, te2, tb2 = self.solve2(xpenemy, xvenemy, xaenemy, ypenemy, yvenemy, yaenemy, xpbullet, xvbullet, ypbullet, yvbullet)
            # print x2, y2, te2, tb2
            a2 = abs(te2 - tb2)
        except ValueError:
            # print "value error2"
            # s2 = (0, 0, -1, -1)(enemy.x, enemy.y)
            shoot = True

        # print enemy.x, enemy.y
        if a1 < a2:
            shoot = a1 < .2 or (abs(enemy.x - x1) < 4 > abs(enemy.y - y1))
            # print a1 < .2
            # print shoot
            # if x1 > 0 < y1 and x1 < 3 > y1:
            if te1 > 0 and te1 < 3 > tb1:
                return x1, y1, shoot
            else:
                return enemy.x, enemy.y, shoot
        else:
            shoot = a2 < .2 or (abs(enemy.x - x2) < 4 > abs(enemy.y - y2))
            # print a2 < .2
            # print shoot
            # if x2 > 0 < y2 and x2 < 3 > y2:
            if te2 > 0 and te2 < 3 > tb2:
                return x2, y2, shoot
            else:
                return enemy.x, enemy.y, shoot

    def solve(self, xpe, xve, xae, ype, yve, yae, xpb, xvb, ypb, yvb):
    # .5*a*t^2+v*t+p=x
    # m*g+n=x
    # .5*q*t^2+w*t+e=y
    # r*g+j=y
        p = xpe
        v = xve
        a = xae
        e = ype
        w = yve
        q = yae
        n = xpb
        m = xvb
        j = ypb
        r = yvb

        x = (w*((-a*m*r-m**2*q)*v-a*m*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q))+m*q*v*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q)+a*m**2*w**2+m*q*r*v**2+a**2*n*r**2+((-a*m*p-a*m*n)*q+(a**2*e-a**2*j)*m)*r+m**2*p*q**2+(a*j-a*e)*m**2*q)/(a**2*r**2-2*a*m*q*r+m**2*q**2)
        g = (w*((-a*r-m*q)*v-a*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q))+q*v*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q)+a*m*w**2+q*r*v**2+((a*n-a*p)*q-a**2*j+a**2*e)*r+(m*p-m*n)*q**2+(a*j-a*e)*m*q)/(a**2*r**2-2*a*m*q*r+m**2*q**2)
        t = -(math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2+(2*a*n-2*a*p)*r**2+((2*m*p-2*m*n)*q+(2*a*e-2*a*j)*m)*r+(2*j-2*e)*m**2*q)-m*w+r*v)/(a*r-m*q)
        y = (w*((-a*r**2-m*q*r)*v-a*r*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q))+q*r*v*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q)+a*m*r*w**2+q*r**2*v**2+((a*n-a*p)*q+a**2*e)*r**2+((m*p-m*n)*q**2+(-a*j-a*e)*m*q)*r+j*m**2*q**2)/(a**2*r**2-2*a*m*q*r+m**2*q**2)

        # x intercept, y intercept, tank arrival time, bullet arrival time
        return x, y, t, g

    def solve2(self, xpe, xve, xae, ype, yve, yae, xpb, xvb, ypb, yvb):
        p = xpe
        v = xve
        a = xae
        e = ype
        w = yve
        q = yae
        n = xpb
        m = xvb
        j = ypb
        r = yvb

        x = (w*(a*m*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q)+(-a*m*r-m**2*q)*v)-m*q*v*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q)+a*m**2*w**2+m*q*r*v**2+a**2*n*r**2+((-a*m*p-a*m*n)*q+(a**2*e-a**2*j)*m)*r+m**2*p*q**2+(a*j-a*e)*m**2*q)/(a**2*r**2-2*a*m*q*r+m**2*q**2)
        g = (w*(a*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q)+(-a*r-m*q)*v)-q*v*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q)+a*m*w**2+q*r*v**2+((a*n-a*p)*q-a**2*j+a**2*e)*r+(m*p-m*n)*q**2+(a*j-a*e)*m*q)/(a**2*r**2-2*a*m*q*r+m**2*q**2)
        t = (math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2+(2*a*n-2*a*p)*r**2+((2*m*p-2*m*n)*q+(2*a*e-2*a*j)*m)*r+(2*j-2*e)*m**2*q)+m*w-r*v)/(a*r-m*q)
        y = (w*(a*r*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q)+(-a*r**2-m*q*r)*v)-q*r*v*math.sqrt(m**2*w**2-2*m*r*v*w+r**2*v**2-2*a*p*r**2+2*a*n*r**2+2*m*p*q*r-2*m*n*q*r-2*a*j*m*r+2*a*e*m*r+2*j*m**2*q-2*e*m**2*q)+a*m*r*w**2+q*r**2*v**2+((a*n-a*p)*q+a**2*e)*r**2+((m*p-m*n)*q**2+(-a*j-a*e)*m*q)*r+j*m**2*q**2)/(a**2*r**2-2*a*m*q*r+m**2*q**2)

        # x intercept, y intercept, tank arrival time, bullet arrival time
        return x, y, t, g

    def get_solution(self, pe, ve, ae, bp, bv):
        tankt = (math.sqrt(ve ** 2 - 2 * ae * pe) - ve) / ae

        bullett = -(bp/bv)

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