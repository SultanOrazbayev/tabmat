from typing import Tuple

import numpy as np
from scipy import sparse as sps
from sparse_dot_mkl import dot_product_mkl

from glm_benchmarks.sandwich.sandwich import sparse_sandwich


class MKLSparseMatrix(sps.csc_matrix):
    """
    A scipy.sparse csc matrix subclass that will use MKL for sparse
    matrix-vector products and will use the fast sparse_sandwich function
    for sandwich products.
    """

    def __init__(self, arg1, shape=None, dtype=None, copy=False):
        """
        Instantiate in the same way as scipy.sparse.csc_matrix
        """
        super().__init__(arg1, shape, dtype, copy)
        self.x_csr = None

    def to_scipy_sparse(self, copy: bool) -> sps.csc_matrix:
        return sps.csc_matrix(self, copy=copy)

    def sandwich(self, d: np.ndarray) -> np.ndarray:
        if self.x_csr is None:
            self.x_csr = self.tocsr(copy=False)

        return sparse_sandwich(self.tocsc(copy=False), self.x_csr, d)

    def dot(self, v):
        if len(v.shape) == 1:
            return dot_product_mkl(self, v)
        if len(v.shape) == 2 and v.shape[1] == 1:
            return dot_product_mkl(self, np.squeeze(v))[:, None]
        return sps.csc_matrix.dot(self, v)

    def __rmatmul__(self, v):
        if len(v.shape) == 1:
            return dot_product_mkl(self.T, v)
        if len(v.shape) == 2 and v.shape[0] == 1:
            return dot_product_mkl(self.T, np.squeeze(v))[None, :]
        return sps.csc_matrix.__rmatmul__(self, v)

    __array_priority__ = 12

    def standardize(self, weights, scale_predictors) -> Tuple:
        from glm_benchmarks.scaled_spmat.standardize import standardize, zero_center

        if scale_predictors:
            return standardize(self, weights=weights)
        else:
            X, col_means = zero_center(self, weights=weights)
            col_stds = np.ones(self.shape[1])
            return X, col_means, col_stds