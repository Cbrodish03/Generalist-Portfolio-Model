import numpy as np
from parser import SIPParser
from portfolio import Portfolio

"""
Dirichlet-random portfolio generator built for Generalist-Portfolio-Model
Works with SIP Standard 2.0-compliant files
"""
class RandomPortfolios:
   def __init__(self, seed: int | None = None):
      """
      Owns the RNG used for all random portfolio generation
      If seed is None, behavior is non-deterministic
      :param seed: the seed for the random number generator
      """
      self.sample_ports = []
      self.seed = seed
      self.rng = np.random.default_rng(seed)

   def generate_sample(self, source, count=10):
      """
      Returns a set of [count] Dirichlet random portfolios
      :param source: SIP trial data
      :param count: number of random portfolios to generate
      :return self.sample_ports: fully initialized instance of RandomPortfolios class
      """

      self.sample_ports = [] # reset sample ports for repeatable calls

      # Fill array with random ports
      for i in range(count):
         port = Portfolio()
         rand = port.construct_port(source, 'r', rng=self.rng)
         self.sample_ports.append(rand)
      
      # Evaluate which random ports are Pareto efficient
      self.pareto_eval()
      
      return self.sample_ports
   
   def pareto_eval(self):
      """
      Evaluates which elements (portfolios) of array are Pareto efficient (maximizes both average return & percentile OM)
      """

      # Creates 2D array of points to maximize
      size = len(self.sample_ports)
      costs = np.empty(shape=(size, 2))
      for i in range(size):
         costs[i] = [ self.sample_ports[i]['metadata']['PercentileOM'], self.sample_ports[i]['metadata']['AverageReturn'] ]
      
      is_efficient = np.arange(costs.shape[0])
      n_points = costs.shape[0]
      next_point_index = 0

      while next_point_index < len(costs):
         nondominated_point_mask = np.any(costs > costs[next_point_index], axis=1)
         nondominated_point_mask[next_point_index] = True
         is_efficient = is_efficient[nondominated_point_mask]
         costs = costs[nondominated_point_mask]
         next_point_index = np.sum(nondominated_point_mask[:next_point_index]) + 1
      
      is_efficient_mask = np.zeros(n_points, dtype=bool)
      is_efficient_mask[is_efficient] = True

      for i in range(size):
         self.sample_ports[i]['metadata']['IsParetoEff'] = is_efficient_mask[i]
      
if __name__ == "__main__":
   SLURP = SIPParser("data/mock_sipmath_v2.xlsx")
   # SLURP = SIPParser("data/small_SIP.xlsx")
   group_data = SLURP.investments

   gen = RandomPortfolios()
   sample_portfolios = gen.generate_sample(group_data, count=100)

   for port in sample_portfolios:
      print(port['metadata']['AverageReturn'], port['metadata']['Variance'], port['weights'], sep=', ')







