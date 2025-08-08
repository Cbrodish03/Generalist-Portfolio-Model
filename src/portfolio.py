import numpy as np
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
         
      self.port['metadata'] = {
         'PortType': port_type,
         'ExpectedRevenue': expected_rev,
         'AverageReturn': mean * expected_rev,
         'Variance': var * expected_rev
      }

      self.port['trials'] = new_trials

      return self.port
   
   def rand_weights(self, source):
      # TODO: give users more control over alpha values => control "degree of randomness"
      count = len(source)
      alphas = np.random.rand(count) + np.random.randint(100, size=count)
      weights = np.random.dirichlet(alphas)

      return weights

   def eff_weights(self, group_data):
      # TODO: implement framework for user-input desired return mu_p
      # Step 1: Create empty ndarray to store mean values, NxN matrix for variances
      mu_hat = np.empty(len(group_data))
      sig_matrix = np.empty((len(group_data), len(group_data)))

      # Step 2: Initialize mu_hat, sig_matrix with avg return & variance for each SIP
      for sip in group_data:
         nptrials = np.array(sip['trials'], dtype='f')

         mu_hat[sip['group_index']] = np.average(nptrials) * sip['metadata']['ExpectedRevenue']
         sig_matrix[sip['group_index']][sip['group_index']] = np.var(nptrials) * sip['metadata']['ExpectedRevenue']

      # Step 3: Populate covariance values with 0
      # TODO: Implement covariance calcs for investment tethering functionality
      for i in range(len(group_data)):
         for j in range(len(group_data)):
            if sig_matrix[i][j] == None:
               sig_matrix[i][j] = 0
      sig_inverse = np.linalg.inv(sig_matrix)
   
      unit_vector = np.empty(len(group_data))
      unit_vector.fill(1)
      U = np.vstack((mu_hat, unit_vector))

      # Turns mu_hat, unit_vector into vectors (1 row, n columns) for matrix operations
      mu_hat = mu_hat.transpose()
      unit_vector = unit_vector.transpose()
      U = U.transpose()

      M = np.matmul(np.matmul(U.transpose(), sig_inverse), U)
      M_inverse = np.linalg.inv(M)

      # THIS IS THE DESIRED RETURN VARIABLE!!
      mu_p = 250000
      u = np.array([mu_p, 1])
      u = u.transpose()

      weights = np.matmul(np.matmul(np.matmul(sig_inverse, U), M_inverse), u)
      return weights

if __name__ == "__main__":
   SLURP = SIPParser("data/mock_sipmath_v2.xlsx")
   # SLURP = SIPParser("data/small_SIP.xlsx")
   group_data = SLURP.investments

   # Test for random case:
   sample_portfolios = []
   for i in range(10):
      gen = Portfolio()
      rand = gen.construct_port(group_data, 'r')
      sample_portfolios.append(rand)

   for port in sample_portfolios:
      print(port['metadata']['AverageReturn'], port['metadata']['Variance'], port['weights'], sep=', ')

   # Test for efficient case:
   gen = Portfolio()
   eff = gen.construct_port(group_data, 'e')
   print(eff['metadata']['AverageReturn'], eff['metadata']['Variance'], eff['weights'], sep=', ')
   



   