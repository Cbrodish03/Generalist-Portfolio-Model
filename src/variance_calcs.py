import numpy as np

def create_matrices(group_data):
   """
   Compiles individual asset mean & variance data into matrices for efficient-frontier calculations.

   Assumptions:
   - `sip['trials']` are in the same *unit* as ExpectedRevenue (i.e. if trials are per-unit returns,
     and you want mean/variance in dollars, scale mean by ExpectedRevenue and variance by ExpectedRevenue**2).
   - We create a diagonal covariance matrix (off-diagonals zero) for now.
   """
   n = len(group_data)
   if n == 0:
      raise ValueError("group_data must contain at least one SIP")

   # start with zeros (avoid np.empty garbage)
   mu_hat = np.zeros(n, dtype=float)
   sig_matrix = np.zeros((n, n), dtype=float)

   # populate diagonal entries
   for sip in group_data:
      idx = sip['group_index']
      nptrials = np.array(sip['trials'], dtype=float)

      # expected revenue (scale)
      rev = sip['metadata'].get('ExpectedRevenue', 1.0)
      if rev is None:
         rev = 1.0

      # mean scaled linearly by revenue (same as your original intent)
      mu_hat[idx] = np.mean(nptrials) * rev

      # variance must be scaled by the square of the linear scale factor
      sig_matrix[idx, idx] = np.var(nptrials) * (rev ** 2)

   # If you later compute covariances, fill off-diagonals here.
   # For now they remain zero (i.e., assets treated as uncorrelated).

   # Small relative regularization (so we don't destroy the frontier)
   # Use a tiny fraction of the average diagonal element.
   diag_mean = np.mean(np.diag(sig_matrix))
   if diag_mean == 0:
      # fallback absolute tiny epsilon if all variances are zero
      eps = 1e-12
   else:
      eps = diag_mean * 1e-10  # extremely small relative regularization

   sig_matrix += np.eye(n) * eps

   unit_vector = np.ones(n, dtype=float)

   # Invert - keep numeric checks for safety
   det = np.linalg.det(sig_matrix)
   if abs(det) < 1e-20:
      # last-resort fallback regularization (still tiny)
      sig_matrix += np.eye(n) * (1e-8)
      # recompute det after extra reg
      det = np.linalg.det(sig_matrix)
      if abs(det) < 1e-20:
         raise np.linalg.LinAlgError("Covariance matrix is singular even after tiny regularization.")

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
   ymax = np.max(mu_hat)

   # Computes individual terms in denominator expression

   # print statements for debug
   # print("mu_hat.transpose = ", mu_hat.transpose())
   # print("sig_inverse = ", sig_inverse)
   # print("mu_hat = ", mu_hat)

   x = np.matmul(np.matmul(mu_hat.transpose(), sig_inverse), mu_hat)
   y = np.matmul(np.matmul(unit_vector.transpose(), sig_inverse), unit_vector)
   z = np.matmul(np.matmul(unit_vector.transpose(), sig_inverse), mu_hat)

   # print statements for debug
   # print("x = ", x)
   # print("y = ", y)
   # print("z = ", z)

   denom = x * y - (z ** 2)

   # Computes numerical coefficients in efficient-frontier equation
   a = (np.matmul(np.matmul(unit_vector.transpose(), sig_inverse), unit_vector)) / denom
   b = 2 * (np.matmul(np.matmul(unit_vector.transpose(), sig_inverse), mu_hat)) / denom
   c = (np.matmul(np.matmul(mu_hat.transpose(), sig_inverse), mu_hat)) / denom

   return a, b, c, ymax