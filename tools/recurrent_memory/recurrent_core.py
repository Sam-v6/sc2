"""CPU inference prototype: parent encoder plus a 32-unit residual GRU.

Memory is explicit (hidden state, previous selected action). Call sequence without
memory only at an episode boundary. No optimizer or game integration is provided.
"""
import numpy as np


class RecurrentCore:
    def __init__(self, parent, seed):
        self.network = [array.copy() for array in parent.network]
        self.actions = list(parent.actions)
        rng = np.random.default_rng(seed)
        inputs = 64+len(self.actions)
        self.weight_ih = rng.normal(0, 1/np.sqrt(inputs), (96, inputs))
        self.weight_hh = rng.normal(0, 1/np.sqrt(32), (96, 32))
        self.bias_ih = np.zeros(96)
        self.bias_hh = np.zeros(96)
        self.actor = np.zeros((32, len(self.actions)))
        self.value = np.zeros(32)

    def step(self, observation, memory):
        hidden, previous = memory
        w1, b1, w2, b2, wv, bv = self.network
        encoded = np.tanh(observation @ w1+b1)
        onehot = np.zeros(len(self.actions))
        if previous != -1:
            onehot[previous] = 1
        inputs = np.concatenate([encoded, onehot])
        ir, iz, inn = np.split(inputs @ self.weight_ih.T+self.bias_ih, 3)
        hr, hz, hn = np.split(hidden @ self.weight_hh.T+self.bias_hh, 3)
        reset = .5*(1+np.tanh((ir+hr)/2))
        update = .5*(1+np.tanh((iz+hz)/2))
        candidate = np.tanh(inn+reset*hn)
        hidden = (1-update)*candidate+update*hidden
        return encoded @ w2+b2+hidden @ self.actor, encoded @ wv+bv+hidden @ self.value, hidden

    def sequence(self, observations, selected, memory=None):
        if memory is None:
            memory = (np.zeros(32), -1)
        logits, values = [], []
        assert len(observations) == len(selected)
        for observation, action in zip(observations, selected):
            logit, value, hidden = self.step(observation, memory)
            logits.append(logit)
            values.append(value)
            memory = (hidden, int(action))
        return np.asarray(logits), np.asarray(values), memory
