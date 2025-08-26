import numpy as np
import variance_calcs as vc
from parser import SIPParser

class Portfolio:
   def __init__(self):
      self.port = {}
   
   # TODO: add function to turn SIPs on/off BEFORE portfolio building/calcs
   # Will probably need to edit input from parser separately
   def construct_port(self, source, type='c'):
      if type == 'c':
         self.port['weights'] = self.cust_weights(source)
         port_type = 'cust'
      elif type == 'r':
         self.port['weights'] = self.rand_weights(source)
         port_type = 'rand'
      elif type == 'e':
         # TODO: add weights calculation for Pareto-efficient port using 10% OM
         self.port['weights'] = self.eff_weights(source)
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
         expected_rev += source[i]['metadata']['ExpectedRevenue'] * self.port['weights'][i]

         # Converts 'assets' to NumPy array (because the calculations don't work otherwise :/ )
         old_trials = np.array(source[i]['trials'], dtype='f')

         for j in range(num_trials):
            new_trials[j] += old_trials[j] * self.port['weights'][i]
      
      # Split the avg_return & variance calculations into two processes since it kept throwing a runtime error :/
      mean = np.mean(new_trials)
      var = np.var(new_trials)
      percentile = np.percentile(new_trials, 10)
         
      self.port['metadata'] = {
         'PortType': port_type,
         'ExpectedRevenue': expected_rev,
         'AverageReturn': mean * expected_rev,
         'Variance': var * expected_rev,
         'TenPercentOM': percentile * expected_rev
      }

      self.port['trials'] = new_trials

      return self.port
   
   def cust_weights(self, source):
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

      if port_points > 0:
         # TODO: add user prompt re: normalizing asset weights
         for i in range(count):
            old = weights[i]
            weights[i] = (old * 1000)/(1000 - port_points)

      return weights

   
   def rand_weights(self, source):
      # TODO: give users more control over alpha values => control "degree of randomness"
      count = len(source)
      alphas = np.random.rand(count) + np.random.randint(100, size=count)
      weights = np.random.dirichlet(alphas)

      return weights

   def eff_weights(self, group_data):
      # TODO: implement framework for user-input desired return mu_p
      mu_hat, sig_inverse, unit_vector = vc.create_matrices(group_data)
      U = np.column_stack((mu_hat, unit_vector))

      M = np.matmul(np.matmul(U.transpose(), sig_inverse), U)
      M_inverse = np.linalg.inv(M)

      mu_p = 190000     # THIS IS THE DESIRED RETURN VARIABLE!!
      u = np.array([mu_p, 1])
      u = u.transpose()

      weights = np.matmul(np.matmul(np.matmul(sig_inverse, U), M_inverse), u)
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
   eff = gen.construct_port(group_data, 'e')
   print(eff['metadata']['AverageReturn'], np.sqrt(eff['metadata']['Variance']), eff['weights'], sep=', ')
   



   