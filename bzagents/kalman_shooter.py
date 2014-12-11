# original code referenced by Greg Czerniak
# rewritten by James Rowe

import math
import random
import numpy

FIXED_TIME_STEP = 0.1

# The idea is to make a Kalman tracker for every tank that we need to track
class Kalman:
    def __init__(self, state_m, control_m, obs_m, 
                init_state_e, init_covariance_e, process_err_e, measure_err_e):
# State transition matrix.
# Basically, multiply state by this and add control factors, and you get a prediction of the state for the next time step.
        self.A = state_m

# Control matrix. 
# This is used to define linear equations for any control factors
        self.B = control_m

# Observation matrix. 
# Multiply a state vector by H to translate it to a measurement vector.
# ie: when multplying by the output to reduce it to a 2x1 matrix for just the x, y coords
        self.H = obs_m

# Initial State matrix
# Initially, your clay pigeons will be at some unknown position on the playing field, and the velocity and acceleration will both be zero.
# so we have a 6 matrix representing the x, xv, xa, y, yv, ya properties
        self.current_state_estimate = init_state_e

# Initial covariance estimate.
# a 6x6 matrix that describes our thoughts about how accurate we are to the target
# Numbers are stored down the diagonol and are the same as 
        self.current_prob_estimate = init_covariance_e
# Estimated error in process.
        self.Q = process_err_e
# Estimated error in measurements.
        self.R = measure_err_e

    def tick(self, control_vector, measurement_vector):
#        '''
#Runs the following functions and updates expected locations
#Kt + 1 = (FEtFT + Ex)HT(H(FEtFT + Ex)HT + Ez)^-1

#ut + 1 = Fut + Kt + 1(zt + 1 - HFut)

#Et + 1 = (I - Kt + 1H)(FEtFT + Ex)
#        '''
        # Prediction step
        predicted_state_estimate = self.A * self.current_state_estimate + self.B * control_vector
        predicted_prob_estimate = (self.A * self.current_prob_estimate) * numpy.transpose(self.A) + self.Q
        # Observation step
        innovation = measurement_vector - self.H*predicted_state_estimate
        innovation_covariance = self.H*predicted_prob_estimate*numpy.transpose(self.H) + self.R
        # Update step
        kalman_gain = predicted_prob_estimate * numpy.transpose(self.H) * numpy.linalg.inv(innovation_covariance)
        self.current_state_estimate = predicted_state_estimate + kalman_gain * innovation
        # We need the size of the matrix so we can make an identity matrix.
        size = self.current_prob_estimate.shape[0]
        # eye(n) = nxn identity matrix.
        self.current_prob_estimate = (numpy.eye(size)-kalman_gain*self.H)*predicted_prob_estimate

