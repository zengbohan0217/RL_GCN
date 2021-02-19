import random
import torch
import numpy as np
from torch import nn, optim
from tqdm import trange
from GCN import *
from collections import namedtuple

Transition = namedtuple("Transition", ["state", "action", "reward", "next_state", "done"])
# state and next_state is array, action reward and done is a number

class DQN:
    def __call__(self, x):
        self.model_pred.eval()
        return self.model_pred(self.graph, x)

    def __init__(self, graph, point_num, batch_size, batch_num, in_c, hid_c, out_c=1, lr=5e-4, update_rate=1):
        super().__init__()
        self.model_train = GCNnet(in_c=in_c, hid_c=hid_c, out_c=out_c)
        self.model_pred = GCNnet(in_c=in_c, hid_c=hid_c, out_c=out_c)
        self.graph = graph
        self.N = point_num
        self.batch_size = batch_size
        self.batch_num = batch_num
        self.optimizer = optim.SGD(self.model_train.parameters(), lr=lr, momentum=0.2)
        self.loss = nn.SmoothL1Loss()
        self.n_train = 0
        self.gamma = 0.8
        self.update_rate = update_rate
        self.lr_shed = optim.lr_scheduler.StepLR(self.optimizer, 40, 0.8)

    def train_once(self, memory):
        """
        state所保留的信息包括了点的类别，不同类别对应地信息，当前请求运输所在位置，派发资源多少等；
        graph中点的类别包括了救助站、救助点，图中线段信息为点与点之间的距离
        """
        self.model_train.train(True)
        self.optimizer.zero_grad()
        samples = random.sample(memory, self.batch_size)
        states_batch, action_batch, reward_batch, next_states_batch, _ = map(np.array, zip(*samples))
        q_values_next_target = self.model_pred(self.graph, next_states_batch).detach().numpy()
        targets_batch = reward_batch + self.gamma * q_values_next_target.max(axis=1)
        targets_batch = np.maximum(-5, targets_batch)
        targets_batch = torch.FloatTensor(targets_batch.reshape(-1, 1))
        q_values_next_pred = self.model_train(self.graph, states_batch)
        action_batch = torch.tensor(action_batch.reshape(-1, 1), dtype=torch.int64)
        pred_batch = q_values_next_pred.gather(-1, action_batch)
        # train model
        l = self.loss(pred_batch, targets_batch)
        l.backward()
        self.optimizer.step()
        return l.item()

    def train_batch(self, memory):
        loss = 0
        for _ in trange(self.batch_num):
            loss += self.train_once(memory)
        self.lr_shed.step()
        # update pred model
        self.n_train += 1
        if self.n_train % self.update_rate == 0:
            self.model_pred.load_state_dict(self.model_train.state_dict())
            self.model_pred.eval()
        return loss / self.batch_num

def get_epsilon(curr_step, decay_end_step, decay_start_step=0, start_eps=1, end_eps=0.1):
    assert(decay_start_step < decay_end_step)
    curr_step = min(curr_step, decay_end_step)
    pos = max(0, curr_step - decay_start_step)
    return start_eps + (end_eps - start_eps) * (pos) / (decay_end_step - decay_start_step)

def epsilon_greedy(estimator, input_state, eps, point_num):
    # input_state batch_size is 1
    action_pro = np.ones(point_num, dtype=float) * eps / point_num
    q_value = estimator(input_state).detach().numpy()
    best_action = np.argmax(q_value[0])
    action_pro[best_action] += (1.0 - eps)
    action = np.random.choice(np.arange(point_num), p=action_pro)
    return action, best_action


