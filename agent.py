


import torch
from torch.optim import Adam
import torch.nn.functional as F
import random
import numpy as np

from pytorch_model import pytorch_DQNetwork
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

from memory import replayMemory

LR = 5e-4
MEMORY_SIZE = 1e6
UPDATE_FREQUENCY = 4
MIN_MEMORY_SIZE = 1000
GAMMA = 0.9
TRANSFER_RATE = 0.001


class Agent():
    def __init__(self, state_space, action_space, seed, batch_size):

        self.state_space = state_space
        self.action_space = action_space
        self.seed = random.seed(seed)
        self.batch_size = batch_size

        '''DQNetwork'''

        self.local_model = pytorch_DQNetwork(state_space, action_space, seed).to(device)
        self.target_model = pytorch_DQNetwork(state_space, action_space, seed).to(device)
        self.optimizer = Adam(self.local_model.parameters(), lr=LR)

        '''Replay Memory'''

        self.memory = replayMemory(action_space, MEMORY_SIZE, batch_size, seed)

        '''How often to update the model'''

        self.update_every = 0

    def step(self, state, action, reward, next_state, done):
        '''

        :param state:
        :param action:
        :param reward:
        :param next_state:
        :param done:
        :return:
        '''

        '''save experience to memory'''
        self.memory.add(state, action, reward, next_state, done)

        self.update_every += 1
        if(self.update_every % UPDATE_FREQUENCY == 0):
            if(len(self.memory) > self.batch_size):
                experience = self.memory.sample()
                self.learn(experience, GAMMA)

    def learn(self, experience, gamma):
        '''

        :param experience:
        :param gamma:
        :return:
        '''

        sampled_state, sampled_action, sampled_reward, sampled_next_state, sampled_done = experience

        next_value = self.target_model(sampled_next_state).detach().max(1)[0].unsqueeze(1)


        DQN_target = sampled_reward + (gamma * next_value * (1 - sampled_done))

        DQN_estimation = self.local_model(sampled_state).gather(1, sampled_action)

        loss = F.mse_loss(DQN_estimation, DQN_target)

        '''delta for priority reply'''
        #delta = np.abs(DQN_estimation - DQN_target)


        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.soft_update(self.local_model, self.target_model, TRANSFER_RATE)

    def soft_update(self, local_model, target_model, transfer_rate):
        '''

        :param local_model:
        :param target_model:
        :param transfer_rate:
        :return:
        '''

        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(transfer_rate * local_param.data + (1.0 - transfer_rate) * target_param.data)

    def act(self, state, epsilon=0.):
        '''

        :param state:
        :param epsilon:
        :return:
        '''

        state = torch.from_numpy(state).float().unsqueeze(0).to(device)

        self.local_model.eval()
        with torch.no_grad():
            action_value = self.local_model(state)
        self.local_model.train()

        if(np.random.uniform(0,1,1) < epsilon):
            action = np.random.choice(np.arange(self.action_space))
        else:
            action = np.argmax(action_value.cpu().data.numpy())

        return action






