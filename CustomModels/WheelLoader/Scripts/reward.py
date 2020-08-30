'''
==========================================================================
This is a file where you can write your own implementation of the reward
function or any other custom function:

get_reward:     calculate your custom reward here.      returns reward.
custom_start:   called at the start of the simulation   returns your value
custom_tick:    called at each timestep                 returns your value
==========================================================================
'''

from random import uniform
import math

class Reward:

    def __init__(self, GObject, GSolver, GDict, MVec3):
        
        # Get Mevea classes
        self.GObject = GObject
        self.GSolver = GSolver
        self.GDict   = GDict
        self.MVec3   = MVec3

    def get_reward(self):

        speed_x = self.GDict['DataSource2'].getDsValue()
        speed_z = self.GDict['DataSource3'].getDsValue()
        collisions = self.GDict['DataSource4'].getDsValue()

        return abs((speed_x + speed_z)) - collisions

    def custom_start(self):
        
        pass


    # Will be called each timestep
    def custom_tick(self):

        pass
