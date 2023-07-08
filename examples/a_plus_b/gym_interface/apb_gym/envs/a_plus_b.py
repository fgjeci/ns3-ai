import gymnasium as gym
from gymnasium import spaces
import numpy as np

import sys
sys.path.append("../../../")
import ns3ai_apb_py as apb

APB_SIZE = 3


class APlusBEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self):
        self.observation_space = spaces.Box(low=0, high=10, shape=(APB_SIZE, 2), dtype=int)
        self.action_space = spaces.Box(low=0, high=20, shape=(APB_SIZE,), dtype=int)

        # create and prepare shared memory
        self._rl = apb.Ns3AiRl(4096, True, True, "My Seg", "My Env", "My Act", "My Lockable")
        assert len(self._rl.m_act) == 0
        self._rl.m_act.resize(APB_SIZE)
        assert len(self._rl.m_env) == 0
        self._rl.m_env.resize(APB_SIZE)

        # init observation and info
        self._obs = np.zeros((APB_SIZE, 2), dtype=int)
        self._info = {
            "sum": np.zeros(APB_SIZE, dtype=int),
        }
        self._is_finished = False

    def _get_obs(self):
        return self._obs

    def _get_info(self):
        return self._info

    def _get_env_from_shared_mem(self):
        # get obs and info(sum of two envs)
        if self._rl.is_finished():
            self._is_finished = True
            return
        self._rl.get_env_begin()
        for i in range(APB_SIZE):
            self._obs[i] = [self._rl.m_env[i].a, self._rl.m_env[i].b]
            self._info["sum"][i] = self._rl.m_env[i].a + self._rl.m_env[i].b
        self._rl.get_env_end()

    def reset(self, seed=None, options=None):
        # seed self._np_random
        super().reset(seed=seed)

        self._get_env_from_shared_mem()

        observation = self._get_obs()
        info = self._get_info()

        return observation, info

    def step(self, action):
        self._rl.set_act_begin()
        for i in range(APB_SIZE):
            self._rl.m_act[i].c = action[i]
        self._rl.set_act_end()

        self._get_env_from_shared_mem()
        terminated = self._is_finished
        reward = 1 if terminated else 0  # Binary sparse rewards
        observation = self._get_obs()
        info = self._get_info()

        return observation, reward, terminated, False, info

    def close(self):
        del self._rl