class KalmanTank:

    def __init__(self, tank):
        self.tank = tank
        dt = FIXED_TIME_STEP
        c = 0
        # x y variance (he said make it a parameter but I don't think its changing really
        x_variance,y_variance = (25, 25)
        state_matrix = numpy.matrix(
            [[1, dt, dt**2/2, 0, 0 ,    0    ],
             [0, 1 ,   dt   , 0, 0 ,    0    ],
             [0,-c ,   1    , 0, 0 ,    0    ],
             [0, 0 ,   0    , 1, dt, dt**2/2 ],
             [0, 0 ,   0    , 0, 1 ,    dt   ], 
             [0, 0 ,   0    , 0,-c ,    1    ]])
        x = tank.x
        y = tank.y
        control_matrix = numpy.matrix(
            [[x], [0], [0], [y], [0], [0]])

        observation_matrix = numpy.matrix(
            [[1, 0, 0, 0, 0, 0],
             [0, 0, 0, 1, 0, 0]])

        init_state_estimate = numpy.matrix(
            [[100, 0, 0, 0, 0, 0],
             [0, 0.1, 0, 0, 0, 0],
             [0, 0, 0.1, 0, 0, 0],
             [0, 0, 0, 100, 0, 0],
             [0, 0, 0, 0, 0.1, 0],
             [0, 0, 0, 0, 0, 0.1]])

        init_covariance_estimate = numpy.matrix(
            [[0.1, 0, 0, 0, 0, 0],
             [0, 0.1, 0, 0, 0, 0],
             [0, 0, 100, 0, 0, 0],
             [0, 0, 0, 0.1, 0, 0],
             [0, 0, 0, 0, 0.1, 0],
             [0, 0, 0, 0, 0, 100]])

        # How accurate is our F, the newtonian method?
        process_err_estimate = numpy.matrix(
            [[0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0]])
        # we set this to 25 since thats about as far off as the x y value could be?
        measure_err_estimate = numpy.matrix(
            [[x_variance, 0],
             [0, y_variance]])
            # [[25, 0, 0, 0, 0, 0],
            #  [0, 25, 0, 0, 0, 0],
            #  [0, 0, 25, 0, 0, 0],
            #  [0, 0, 0, 25, 0, 0],
            #  [0, 0, 0, 0, 25, 0],
            #  [0, 0, 0, 0, 0, 25]])

        self.kalman = Kalman(state_matrix, control_matrix, observation_matrix, 
                init_state_estimate, init_covariance_estimate, process_err_estimate, measure_err_estimate)

    def tick(self, tank):
        # calculate the two matrixes needed for the Kalman filter
        # and then set the self.tank to tank
        measurement_vector = numpy.matrix(
            [[tank.x], [tank.y]])
        # TODO verify this is correct
        control_vector = numpy.matrix([[tank.x, 0, 0, tank.y, 0, 0]])

        self.kalman.tick(control_vector, measurement_vector)
        self.tank = tank

    def getKalmanMatrix(self):
        return self.kalman.current_state_estimate


# Simulates the classic physics problem of a cannon shooting a ball in a
# parabolic arc.  In addition to giving "true" values back, you can also ask
# for noisy values back to test Kalman filters.
# class Cannon:
#   #--------------------------------VARIABLES----------------------------------
#   angle = 45 # The angle from the ground to point the cannon.
#   muzzle_velocity = 100 # Muzzle velocity of the cannon.
#   gravity = [0,-9.81] # A vector containing gravitational acceleration.
#   # The initial velocity of the cannonball
#   velocity = [muzzle_velocity*math.cos(angle*math.pi/180), muzzle_velocity*math.sin(angle*math.pi/180)]
#   loc = [0,0] # The initial location of the cannonball.
#   acceleration = [0,0] # The initial acceleration of the cannonball.
#   #---------------------------------METHODS-----------------------------------
#   def __init__(self,_timeslice,_noiselevel):
#     self.timeslice = _timeslice
#     self.noiselevel = _noiselevel
#   def add(self,x,y):
#     return x + y
#   def mult(self,x,y):
#     return x * y
#   def GetX(self):
#     return self.loc[0]
#   def GetY(self):
#     return self.loc[1]
#   def GetXWithNoise(self):
#     return random.gauss(self.GetX(),self.noiselevel)
#   def GetYWithNoise(self):
#     return random.gauss(self.GetY(),self.noiselevel)
#   def GetXVelocity(self):
#     return self.velocity[0]
#   def GetYVelocity(self):
#     return self.velocity[1]
#   # Increment through the next timeslice of the simulation.
#   def Step(self):
#     # We're gonna use this vector to timeslice everything.
#     timeslicevec = [self.timeslice,self.timeslice]
#     # Break gravitational force into a smaller time slice.
#     sliced_gravity = map(self.mult,self.gravity,timeslicevec)
#     # The only force on the cannonball is gravity.
#     sliced_acceleration = sliced_gravity
#     # Apply the acceleration to velocity.
#     self.velocity = map(self.add, self.velocity, sliced_acceleration)
#     sliced_velocity = map(self.mult, self.velocity, timeslicevec )
#     # Apply the velocity to location.
#     self.loc = map(self.add, self.loc, sliced_velocity)
#     # Cannonballs shouldn't go into the ground.
#     if self.loc[1] < 0:
#       self.loc[1] = 0

#=============================REAL PROGRAM START================================
# Let's go over the physics behind the cannon shot, just to make sure it's
# correct:
# sin(45)*100 = 70.710 and cos(45)*100 = 70.710
# vf = vo + at
# 0 = 70.710 + (-9.81)t
# t = 70.710/9.81 = 7.208 seconds for half
# 14.416 seconds for full journey
# distance = 70.710 m/s * 14.416 sec = 1019.36796 m

