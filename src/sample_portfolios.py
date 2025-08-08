import numpy as np
from parser import SIPParser
from portfolio import Portfolio

"""
Dirichlet-random portfolio generator built for Generalist-Portfolio-Model
Works with SIP Standard 2.0-compliant files
"""
class RandomPortfolios:
   def __init__(self):
      self.sample_ports = []

   def generate_sample(self, source, count=10):
      """
      Returns a set of [count] Dirichlet random portfolios
      """
      for i in range(count):
         port = Portfolio()
         rand = port.construct_port(source, 'r')
         self.sample_ports.append(rand)
      
      return self.sample_ports
      
if __name__ == "__main__":
   SLURP = SIPParser("data/mock_sipmath_v2.xlsx")
   # SLURP = SIPParser("data/small_SIP.xlsx")
   group_data = SLURP.investments

   gen = RandomPortfolios()
   sample_portfolios = gen.generate_sample(group_data, count=100)

   for port in sample_portfolios:
      print(port['metadata']['AverageReturn'], port['metadata']['Variance'], port['weights'], sep=', ')







