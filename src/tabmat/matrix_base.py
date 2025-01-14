from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple, Union

import numpy as np


class MatrixBase(ABC):
    """Base class for all matrix classes. ``MatrixBase`` cannot be instantiated."""

    ndim = 2
    shape: Tuple[int, int]
    dtype: np.dtype

    @abstractmethod
    def matvec(self, other, cols: np.ndarray = None, out: np.ndarray = None):
        """
        Perform: self[:, cols] @ other, so result[i] = sum_j self[i, j] other[j].

        The 'cols' parameter allows restricting to a subset of the matrix without making
        a copy. If provided:

        ::

            result[i] = sum_{j in cols} self[i, j] other[j].

        If 'out' is provided, we modify 'out' in place by adding the output of this
        operation to it.
        """
        pass

    @abstractmethod
    def transpose_matvec(
        self,
        vec: Union[np.ndarray, List],
        rows: np.ndarray = None,
        cols: np.ndarray = None,
        out: np.ndarray = None,
    ) -> np.ndarray:
        """
        Perform: self[rows, cols].T @ vec, so result[i] = sum_j self[j, i] vec[j].

        The rows and cols parameters allow restricting to a subset of the
        matrix without making a copy.

        If 'rows' and 'cols' are provided:

        ::

            result[i] = sum_{j in rows} self[j, cols[i]] vec[j].

        Note that the length of the output is len(cols).

        If ``out`` is provided:

        ::

            out[cols[i]] += sum_{j in rows} self[j, cols[i]] vec[j]

        """
        pass

    @abstractmethod
    def sandwich(
        self, d: np.ndarray, rows: np.ndarray = None, cols: np.ndarray = None
    ) -> np.ndarray:
        """
        Perform a sandwich product: (self[rows, cols].T * d[rows]) @ self[rows, cols].

        The rows and cols parameters allow restricting to a subset of the
        matrix without making a copy.
        """
        pass

    def __matmul__(self, other):
        """Define the behavior of 'self @ other'."""
        return self.matvec(other)

    @abstractmethod
    def getcol(self, i: int):  # noqa D102
        pass

    @property
    def A(self) -> np.ndarray:
        """Convert self into an np.ndarray. Synonym for ``toarray()``."""
        return self.toarray()

    @abstractmethod
    def toarray(self) -> np.ndarray:  # noqa D102
        """Convert self into an np.ndarray."""
        pass

    def __rmatmul__(self, other: Union[np.ndarray, List]) -> np.ndarray:
        """
        Perform other @ X = (X.T @ other.T).T = X.transpose_matvec(other.T).T.

        Parameters
        ----------
        other: array-like

        Returns
        -------
        array

        """
        if not hasattr(other, "T"):
            other = np.asarray(other)
        return self.transpose_matvec(other.T).T  # type: ignore

    @abstractmethod
    def astype(self, dtype, order="K", casting="unsafe", copy=True):  # noqa D102
        pass

    def _get_col_means(self, weights: np.ndarray) -> np.ndarray:
        """Get means of columns."""
        return self.transpose_matvec(weights)

    @abstractmethod
    def _get_col_stds(  # noqa D102
        self, weights: np.ndarray, col_means: np.ndarray
    ) -> np.ndarray:
        pass

    def standardize(
        self, weights: np.ndarray, center_predictors: bool, scale_predictors: bool
    ) -> Tuple[Any, np.ndarray, Optional[np.ndarray]]:
        """
        Return a StandardizedMatrix along with the column means and column standard deviations.

        It is often useful to modify a dataset so that each column has mean
        zero and standard deviation one. This function does this "standardization"
        without modifying the underlying dataset by storing shifting and scaling
        factors that are then used whenever an operation is performed with the new
        StandardizedMatrix.

        Note: If center_predictors is False, col_means will be zeros.

        Note: If scale_predictors is False, col_stds will be None.
        """
        from .standardized_mat import StandardizedMatrix

        col_means = self._get_col_means(weights)
        if scale_predictors:
            col_stds = self._get_col_stds(weights, col_means)
            mult = _one_over_var_inf_to_val(col_stds, 1.0)
            if center_predictors:
                shifter = -col_means * mult
                out_means = col_means
            else:
                shifter = np.zeros_like(col_means)
                out_means = shifter
        else:
            col_stds = None
            if center_predictors:
                shifter = -col_means
                out_means = col_means
            else:
                shifter = np.zeros_like(col_means)
                out_means = shifter
            mult = None

        return StandardizedMatrix(self, shifter, mult), out_means, col_stds

    @abstractmethod
    def __getitem__(self, item):
        pass

    # Higher priority than numpy arrays, so behavior for funcs like "@" defaults to the
    # behavior of this class
    __array_priority__ = 11


def _one_over_var_inf_to_val(arr: np.ndarray, val: float) -> np.ndarray:
    """
    Return 1/arr unless the values are zeros.

    If values are zeros, return val.
    """
    zeros = np.where(np.abs(arr) < 1e-7)
    with np.errstate(divide="ignore"):
        one_over = 1 / arr
    one_over[zeros] = val
    return one_over
