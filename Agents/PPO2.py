import gym
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import PPO2


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

# The algorithms require a vectorized environment to run
path = 'C:\Data\MeveaOpenAIGym\Gym-Examples\CustomModels\WheelLoader\\'

env_list = []

for i in range(4):
  kwargs = {'mvs_folder': path}
  sim = gym.make('gym_mevea_single:mevea-custom-v0', **kwargs)
  env = DummyVecEnv([lambda: sim])



model = PPO2(MlpPolicy, env, verbose=1)
model.learn(total_timesteps=20000)

for env in env_list:
  obs = env.reset()

for i in range(2000):
  for env in env_list:
    print(env_list.index(env))
    action, _states = model.predict(obs)
    obs, rewards, done, info = env.step(action)

for env in env_list:
  env.close()


'''
# Our firewall does not allow it, but could be an option

import ray
from ray.tune.registry import register_env
from ray.rllib.agents.ppo import ppo

def env_creator(env_config):
    import gym
    path = 'C:\Data\Mevea-Gym-Toolbox2\Excavator\Model\\'
    kwargs = {'mvs_folder': path}
    return gym.make('gym_mevea_single:mevea-custom-v0', **kwargs)  # or return your own custom env

env_creator_name = "custom_env"
register_env(env_creator_name, env_creator)

ray.init()
agent = ppo.PPOAgent(env=env_creator_name, config={
    "env_config": {},  # config to pass to env creator
})
'''