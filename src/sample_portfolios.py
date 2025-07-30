import numpy as np
from parser import SIPParser


class RandomPortfolios:
   def __init__(self):
      self.sample_ports = []

   def random_port(assets, port_index):
      """
      Creates a single random portfolio of SIP assets using Dirichlet-distributed random weights
      """
      count = assets[-1]['group_index']
      num_trials = len(assets[0]['trials'])
      expected_rev = 0

      # Generates Dirichlet-random weights for portfolios given array of concentration parameters 'alphas'
      # NOTE on 'alphas': higher alpha values => more "uniformly random" weights
      alphas = np.random.rand(count)
      alphas += np.random.randint(100, size=count)
      weights = np.random.dirichlet(alphas)

      # Creates empty array for new weighted combination of trials
      new_trials = np.empty(num_trials)
   
      # Recalculates expected revenue & trial data for random portfolio as a weighted combination of asset data
      for i in range(count):
         expected_rev += assets[i]['metadata']['ExpectedRevenue'] * weights[i]

         # Converts 'assets' to NumPy array (because the calculations don't work otherwise :/ )
         old_trials = np.array(assets[i]['trials'], dtype='f')

         # I KNOW this is the problem area in this program, but I'm not sure how to make this calculation more efficient while still doing what I want it to do
         for j in range(num_trials):
            new_trials[j] += old_trials[j] * weights[i]
      
      # Split the avg_return & variance calculations into two processes since it kept throwing a runtime error :/
      mean = np.mean(new_trials)
      var = np.var(new_trials)

      # Constructs a dictionary to package random portfolio information
      # Similar to structure from SIPParser
      random_port = {
         'port_index': port_index,
         'expected_revenue': expected_rev,
         'avg_return': mean * expected_rev,
         'variance': var * expected_rev,
         'asset_weights': weights,
         'trials': new_trials
      }

      return random_port

   def generate_sample(source):
      """
      Returns a set of [count] Dirichlet random portfolios
      """
      sample_ports = []
      
      count = int(input("How many Dirichlet-random portfolios would you like to generate?\n"))

      # TODO: implement parameters for generation (min average return, etc)
      for i in range(count):
         sample_ports.append(RandomPortfolios.random_port(source, i))
      
      return sample_ports

if __name__ == "__main__":
   SLURP = SIPParser("data/mock_sipmath_v2.xlsx")
   # SLURP = SIPParser("data/small_SIP.xlsx")
   group_data = SLURP.investments

   sample_portfolios = RandomPortfolios.generate_sample(group_data)
   for port in sample_portfolios:
      print(port['avg_return'], port['variance'], port['asset_weights'], sep=', ')







