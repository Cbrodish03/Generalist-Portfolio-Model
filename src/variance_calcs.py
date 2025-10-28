import numpy as np

def create_matrices(group_data):
   """
   Compiles individual asset mean & variance data into matrices for efficient-frontier calculations
   :param group_data: SIP trial data
   :return mu_hat: vector containing average return data for calculations
   :return sig_inverse: 2D array (inverted) of SIP data variance
   :return unit_vector: n-dimensional unit vector
   """
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
   
   unit_vector = np.empty(len(group_data))
   unit_vector.fill(1)

   # Turns mu_hat, unit_vector into vectors (1 row, n columns) for matrix operations
   mu_hat = mu_hat.transpose()
   unit_vector = unit_vector.transpose()

   return mu_hat, sig_matrix, unit_vector

def compute_coeffs(group_data):
   """
   Computes numerical coefficients for efficient-frontier equation, given SIP data on mean & variance
   :param group_data: SIP trial data
   :return a, b, c: coefficients in efficient frontier equation
   :return ymax: maximum average return value
   """
   mu_hat, sig_matrix, unit_vector = create_matrices(group_data)
   sig_inverse = np.linalg.inv(sig_matrix)

   # Finds maximum avg return value (for graphing purposes)(this should prob go somewhere else)
   ymax = np.max(mu_hat.transpose())

   # Computes individual terms in denominator expression
   x = np.matmul(np.matmul(mu_hat.transpose(), sig_inverse), mu_hat)
   y = np.matmul(np.matmul(unit_vector.transpose(), sig_inverse), unit_vector)
   z = np.matmul(np.matmul(unit_vector.transpose(), sig_inverse), mu_hat)

   denom = x * y - (z ** 2)

   # Computes numerical coefficients in efficient-frontier equation
   a = (np.matmul(np.matmul(unit_vector.transpose(), sig_inverse), unit_vector)) / denom
   b = 2 * (np.matmul(np.matmul(unit_vector.transpose(), sig_inverse), mu_hat)) / denom
   c = (np.matmul(np.matmul(mu_hat.transpose(), sig_inverse), mu_hat)) / denom

   return a, b, c, ymax