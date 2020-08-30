
import gym
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import TRPO


# The algorithms require a vectorized environment to run

path = 'C:\Data\Mevea-Gym-Toolbox2\Excavator\Model\\'
kwargs = {'mvs_folder': path}
sim = gym.make('gym_mevea_single:mevea-custom-v0', **kwargs)

env = DummyVecEnv([lambda: sim])

model = TRPO(MlpPolicy, env, verbose=1)
model.learn(total_timesteps=20000)

obs = env.reset()

for i in range(2000):
  action, _states = model.predict(obs)
  obs, rewards, done, info = env.step(action)
  env.render()