# timeslice = 0.1 # How many seconds should elapse per iteration?
# iterations = 144 # How many iterations should the simulation run for?
# # (notice that the full journey takes 14.416 seconds, so 145 iterations will
# # cover the whole thing when timeslice = 0.10)
# noiselevel = 30  # How much noise should we add to the noisy measurements?
# muzzle_velocity = 100 # How fast should the cannonball come out?
# angle = 45 # Angle from the ground.

# # These are arrays to store the data points we want to plot at the end.
# x = []
# y = []
# nx = []
# ny = []
# kx = []
# ky = []

# # Let's make a cannon simulation.
# c = Cannon(timeslice,noiselevel)

# speedX = muzzle_velocity*math.cos(angle*math.pi/180)
# speedY = muzzle_velocity*math.sin(angle*math.pi/180)

# # This is the state transition vector, which represents part of the kinematics.
# # 1, ts, 0,  0  =>  x(n+1) = x(n) + vx(n)
# # 0,  1, 0,  0  => vx(n+1) =        vx(n)
# # 0,  0, 1, ts  =>  y(n+1) =              y(n) + vy(n)
# # 0,  0, 0,  1  => vy(n+1) =                     vy(n)
# # Remember, acceleration gets added to these at the control vector.
# state_transition = numpy.matrix([[1,timeslice,0,0],[0,1,0,0],[0,0,1,timeslice],[0,0,0,1]])

# control_matrix = numpy.matrix([[0,0,0,0],[0,0,0,0],[0,0,1,0],[0,0,0,1]])
# # The control vector, which adds acceleration to the kinematic equations.
# # 0          =>  x(n+1) =  x(n+1)
# # 0          => vx(n+1) = vx(n+1)
# # -9.81*ts^2 =>  y(n+1) =  y(n+1) + 0.5*-9.81*ts^2
# # -9.81*ts   => vy(n+1) = vy(n+1) + -9.81*ts
# control_vector = numpy.matrix([[0],[0],[0.5*-9.81*timeslice*timeslice],[-9.81*timeslice]])

# # After state transition and control, here are the equations:
# #  x(n+1) = x(n) + vx(n)
# # vx(n+1) = vx(n)
# #  y(n+1) = y(n) + vy(n) - 0.5*9.81*ts^2
# # vy(n+1) = vy(n) + -9.81*ts
# # Which, if you recall, are the equations of motion for a parabola.  Perfect.

# # Observation matrix is the identity matrix, since we can get direct
# # measurements of all values in our example.
# observation_matrix = numpy.eye(4)

# # This is our guess of the initial state.  I intentionally set the Y value
# # wrong to illustrate how fast the Kalman filter will pick up on that.
# initial_state = numpy.matrix([[0],[speedX],[500],[speedY]])

# initial_probability = numpy.eye(4)

# process_covariance = numpy.zeros(4)
# measurement_covariance = numpy.eye(4)*0.2

# kf = KalmanFilterLinear(state_transition, control_matrix, observation_matrix, initial_state, initial_probability, process_covariance, measurement_covariance)

# # Iterate through the simulation.
# for i in range(iterations):
#     x.append(c.GetX())
#     y.append(c.GetY())
#     newestX = c.GetXWithNoise()
#     newestY = c.GetYWithNoise()
#     nx.append(newestX)
#     ny.append(newestY)
#     # Iterate the cannon simulation to the next timeslice.
#     c.Step()
#     kx.append(kf.GetCurrentState()[0,0])
#     ky.append(kf.GetCurrentState()[2,0])
#     kf.Step(control_vector,numpy.matrix([[newestX],[c.GetXVelocity()],[newestY],[c.GetYVelocity()]]))

# # Plot all the results we got.
# pylab.plot(x,y,'-',nx,ny,':',kx,ky,'--')
# pylab.xlabel('X position')
# pylab.ylabel('Y position')
# pylab.title('Measurement of a Cannonball in Flight')
# pylab.legend(('true','measured','kalman'))
# pylab.show()