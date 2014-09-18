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
            if self.radius <= distance
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

#class PerpendicularField:

#class TangentialField:
