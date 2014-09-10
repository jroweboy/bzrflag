

# Should a tank even have a state? Will we need this information later or should
# every tank be inherintly preemptable?

# Since its single threaded I'm thinking we won't need states
class State:
    IDLE = 1   # No action in progress right now
    BUSY = 2   # Action in progress (whether a self action or a main controlled action)
    ACTING = 3 # No action given by main control and is acting on its own (could be idle as well)

# Potentially move all this to another file. If we need a common base, define it here
# I think that the goal should be let the main control define roles for a tank based on
# what it perceives and let the individual tanks be an actor based on the total information gained from
# all the tanks. The actions handed by main should preempt the actions done by the actor
class Role:
    ''' When the main control is not giving direct commands, follow this pattern
    The tanks that are given a role should be scheduled by the main '''
    def tick(self, time):
        self.act()

class Defender(Role):
    def act(self):
        ''' 
        Goals: hide behind walls and poke around the corner. 
               Chase people that grab the flag '''
        pass 

class Attacker(Role):
    def act(self):
        ''' 
        Goals: Destroy enemy tanks and make room for the runners
               Swap to protecting the runner if it grabs the flag '''
        pass 

class Runner(Role):
    def act(self):
        '''
        Goals: Focus on not dieing and getting the enemy flag
               Potentially just fire randomly?'''
        pass

class Idle(Role):
    def act(self):
        '''
        Goals: Do nothing unless the main control says to or changes the Role'''
        pass

class Tank():
    def __init__(self, tank):
        self.tank = tank
        self.state = READY
        self.role = Idle()

    def move(self, x, y):
        pass

    def turn(self, angle):
        pass

    def shoot(self, angle=-1):
        #self.state = State.BUSY
        if angle == -1:
            # shoot straight
            pass
        else:
            self.turn(angle)
            # shoot straight
        #self.state = State.IDLE

    def 
