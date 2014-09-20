import math

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
        distance = math.hypot(self.x - tank.pos.x, self.y - tank.pos.y)
        if distance < self.radius:
            return 0, 0
        else:
            theta = math.atan2(self.y - tank.pos.y, self.x - tank.pos.x)
            if distance <= self.spread + self.radius:
                dx = self.alpha * (distance - self.radius) * math.cos(theta)
                dy = self.alpha * (distance - self.radius) * math.sin(theta)
            else:
                dx = self.alpha * self.spread * math.cos(theta)
                dy = self.alpha * self.spread * math.sin(theta)
            return dx, dy

class ObstacleField:

    def __init__(self, x, y, radius, spread, alpha):
        self.x = x
        self.y = y
        self.radius = radius
        self.spread = spread
        self.alpha = alpha

    def calc(self, tank):
        distance = math.hypot(self.x - tank.pos.x, self.y - tank.pos.y)
        if distance > self.radius + self.spread:
            return 0, 0
        else:
            theta = math.atan2(self.y - tank.pos.y, self.x - tank.pos.x)
            if self.radius <= distance:
                dx = self.alpha * (distance - self.radius - self.spread) * math.cos(theta)
                dy = self.alpha * (distance - self.radius - self.spread) * math.sin(theta)
            else:
                dx = math.copysign(float("inf"),-1*math.cos(theta))
                dy = math.copysign(float("inf"),-1*math.sin(theta))
            return dx, dy

class RandomField:

    def __init__(self, min, max):
        self.min = min;
        self.max = max;

    def calc(self):
        dx = random.random() * (max - min) + min
        dy = random.random() * (max - min) + min
        return dx, dy


class PerpendicularField:
    """ This perpendicular field defines a rectangle by a line segment and radius.
        Agents on one side of the line segment within the radius are influenced
        perpendicular to the line segment.
    """
    def __init__(self, p1, p2, radius, alpha):
        self.p1 = p1
        self.p2 = p2
        self.radius = radius
        self.alpha = alpha

    def calc(self, tank):
        # Ax + By + C = 0
        a = p1.y - p2.y
        b = p2.x - p1.x
        c = (p2.y * p1.x) - (p1.y * p2.x)

        # check if the agent is close enough
        distance = abs((a * tank.pos.x + b * tank.pos.y + c) / math.sqrt(a * a + b * b))
        if distance > self.radius:
            return 0, 0

        # check if the agent is on the correct side
        # if we look at the lines that make an octogon with direction clockwise
        # then the correct side is outside the octogon
        if a * tank.pos.x + b * tank.pos.y + c <= 0:
            return 0, 0

        # check if the agent is within the line segment's region
        # (x1,y1) and (tank.x, tank.y) make a line perpendicular to our line
        # the two lines intersect at (x1,y1)
        x1 = (b * (b * tank.pos.x - a * tank.pos.y) - a * c) / (a * a + b * b)
        y1 = (a * (a * tank.pos.y - b * tank.pos.x) - b * c) / (a * a + b * b)
        if p2.x > p1.x:
            if x1 < p1.x or x2 > p2.x:
                return 0, 0
        else:
            if x1 < p2.x or x2 > p1.x:
                return 0, 0
        if p2.y > p1.y:
            if y1 < p1.y or y2 > p2.y:
                return 0, 0
        else:
            if y1 < p2.y or y1 > p1.y:
                return 0, 0

        # calculate dx,dy
        theta = math.atan2(a, b) # the angle perpendicular to the line segment
        dx = self.alpha * ((self.radius - distance) / self.radius) * math.cos(theta)
        dy = self.alpha * ((self.radius - distance) / self.radius) * math.sin(theta)

#class TangentialField:
