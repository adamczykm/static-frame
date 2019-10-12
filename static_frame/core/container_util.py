'''
This module us for utilty functions that take as input and / or return Container subclasses such as Index, Series, or Frame, and that need to be shared by multiple such Container classes.
'''

import numpy as np
import typing as tp

if tp.TYPE_CHECKING:
    from static_frame.core.series import Series #pylint: disable=W0611
    from static_frame.core.frame import Frame #pylint: disable=W0611

from static_frame.core.util import IndexConstructor
from static_frame.core.util import IndexInitializer
from static_frame.core.util import STATIC_ATTR
from static_frame.core.util import AnyCallable
from static_frame.core.util import NULL_SLICE

from static_frame.core.index_base import IndexBase


def is_static(value: IndexConstructor) -> bool:
    try:
        # if this is a class constructor
        return getattr(value, STATIC_ATTR)
    except AttributeError:
        pass
    # assume this is a class method
    return getattr(value.__self__, STATIC_ATTR)


def index_from_optional_constructor(
        value: IndexInitializer,
        *,
        default_constructor: IndexConstructor,
        explicit_constructor: tp.Optional[IndexConstructor] = None,
        ) -> IndexBase:
    '''
    Given a value that is an IndexInitializer (which means it might be an Index), determine if that value is really an Index, and if so, determine if a copy has to be made; otherwise, use the default_constructor. If an explicit_constructor is given, that is always used.
    '''
    # NOTE: this might return an own_index flag to show callers when a new index has been created

    if explicit_constructor:
        return explicit_constructor(value)

    # default constructor could be a function with a STATIC attribute
    if isinstance(value, IndexBase):
        # if default is STATIC, and value is not STATIC, get an immutabel
        if is_static(default_constructor): # type: ignore
            if not value.STATIC:
                # v: ~S, dc: S, use immutable alternative
                return value._IMMUTABLE_CONSTRUCTOR(value)
            # v: S, dc: S, both immutable
            return value
        else: # default constructor is mutable
            if not value.STATIC:
                # v: ~S, dc: ~S, both are mutable
                return value.copy()
            # v: S, dc: ~S, return a mutable version of something that is not mutable
            return default_constructor(value)

    # cannot always deterine satic status from constructors; fallback on using default constructor
    return default_constructor(value)



# matmul of two series reduces to a single value

def matmul(
        lhs: tp.Union['Series', 'Frame', tp.Iterable],
        rhs: tp.Union['Series', 'Frame', tp.Iterable],
        ) -> tp.Any: #tp.Union['Series', 'Frame']:
    '''
    Implementation of matrix multiplication for Series and Frame
    '''
    from static_frame.core.series import Series
    from static_frame.core.frame import Frame

    # for a @ b = c
    # if a is 2D: a.columns must align b.index
    # if b is 1D, a.columns bust align with b.index
    # if a is 1D: len(a) == b.index (len of b), returns w columns of B

    if not isinstance(rhs, (np.ndarray, Series, Frame)):
        # try to make it into an array
        rhs = np.array(rhs)

    if not isinstance(lhs, (np.ndarray, Series, Frame)):
        # try to make it into an array
        lhs = np.array(lhs)

    if isinstance(lhs, np.ndarray):
        lhs_type = np.ndarray
    elif isinstance(lhs, Series):
        lhs_type = Series
    else: # normalize subclasses
        lhs_type = Frame

    if isinstance(rhs, np.ndarray):
        rhs_type = np.ndarray
    elif isinstance(rhs, Series):
        rhs_type = Series
    else: # normalize subclasses
        rhs_type = Frame

    if rhs_type == np.ndarray and lhs_type == np.ndarray:
        return np.matmul(lhs, rhs)


    own_index = True
    constructor = None

    if lhs.ndim == 1: # Series, 1D array
        # result will be 1D or 0D
        columns = None

        if lhs_type == Series and (rhs_type == Series or rhs_type == Frame):
            aligned = lhs._index.union(rhs._index)
            # if the aligned shape is not the same size as the originals, we do not have the same values in each and cannot proceed (all values go to NaN)
            if len(aligned) != len(lhs._index) or len(aligned) != len(rhs._index):
                raise RuntimeError('shapes not alignable for matrix multiplication')

        if lhs_type == Series:
            if rhs_type == np.ndarray:
                if lhs.shape[0] != rhs.shape[0]: # works for 1D and 2D
                    raise RuntimeError('shapes not alignable for matrix multiplication')
                ndim = rhs.ndim - 1 # if 2D, result is 1D, of 1D, result is 0
                left = lhs.values
                right = rhs # already np
                if ndim == 1:
                    index = None # force auto increment integer
                    own_index = False
                    constructor = lhs.__class__
                # else:
                #     index = lhs.index
            elif rhs_type == Series:
                ndim = 0
                left = lhs.reindex(aligned).values
                right = rhs.reindex(aligned).values
                # index = aligned
            else: # rhs is Frame
                ndim = 1
                left = lhs.reindex(aligned).values
                right = rhs.reindex(index=aligned).values
                index = rhs._columns
                constructor = lhs.__class__
        else: # lhs is 1D array
            left = lhs
            right = rhs.values
            if rhs_type == Series:
                ndim = 0
            else: # rhs is Frame, len(lhs) == len(rhs.index)
                ndim = 1
                index = rhs._columns
                constructor = Series # cannot get from argument

    elif lhs.ndim == 2: # Frame, 2D array

        if lhs_type == Frame and (rhs_type == Series or rhs_type == Frame):
            aligned = lhs._columns.union(rhs._index)
            # if the aligned shape is not the same size as the originals, we do not have the same values in each and cannot proceed (all values go to NaN)
            if len(aligned) != len(lhs._columns) or len(aligned) != len(rhs._index):
                raise RuntimeError('shapes not alignable for matrix multiplication')

        if lhs_type == Frame:
            if rhs_type == np.ndarray:
                if lhs.shape[1] != rhs.shape[0]: # works for 1D and 2D
                    raise RuntimeError('shapes not alignable for matrix multiplication')
                ndim = rhs.ndim
                left = lhs.values
                right = rhs # already np
                index = lhs._index

                if ndim == 1:
                    constructor = Series
                else:
                    constructor = lhs.__class__
                    columns = None # force auto increment index
            elif rhs_type == Series:
                # a.columns must align with b.index
                ndim = 1
                left = lhs.reindex(columns=aligned).values
                right = rhs.reindex(aligned).values
                index = lhs._index  # this axis is not changed
                constructor = rhs.__class__
            else: # rhs is Frame
                # a.columns must align with b.index
                ndim = 2
                left = lhs.reindex(columns=aligned).values
                right = rhs.reindex(index=aligned).values
                index = lhs._index
                columns = rhs._columns
                constructor = lhs.__class__ # give left precedence
        else: # lhs is 2D array
            left = lhs
            right = rhs.values
            if rhs_type == Series: # returns unindexed Series
                ndim = 1
                index = None
                own_index = False
                constructor = rhs.__class__
            else: # rhs is Frame, lhs.shape[1] == rhs.shape[0]
                if lhs.shape[1] != rhs.shape[0]: # works for 1D and 2D
                    raise RuntimeError('shapes not alignable for matrix multiplication')
                ndim = 2
                index = None
                own_index = False
                columns = rhs._columns
                constructor = rhs.__class__

    # import ipdb; ipdb.set_trace()

    # NOTE: np.matmul is not the same as np.dot for some arguments
    data = np.matmul(left, right)
    # import ipdb; ipdb.set_trace()

    if ndim == 0:
        return data

    data.flags.writeable = False
    if ndim == 1:
        return constructor(data,
                index=index,
                own_index=own_index,
                )
    return constructor(data,
            index=index,
            own_index=own_index,
            columns=columns
            )




