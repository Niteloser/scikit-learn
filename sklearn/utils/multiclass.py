# Author: Arnaud Joly, Joel Nothman
#
# License: BSD 3 clause
"""
Multi-class / multi-label utility function
==========================================

"""
from collections import Sequence
from itertools import chain

import numpy as np

from ..externals.six import string_types


def _unique_multiclass(y):
    if isinstance(y, np.ndarray):
        return np.unique(y)
    else:
        return set(y)


def _unique_sequence_of_sequence(y):
    return set(chain.from_iterable(y))


def _unique_indicator(y):
    return np.arange(y.shape[1])


_FN_UNIQUE_LABELS = {
    'binary': _unique_multiclass,
    'multiclass': _unique_multiclass,
    'multilabel-sequences': _unique_sequence_of_sequence,
    'multilabel-indicator': _unique_indicator,
}


def unique_labels(*ys):
    """Extract an ordered array of unique labels

    We don't allow:
        - mix of multilabel and multiclass (single label) targets
        - mix of label indicator matrix and anything else,
          because there are no explicit labels)
        - mix of label indicator matrices of different sizes
        - mix of string and integer labels

    At the moment, we also don't allow "mutliclass-multioutput" input type.

    Parameters
    ----------
    ys : array-likes,

    Returns
    -------
    out : numpy array of shape [n_unique_labels]
        An ordered array of unique labels.

    Examples
    --------
    >>> from sklearn.utils.multiclass import unique_labels
    >>> unique_labels([3, 5, 5, 5, 7, 7])
    array([3, 5, 7])
    >>> unique_labels([1, 2, 3, 4], [2, 2, 3, 4])
    array([1, 2, 3, 4])
    >>> unique_labels([1, 2, 10], [5, 11])
    array([ 1,  2,  5, 10, 11])
    >>> unique_labels(np.array([[0.0, 1.0], [1.0, 1.0]]), np.zeros((2, 2)))
    array([0, 1])
    >>> unique_labels([(1, 2), (3,)], [(1, 2), tuple()])
    array([1, 2, 3])

    """
    if not ys:
        raise ValueError('No argument has been passed.')

    # Check that we don't mix label format
    ys_types = set(type_of_target(x) for x in ys)
    if ys_types == set(["binary", "multiclass"]):
        ys_types = set(["multiclass"])

    if len(ys_types) > 1:
        raise ValueError("Mix type of y not allowed, got types %s" % ys_types)

    label_type = ys_types.pop()

    # Check consistency for the indicator format
    if (label_type == "multilabel-indicator" and
            len(set(y.shape[1] for y in ys)) > 1):
        raise ValueError("Multi-label binary indicator input with "
                         "different numbers of labels")

    # Get the unique set of labels
    _unique_labels = _FN_UNIQUE_LABELS.get(label_type, None)
    if not _unique_labels:
        raise ValueError("Unknown label type")

    ys_labels = set(chain.from_iterable(_unique_labels(y) for y in ys))

    # Check that we don't mix string type with number type
    if (len(set(isinstance(label, string_types) for label in ys_labels)) > 1):
        raise ValueError("Mix of label input types (string and number)")

    return np.array(sorted(ys_labels))


def _is_integral_float(y):
    return y.dtype.kind == 'f' and np.all(y.astype(int) == y)


def is_label_indicator_matrix(y):
    """ Check if ``y`` is in the label indicator matrix format (multilabel).

    Parameters
    ----------
    y : numpy array of shape [n_samples] or sequence of sequences
        Target values. In the multilabel case the nested sequences can
        have variable lengths.

    Returns
    -------
    out : bool,
        Return ``True``, if ``y`` is in a label indicator matrix format,
        else ``False``.

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.utils.multiclass import is_label_indicator_matrix
    >>> is_label_indicator_matrix([0, 1, 0, 1])
    False
    >>> is_label_indicator_matrix([[1], [0, 2], []])
    False
    >>> is_label_indicator_matrix(np.array([[1, 0], [0, 0]]))
    True
    >>> is_label_indicator_matrix(np.array([[1], [0], [0]]))
    False
    >>> is_label_indicator_matrix(np.array([[1, 0, 0]]))
    True

    """
    if not (hasattr(y, "shape") and y.ndim == 2 and y.shape[1] > 1):
        return False
    labels = np.unique(y)
    return len(labels) <= 2 and (y.dtype.kind in 'biu'  # bool, int, uint
                                 or _is_integral_float(labels))


