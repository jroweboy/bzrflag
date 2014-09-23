import math
import random

# possibly return an angle and magniture instead of dx dy

class GoalField:
    """ Class represent the potential field of a goal.
        Alpha is the strength of the field.
        Agents within radius ditance of the field are not affected.
        Agents outside of spread + radius are attracted with maximum strength.
    """
    def __init__(self, x, y, radius, spread, alpha):
        self.x = x
        self.y = y
        self.radius = radius
        self.spread = spread
        self.alpha = alpha

    def calc(self, tank):
        distance = math.hypot(self.x - tank.x, self.y - tank.y)
        if distance < self.radius:
            return 0, 0
        else:
            theta = math.atan2(self.y - tank.y, self.x - tank.x)
            if distance < self.spread + self.radius:
                dx = self.alpha * (distance / (self.spread + self.radius)) * (math.cos(theta) / math.pi)
                dy = self.alpha * (distance / (self.spread + self.radius)) * (math.sin(theta) / math.pi)
            else:
                dx = self.alpha * math.cos(theta)
                dy = self.alpha * math.sin(theta)
            return dx, dy

class ObstacleField:

    def __init__(self, x, y, radius, spread, alpha):
        self.x = x
        self.y = y
        self.radius = radius
        self.spread = spread
        self.alpha = alpha

    def calc(self, tank):
        distance = math.hypot(self.x - tank.x, self.y - tank.y)
        if distance > self.radius + self.spread:
            return 0, 0
        else:
            # can this be right? seems like the same direction as the goal...
            # theta = math.atan2(self.y - tank.y, self.x - tank.x)
            theta = math.atan2(self.y - tank.y, self.x - tank.x) + math.pi
            if self.radius < distance:
                dx = self.alpha * ((self.spread + self.radius - distance) / (self.spread + self.radius)) * (math.cos(theta) / math.pi)
                dy = self.alpha * ((self.spread + self.radius - distance) / (self.spread + self.radius)) * (math.sin(theta) / math.pi)
            else:
                # should be infinity I guess...
                dx = self.alpha * (math.cos(theta) / math.pi)
                dy = self.alpha * (math.sin(theta) / math.pi)
            return dx, dy

class TangentialField:

    def __init__(self, x, y, radius, spread, alpha):
        self.x = x
        self.y = y
        self.radius = radius
        self.spread = spread
        self.alpha = alpha

    def calc(self, tank):
        distance = math.hypot(self.x - tank.x, self.y - tank.y)
        if distance > self.radius + self.spread:
            return 0, 0
        else:
            theta = math.atan2(self.y - tank.y, self.x - tank.x) + (math.pi / 2)
            if self.radius < distance:
                dx = self.alpha * ((self.spread + self.radius - distance) / (self.spread + self.radius)) * (math.cos(theta) / math.pi)
                dy = self.alpha * ((self.spread + self.radius - distance) / (self.spread + self.radius)) * (math.sin(theta) / math.pi)
            else:
                # should be infinity I guess...
                dx = self.alpha * (math.cos(theta) / math.pi)
                dy = self.alpha * (math.sin(theta) / math.pi)
            return dx, dy

class RandomField:

    def __init__(self, min, max):
        self.min = min;
        self.max = max;

    def calc(self, tank):
        dx = random.random() * (self.max - self.min) + self.min
        dy = random.random() * (self.max - self.min) + self.min
        return dx, dy

class PerpendicularField:
    """ This perpendicular field defines a rectangle by a line segment and radius.
        Agents on one side of the line segment within the radius are influenced
        perpendicular to the line segment.
    """
    def __init__(self, p1, p2, radius, alpha, tangential=False):
        self.p1 = p1
        self.p2 = p2
        self.radius = radius
        self.alpha = alpha
        self.tangential = tangential

    def calc(self, tank):
        # Ax + By + C = 0
        a = self.p1.y - self.p2.y
        b = self.p2.x - self.p1.x
        c = (self.p2.y * self.p1.x) - (self.p1.y * self.p2.x)

        # check if the agent is close enough
        distance = abs((a * tank.x + b * tank.y + c) / math.sqrt(a ** 2 + b ** 2))
        if distance > self.radius:
            return 0, 0

        # check if the agent is on the correct side
        # if we look at the lines that make an octogon with direction clockwise
        # then the correct side is outside the octogon
        if a * tank.x + b * tank.y + c <= 0:
            return 0, 0

        # check if the agent is within the line segment's region
        # (x1,y1) and (tank.x, tank.y) make a line perpendicular to our line
        # the two lines intersect at (x1,y1)
        x1 = (b * (b * tank.x - a * tank.y) - a * c) / (a ** 2 + b ** 2)
        y1 = (a * (a * tank.y - b * tank.x) - b * c) / (a ** 2 + b ** 2)
        if self.p2.x > self.p1.x:
            if x1 < self.p1.x or x1 > self.p2.x:
                return 0, 0
        else:
            if x1 < self.p2.x or x1 > self.p1.x:
                return 0, 0
        if self.p2.y > self.p1.y:
            if y1 < self.p1.y or y1 > self.p2.y:
                return 0, 0
        else:
            if y1 < self.p2.y or y1 > self.p1.y:
                return 0, 0

        # calculate dx,dy
        if self.tangential:
            theta = math.atan2(-1 * a, b)
        else:
            theta = math.atan2(b, a) # the angle perpendicular to the line segment
        dx = self.alpha * ((self.radius - distance) / self.radius) * (math.cos(theta) / math.pi)
        dy = self.alpha * ((self.radius - distance) / self.radius) * (math.sin(theta) / math.pi)
        return dx, dy
