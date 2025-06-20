import numpy as np
import parser

group_data = parser.SIPParser("data/small_SIP.xlsx")

# TODO: implement binary toggle on/off for individual SIPs here?

def avg_return_vector(group_data):
   """
   Calculates & stores average return value for each SIP
   """
   # Step 1: Create empty ndarray to store values
   mu_hat = np.empty(len(group_data))

   # Step 2: Initialize mu_hat with avg return for each SIP
   for sip in group_data:
      mu_hat[sip['group_index']] = np.average(sip['trials']) * sip['metadata']['ExpectedRevenue']
   
   return mu_hat

def covariance_matrix(group_data):
   """
   Initializes & populates a NxN matrix containing (co)variance of all SIPs
   """
   # Step 1: Create empty NxN array to store values
   sig_matrix = np.empty((len(group_data), len(group_data)))

   # Step 2: Initialize with variance values
   for sip in group_data:
      sig_matrix[sip['group_index']['group_index']] = np.var(sip['trials']) * sip['metadata']['ExpectedRevenue']

   # Step 3: Populate covariance values with 0
   # TODO: Implement covariance calcs for investment tethering functionality
   for i,j in len(group_data):
      if sig_matrix[i][j] == None:
         sig_matrix[i][j] = 0
   
   return sig_matrix