def is_sequence_of_sequences(y):
    """ Check if ``y`` is in the sequence of sequences format (multilabel).

    Parameters
    ----------
    y : sequence or array.

    Returns
    -------
    out : bool,
        Return ``True``, if ``y`` is a sequence of sequences else ``False``.

    >>> import numpy as np
    >>> from sklearn.utils.multiclass import is_multilabel
    >>> is_sequence_of_sequences([0, 1, 0, 1])
    False
    >>> is_sequence_of_sequences([[1], [0, 2], []])
    True
    >>> is_sequence_of_sequences(np.array([[1], [0, 2], []], dtype=object))
    True
    >>> is_sequence_of_sequences([(1,), (0, 2), ()])
    True
    >>> is_sequence_of_sequences(np.array([[1, 0], [0, 0]]))
    False
    >>> is_sequence_of_sequences(np.array([[1], [0], [0]]))
    False
    >>> is_sequence_of_sequences(np.array([[1, 0, 0]]))
    False
    """
    # the explicit check for ndarray is for forward compatibility; future
    # versions of Numpy might want to register ndarray as a Sequence
    try:
        return (not isinstance(y[0], np.ndarray) and isinstance(y[0], Sequence)
                and not isinstance(y[0], string_types))
    except IndexError:
        return False


def is_multilabel(y):
    """ Check if ``y`` is in a multilabel format.

    Parameters
    ----------
    y : numpy array of shape [n_samples] or sequence of sequences
        Target values. In the multilabel case the nested sequences can
        have variable lengths.

    Returns
    -------
    out : bool,
        Return ``True``, if ``y`` is in a multilabel format, else ```False``.

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.utils.multiclass import is_multilabel
    >>> is_multilabel([0, 1, 0, 1])
    False
    >>> is_multilabel([[1], [0, 2], []])
    True
    >>> is_multilabel(np.array([[1, 0], [0, 0]]))
    True
    >>> is_multilabel(np.array([[1], [0], [0]]))
    False
    >>> is_multilabel(np.array([[1, 0, 0]]))
    True

    """
    return is_label_indicator_matrix(y) or is_sequence_of_sequences(y)


def type_of_target(y):
    """Determine the type of data indicated by target `y`

    Parameters
    ----------
    y : array-like

    Returns
    -------
    target_type : string
        One of:
        * 'continuous': `y` is an array-like of floats that are not all
          integers, and is 1d or a column vector.
        * 'continuous-multioutput': `y` is a 2d array of floats that are
          not all integers, and both dimensions are of size > 1.
        * 'binary': `y` contains <= 2 discrete values and is 1d or a column
          vector.
        * 'multiclass': `y` contains more than two discrete values, is not a
          sequence of sequences, and is 1d or a column vector.
        * 'mutliclass-multioutput': `y` is a 2d array that contains more
          than two discrete values, is not a sequence of sequences, and both
          dimensions are of size > 1.
        * 'multilabel-sequences': `y` is a sequence of sequences, a 1d
          array-like of objects that are sequences of labels.
        * 'multilabel-indicator': `y` is a label indicator matrix, an array
          of two dimensions with at least two columns, and at most 2 unique
          values.
        * 'unknown': `y` is array-like but none of the above, such as a 3d
          array, or an array of non-sequence objects.

    Examples
    --------
    >>> import numpy as np
    >>> type_of_target([0.1, 0.6])
    'continuous'
    >>> type_of_target([1, -1, -1, 1])
    'binary'
    >>> type_of_target(['a', 'b', 'a'])
    'binary'
    >>> type_of_target([1, 0, 2])
    'multiclass'
    >>> type_of_target(['a', 'b', 'c'])
    'multiclass'
    >>> type_of_target(np.array([[1, 2], [3, 1]]))
    'multiclass-multioutput'
    >>> type_of_target(np.array([[1.5, 2.0], [3.0, 1.6]]))
    'continuous-multioutput'
    >>> type_of_target([['a', 'b'], ['c'], []])
    'multilabel-sequences'
    >>> type_of_target([[]])
    'multilabel-sequences'
    >>> type_of_target(np.array([[0, 1], [1, 1]]))
    'multilabel-indicator'
    """
    # XXX: is there a way to duck-type this condition?
    valid = (isinstance(y, (np.ndarray, Sequence))
             and not isinstance(y, string_types))
    if not valid:
        raise ValueError('Expected array-like (array or non-string sequence), '
                         'got %r' % y)

    if is_sequence_of_sequences(y):
        return 'multilabel-sequences'
    elif is_label_indicator_matrix(y):
        return 'multilabel-indicator'

    try:
        y = np.asarray(y)
    except ValueError:
        # known to fail in numpy 1.3 for array of arrays
        return 'unknown'
    if y.ndim > 2 or y.dtype == object:
        return 'unknown'
    if y.ndim == 2 and y.shape[1] == 0:
        return 'unknown'
    elif y.ndim == 2 and y.shape[1] > 1:
        suffix = '-multioutput'
    else:
        # column vector or 1d
        suffix = ''

    # check float and contains non-integer float values:
    if y.dtype.kind == 'f' and np.any(y != y.astype(int)):
        return 'continuous' + suffix
    if len(np.unique(y)) <= 2:
        assert not suffix, "2d binary array-like should be multilabel"
        return 'binary'
    else:
        return 'multiclass' + suffix