def axis_window_items( *,
        source: tp.Union['Series', 'Frame'],
        axis: int = 0,
        size: int = 2,
        step: int = 1,
        window_sized: bool = True,
        window_func: tp.Optional[AnyCallable] = None,
        window_valid: tp.Optional[AnyCallable] = None,
        label_shift: int = 0,
        start_shift: int = 0,
        size_increment: int = 0,
        window_array: bool = False,
        ) -> tp.Iterator[tp.Tuple[tp.Hashable, tp.Any]]:
    '''Generator of index, window pairs pairs.

    Args:
        size: integer greater than 0
        step: integer greater than 0 to determine the step size between windows. A step of 1 shifts the window 1 data point; a step equal to window size results in non-overlapping windows.
        window_sized: if True, windows that do not meet the size are skipped.
        window_func: Array processor of window values, pre-function application; useful for applying weighting to the window.
        window_valid: Function that, given an array window, returns True if the window meets requirements and should be returned.
        label_shift: shift, relative to the right-most data point contained in the window, to derive the label paired with the window; e.g., o return the first label of the window, the shift will be the size minus one.
        start_shift: shift from 0 to determine where the collection of windows begins.
        size_increment: value to be added to each window aftert the first, so as to, in combination with setting the step size to 0, permit expanding windows.
        window_array: if True, the window is returned as an array instead of a SF object.
    '''
    if size <= 0:
        raise RuntimeError('window size must be greater than 0')
    if step < 0:
        raise RuntimeError('window step cannot be less than than 0')

    source_ndim = source.ndim

    if source_ndim == 1:
        labels = source._index
        if window_array:
            values = source.values
    else:
        labels = source._index if axis == 0 else source._columns
        if window_array:
            values = source._blocks.values

    count_window_max = len(labels)
    idx_left_max = count_window_max - 1

    idx_left = start_shift
    count = 0

    while True:
        idx_right = idx_left + size - 1

        # floor idx_left at 0
        key = slice(max(idx_left, 0), idx_right + 1)

        if source_ndim == 1:
            if window_array:
                window = values[key]
            else:
                window = source._extract_iloc(key)
        else:
            if axis == 0:
                if window_array:
                    window = values[key]
                else: # use low level iloc selector
                    window = source._extract(row_key=key)
            else:
                if window_array:
                    window = values[NULL_SLICE, key]
                else:
                    window = source._extract(column_key=key)

        valid = True
        try:
            idx_label = idx_right + label_shift
            if idx_label < 0: # do not wrap around
                raise IndexError()
            label = labels.iloc[idx_label]
        except IndexError: # an invalid label has to be dropped
            valid = False

        if valid and window_sized and window.shape[axis] != size:
            valid = False
        if valid and window_valid and not window_valid(window):
            valid = False

        if valid:
            if window_func:
                window = window_func(window)
            yield label, window

        idx_left += step
        size += size_increment
        count += 1

        if count > count_window_max or idx_left > idx_left_max:
            break
