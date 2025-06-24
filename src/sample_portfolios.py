import numpy as np
import matplotlib.pyplot as plt
from parser import SIPParser
import os
import pandas as pd
import math

class RandomPortfolios:
   def __init__(self):
      self.sample_ports = []

   def random_port(assets, port_index):
      count = assets[-1]['group_index']
      num_trials = len(assets[0]['trials'])
      expected_rev = 0

      alphas = np.random.rand(count)
      weights = np.random.dirichlet(alphas)

      new_trials = np.empty(num_trials)
   
      for i in range(count):
         expected_rev += assets[i]['metadata']['ExpectedRevenue'] * weights[i]

         for j in range(num_trials):
            new_trials[j] += assets[i]['trials'][j] * weights[i]
      
   
      random_port = {
         'port_index': port_index,
         'expected_revenue': expected_rev,
         'avg_return': expected_rev * np.mean(new_trials),
         'variance': np.var(new_trials),
         'asset_weights': weights,
         'trials': new_trials
      }

      return random_port

   def generate_sample(source):
      sample_ports = []
      # Theoretically this 'count' variable should be user-generated?
      count = 20

      for i in range(count):
         sample_ports.append(RandomPortfolios.random_port(source, i))
   
      print(sample_ports)

if __name__ == "__main__":
   SLURP = SIPParser("data/small_SIP.xlsx")
   SLURP.parse_xlsx()

   sample_portfolios = RandomPortfolios.generate_sample(SLURP.group_data)







