import numpy as np
import cvxpy as cp
import variance_calcs as vc
from parser import SIPParser

class Portfolio:
   def __init__(self):
      self.port = {}
   
   # TODO: add function to turn SIPs on/off BEFORE portfolio building/calcs
   # Will probably need to edit input from parser separately
   def construct_port(self, source, type='c', mu_p=None, rng=None):
      """
      Creates an individual Portfolio object using SIP data
      :param source: SIP trial data used to construct portfolio
      :param type: can select custom, random, or Markowitz-efficient weights
      :return self.port: returns singular Portfolio object with desired asset weights
      """
      port = {}

      if type == 'c':
         port['weights'] = self.cust_weights(source)
         port_type = 'cust'
      elif type == 'r':
         if rng is None:
            raise ValueError("RNG must be provided for random portfolio generation.")
         port['weights'] = self.rand_weights(source, rng=rng)
         port_type = 'rand'
      elif type == 'e':
         # TODO: add weights calculation for Pareto-efficient port using 10% OM
         port['weights'] = self.eff_weights(source, mu_p)
         port_type = 'eff'
      else:
         raise ValueError("Invalid portfolio type.")

      count = len(source)
      num_trials = len(source[0]['trials'])
      expected_rev = 0.0

      # Creates empty array for new weighted combination of trials
      new_trials = np.zeros(num_trials)
   
      # Recalculates expected revenue & trial data for random portfolio as a weighted combination of asset data
      for i in range(count):
         expected_rev += source[i]['metadata']['ExpectedRevenue'] * port['weights'][i]

         # Converts 'assets' to NumPy array (because the calculations don't work otherwise :/ )
         old_trials = np.array(source[i]['trials'], dtype='f')

         for j in range(num_trials):
            new_trials[j] += old_trials[j] * port['weights'][i]
      
      # Split the avg_return & variance calculations into two processes since it kept throwing a runtime error :/
      mean = np.mean(new_trials)
      var = np.var(new_trials)
      percentile = np.percentile(new_trials, 10)      # TODO: make user-defined!
         
      port['metadata'] = {
         'PortType': port_type,
         'ExpectedRevenue': expected_rev,
         'AverageReturn': mean * expected_rev,
         'Variance': var * (expected_rev ** 2),
         'PercentileOM': percentile * expected_rev,
         'IsParetoEff': False
      }

      port['trials'] = new_trials

      return port
   
   def cust_weights(self, source):
      """
      Allows user to input custom asset weights for portfolio generation
      :param source: SIP trial data
      :return weights: an array of size count with user-defined asset weights
      """
      
      count = len(source)
      # Default: all assets weighted uniformly
      weights = np.full(count, 1/count)

      # I built this system like an RPG character stat builder, there's absolutely an easier/more UI-friendly way to do this
      # The theory on this is that every 10 "port points" represents 1% of the total custom portfolio build - i.e. if an asset is assigned 400 port points, it represents 40% of the portfolio by volume 
      port_points = 1000
      for i in range(count):
         asset_points = int(input(f"Weight for Asset {i + 1}:\n"))
         port_points -= asset_points
         if (asset_points < 0) or (port_points < 0):
            raise ValueError("Invalid asset weight!")
         print(f"Port points remaining: {port_points}\n")
         weights[i] = asset_points/1000

         for j in range(i + 1, count):
            weights[j] = (1000 - port_points)/(count * 1000)

      # Normalizes custom input weights to ensure 100% of assets are allocated
      if port_points > 0:
         # TODO: add user prompt re: normalizing asset weights
         for i in range(count):
            old = weights[i]
            weights[i] = (old * 1000)/(1000 - port_points)

      return weights

   
   def rand_weights(self, source, rng):
      """
      Generates Dirichlet-random asset weights for portfolio object
      :param source: SIP trial data
      :param rng: random number generator instance
      :return weights: array of size count random asset weights
      """
      
      # TODO: give users more control over alpha values => control "degree of randomness"
      count = len(source)

      # Generate alpha parameters: uniform [0, 1) + integer [0, 100)
      alphas = rng.random(count) + rng.integers(100, size=count)
      # alphas = np.random.rand(count) + np.random.randint(100, size=count)
      weights = rng.dirichlet(alphas)

      return weights

   def eff_weights(self, group_data, mu_p):
      """
      Calculates Markowitz efficient asset weights
      :param source: SIP trial data
      :param mu_p: desired average return value for portfolio
      :return weights: array of size count efficient asset weights (minimizes variance for given average return)
      """

      # TODO: implement framework for user-input desired return mu_p
      mu_hat, sig_matrix, unit_vector = vc.create_matrices(group_data)
      n = len(mu_hat)

      # Define optimization variables
      w = cp.Variable(n)
      # Objective: minimize variance
      objective = cp.Minimize(cp.quad_form(w, sig_matrix))
      # Constraints: target return mu_p, sum-to-one, non-negativity
      constraints = [
         mu_hat.T @ w == mu_p,
         cp.sum(w) == 1,
         w >= 0
      ]

      # Solve quadratic program
      prob = cp.Problem(objective, constraints)
      prob.solve(
         solver=cp.SCS, # deterministic solver for QP
         warm_start=False
      )

      if w.value is None:
         raise ValueError("No feasible solution found for given target return.")
      
      weights = np.array(w.value).flatten()
      # Trim floating-point errors
      weights[np.abs(weights) < 1e-8] = 0
      """if np.any(weights < -1e-6):
         print("Warning: Infeasible solution or solver tolerance too loose.")"""
      return weights

if __name__ == "__main__":
   SLURP = SIPParser("data/mock_sipmath_v2.xlsx")
   # SLURP = SIPParser("data/small_SIP.xlsx")
   group_data = SLURP.investments

   # Test for custom case:
   """ gen = Portfolio()
   cust = gen.construct_port(group_data)
   print(cust['metadata']['AverageReturn'], cust['metadata']['Variance'], cust['weights'], sep=', ') """
   
   # Test for random case:
   """ sample_portfolios = []
   for i in range(10):
      gen = Portfolio()
      rand = gen.construct_port(group_data, 'r')
      sample_portfolios.append(rand)

   for port in sample_portfolios:
      print(port['metadata']['AverageReturn'], port['metadata']['Variance'], port['weights'], sep=', ') """

   # Test for efficient case:
   gen = Portfolio()
   mu_p = int(input("Desired average return: "))
   while mu_p != 0:
      eff = gen.construct_port(group_data, 'e')
      print(eff['metadata']['AverageReturn'], np.sqrt(eff['metadata']['Variance']), eff['weights'], sep=', ')
   



   
