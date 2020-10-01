"""
A tutorial example of how to use PPO-CMA
"""

import tensorflow as tf
from Agent import Agent
#import mevea_env as gym
import gym

#Simulation budget (steps) per iteration. This is the main parameter to tune.
#8k works for relatively simple environments like the OpenAI Gym Roboschool 2D Hopper.
#For more complex problems such as 3D humanoid locomotion, try 32k or even 64k.
#Larger values are slower but more robust.
N=80

# Stop training after this many steps
max_steps=100000

# Init tensorflow
sess = tf.InteractiveSession()

# Create environment (replace this with your own simulator)
print("Creating simulation environment")

'''
=============================================================
To open other mevea simulator provide simulation folder path:
=============================================================

path = 'C:\Data\MeveaOpenAIGym\Gym-Examples\CustomModels\Excavator\Model'
kwargs = {'mvs_folder': path}
sim = gym.make('gym_mevea_single:mevea-custom-v0', **kwargs)


path = 'C:\Data\MeveaOpenAIGym\Gym-Examples\CustomModels\WheelLoader\\'
kwargs = {'mvs_folder': path}
sim = gym.make('gym_mevea_single:mevea-custom-v0', **kwargs)


path = 'C:\Data\MeveaOpenAIGym\Gym-Examples\CustomModels\Jib_Crane\\'
kwargs = {'mvs_folder': path}
sim = gym.make('gym_mevea_single:mevea-custom-v0', **kwargs)
'''
path = 'C:\Data\MeveaOpenAIGym\Gym-Examples\CustomModels\Excavator\Model'
kwargs = {'mvs_folder': path}
sim = gym.make('gym_mevea_single:mevea-custom-v0', **kwargs)
# Run tutorial Jib Crane model 
#sim = gym.make('gym_mevea_single:mevea-custom-v0')

# Create the agent
agent=Agent(
    stateDim=sim.observation_space.low.shape[0]
    , actionDim=sim.action_space.low.shape[0]
    , actionMin=sim.action_space.low
    , actionMax=sim.action_space.high
)


# Finalize initialization
tf.global_variables_initializer().run(session=sess)
agent.init(sess)  # must be called after TensorFlow global variables init

# Main training loop
totalSimSteps = 0
while totalSimSteps < max_steps:

    #Run episodes until the iteration simulation budget runs out
    iterSimSteps = 0
    while iterSimSteps < N:

        # Reset the simulation 
        observation = sim.reset()

        # Simulate this episode until done
        while True:

            # Query the agent for action given the state observation
            action = agent.act(sess,observation)
            
            #Simulate using the action
            #Note: this tutorial does not repeat the same action for two steps, 
            #unlike the Run.py script used for the ICML paper results.
            #Repeating the action for multiple steps seems to yield better exploration 
            #in most cases, possibly because it reduces high-frequency action noise.
            nextObservation, reward, done, info = sim.step(action[0, :])
            
            # Save the experience point
            agent.memorize(observation,action,reward,nextObservation,done)
            observation=nextObservation

            # Bookkeeping
            iterSimSteps += 1

            # Episode terminated? (e.g., due to time limit or failure)
            if done: 
                break

    #All episodes of this iteration done, update the agent and print results
    averageEpisodeReturn=agent.updateWithMemorized(sess,verbose=False)
    totalSimSteps += iterSimSteps
    print("Simulation steps {}, average episode return {}".format(totalSimSteps,averageEpisodeReturn))

sim.close()