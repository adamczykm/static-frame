import sys
import typing as tp
import os
import operator
import struct

from collections import abc
from collections import defaultdict

from itertools import chain
from io import StringIO
from io import BytesIO
import datetime
from urllib import request
import tempfile
from functools import reduce
from itertools import zip_longest

import numpy as np  # type: ignore


if tp.TYPE_CHECKING:

    from static_frame.core.index_base import IndexBase
    from static_frame.core.index import Index
    from static_frame.core.series import Series
    from static_frame.core.frame import Frame
    from static_frame.core.frame import FrameAsType
    from static_frame.core.type_blocks import TypeBlocks


# dtype.kind
#     A character code (one of ‘biufcmMOSUV’) identifying the general kind of data.
#     b 	boolean
#     i 	signed integer
#     u 	unsigned integer
#     f 	floating-point
#     c 	complex floating-point
#     m 	timedelta
#     M 	datetime
#     O 	object
#     S 	(byte-)string
#     U 	Unicode
#     V 	void

# https://docs.scipy.org/doc/numpy-1.10.1/reference/arrays.scalars.html


DEFAULT_SORT_KIND = 'mergesort'

DEFAULT_INT_DTYPE = np.int64 # default for SF construction

# ARCHITECTURE_SIZE = struct.calcsize('P') * 8 # size of pointer
# ARCHITECTURE_INT_DTYPE = np.int64 if ARCHITECTURE_SIZE == 64 else np.int32

DEFAULT_STABLE_SORT_KIND = 'mergesort'
DTYPE_STR_KIND = ('U', 'S') # S is np.bytes_
DTYPE_INT_KIND = ('i', 'u') # signed and unsigned
DTYPE_NAN_KIND = ('f', 'c') # kinds taht support NaN values
DTYPE_DATETIME_KIND = 'M'
DTYPE_TIMEDELTA_KIND = 'm'
DTYPE_NAT_KIND = ('M', 'm')

DTYPE_OBJECT = np.dtype(object)
DTYPE_BOOL = np.dtype(bool)

NULL_SLICE = slice(None)
UNIT_SLICE = slice(0, 1)
SLICE_START_ATTR = 'start'
SLICE_STOP_ATTR = 'stop'
SLICE_STEP_ATTR = 'step'
SLICE_ATTRS = (SLICE_START_ATTR, SLICE_STOP_ATTR, SLICE_STEP_ATTR)

STATIC_ATTR = 'STATIC'

EMPTY_TUPLE = ()

# defaults to float64
EMPTY_ARRAY = np.array(EMPTY_TUPLE, dtype=None)
EMPTY_ARRAY.flags.writeable = False

EMPTY_ARRAY_BOOL = np.array(EMPTY_TUPLE, dtype=DTYPE_BOOL)
EMPTY_ARRAY_BOOL.flags.writeable = False

EMPTY_ARRAY_INT = np.array(EMPTY_TUPLE, dtype=DEFAULT_INT_DTYPE)
EMPTY_ARRAY_INT.flags.writeable = False

NAT = np.datetime64('nat')
# define missing for timedelta as an untyped 0
EMPTY_TIMEDELTA = np.timedelta64(0)

# _DICT_STABLE = sys.version_info >= (3, 6)

# map from datetime.timedelta attrs to np.timedelta64 codes
TIME_DELTA_ATTR_MAP = (
        ('days', 'D'),
        ('seconds', 's'),
        ('microseconds', 'us')
        )

# ufunc functions that will not work with DTYPE_STR_KIND, but do work if converted to object arrays; see UFUNC_AXIS_SKIPNA for the matching functions
UFUNC_AXIS_STR_TO_OBJ = {np.min, np.max, np.sum}

#-------------------------------------------------------------------------------
# utility type groups

INT_TYPES = (int, np.integer) # np.integer catches all np int types

BOOL_TYPES = (bool, np.bool_)

DICTLIKE_TYPES = (abc.Set, dict)

# iterables that cannot be used in NP array constructors; asumes that dictlike types have already been identified
INVALID_ITERABLE_FOR_ARRAY = (abc.ValuesView, abc.KeysView)
NON_STR_TYPES = {int, float, bool}


# for getitem / loc selection
KEY_ITERABLE_TYPES = (list, np.ndarray)

# types of keys that return muultiple items, even if the selection reduces to 1
KEY_MULTIPLE_TYPES = (slice, list, np.ndarray)

# for type hinting
# keys once dimension has been isolated
GetItemKeyType = tp.Union[
        int, np.integer, slice, tp.List[tp.Any], None, 'Index', 'Series', np.ndarray]

# keys that might include a multiple dimensions speciation; tuple is used to identify compound extraction
GetItemKeyTypeCompound = tp.Union[
        tp.Tuple[tp.Any, ...], int, np.integer, slice, tp.List[tp.Any], None, 'Index', 'Series', np.ndarray]

UFunc = tp.Callable[..., np.ndarray]
AnyCallable = tp.Callable[..., tp.Any]

CallableOrMapping = tp.Union[AnyCallable, tp.Mapping[tp.Hashable, tp.Any], 'Series']
KeyOrKeys = tp.Union[tp.Hashable, tp.Iterable[tp.Hashable]]
FilePathOrFileLike = tp.Union[str, tp.TextIO]

DtypeSpecifier = tp.Optional[tp.Union[str, np.dtype, type]]

# support an iterable of specifiers, or mapping based on column names
DtypesSpecifier = tp.Optional[
        tp.Union[tp.Iterable[DtypeSpecifier], tp.Dict[tp.Hashable, DtypeSpecifier]]]

# specifiers that are equivalent to object
DTYPE_SPECIFIERS_OBJECT = {DTYPE_OBJECT, object, tuple}

DepthLevelSpecifier = tp.Union[int, tp.Iterable[int]]

CallableToIterType = tp.Callable[[], tp.Iterable[tp.Any]]

IndexSpecifier = tp.Union[int, str]
IndexInitializer = tp.Union[
        'IndexBase',
        tp.Iterable[tp.Hashable],
        tp.Generator[tp.Hashable, None, None]]
IndexConstructor = tp.Callable[[IndexInitializer], 'IndexBase']

# take integers for size; otherwise, extract size from any other index initializer
IndexAutoInitializer = int

SeriesInitializer = tp.Union[
        tp.Iterable[tp.Any],
        np.ndarray,
        tp.Mapping[tp.Hashable, tp.Any],
        int, float, str, bool]

# support single items, or numpy arrays, or values that can be made into a 2D array
FrameInitializer = tp.Union[
        tp.Iterable[tp.Iterable[tp.Any]],
        np.ndarray,
        ]

FRAME_INITIALIZER_DEFAULT = object()

DateInitializer = tp.Union[str, datetime.date, np.datetime64]
YearMonthInitializer = tp.Union[str, datetime.date, np.datetime64]
YearInitializer = tp.Union[str, datetime.date, np.datetime64]


#-------------------------------------------------------------------------------

def mloc(array: np.ndarray) -> int:
    '''Return the memory location of an array.
    '''
    return tp.cast(int, array.__array_interface__['data'][0])


def immutable_filter(src_array: np.ndarray) -> np.ndarray:
    '''Pass an immutable array; otherwise, return an immutable copy of the provided array.
    '''
    if src_array.flags.writeable:
        dst_array = src_array.copy()
        dst_array.flags.writeable = False
        return dst_array
    return src_array # keep it as is

def name_filter(name: tp.Hashable) -> tp.Hashable:
    '''
    For name attributes on containers, only permit recursively hashable objects.
    '''
    try:
        hash(name)
    except TypeError:
        raise TypeError('unhashable name attribute', name)
    return name

def shape_filter(array: np.ndarray) -> tp.Tuple[int, int]:
    '''Reprsent a 1D array as a 2D array with length as rows of a single-column array.

    Return:
        row, column count for a block of ndim 1 or ndim 2.
    '''
    if array.ndim == 1:
        return array.shape[0], 1
    return tp.cast(tp.Tuple[int, int], array.shape)

def column_2d_filter(array: np.ndarray) -> np.ndarray:
    '''Reshape a flat ndim 1 array into a 2D array with one columns and rows of length. This is used (a) for getting string representations and (b) for using np.concatenate and np binary operators on 1D arrays.
    '''
    # it is not clear when reshape is a copy or a view
    if array.ndim == 1:
        return np.reshape(array, (array.shape[0], 1))
    return array

def column_1d_filter(array: np.ndarray) -> np.ndarray:
    '''
    Ensure that a column that might be 2D or 1D is returned as a 1D array.
    '''
    if array.ndim == 2:
        # could assert that array.shape[1] == 1, but this will raise if does not fit
        return np.reshape(array, array.shape[0])
    return array

def _gen_skip_middle(
        forward_iter: CallableToIterType,
        forward_count: int,
        reverse_iter: CallableToIterType,
        reverse_count: int,
        center_sentinel: tp.Any) -> tp.Iterator[tp.Any]:
    '''
    Provide a generator to yield the count values from each side.
    '''
    assert forward_count > 0 and reverse_count > 0
    # for the forward gen, we take one more column to serve as the center column ellipsis; thus, we start enumeration at 0
    for idx, value in enumerate(forward_iter(), start=1):
        yield value
        if idx == forward_count:
            break
    # center sentinel
    yield center_sentinel

    values = []
    for idx, col in enumerate(reverse_iter(), start=1):
        values.append(col)
        if idx == reverse_count:
            break
    yield from reversed(values)


def resolve_dtype(dt1: np.dtype, dt2: np.dtype) -> np.dtype:
    '''
    Given two dtypes, return a compatible dtype that can hold both contents without truncation.
    '''
    # NOTE: np.dtype(object) == np.object_, so we can return np.object_
    # if the same, return that detype
    if dt1 == dt2:
        return dt1

    # if either is object, we go to object
    if dt1.kind == 'O' or dt2.kind == 'O':
        return DTYPE_OBJECT

    dt1_is_str = dt1.kind in DTYPE_STR_KIND
    dt2_is_str = dt2.kind in DTYPE_STR_KIND
    if dt1_is_str and dt2_is_str:
        # if both are string or string-like, we can use result type to get the longest string
        return np.result_type(dt1, dt2)

    dt1_is_dt = dt1.kind == DTYPE_DATETIME_KIND
    dt2_is_dt = dt2.kind == DTYPE_DATETIME_KIND
    if dt1_is_dt and dt2_is_dt:
        # if both are datetime, result type will work
        return np.result_type(dt1, dt2)

    dt1_is_tdelta = dt1.kind == DTYPE_TIMEDELTA_KIND
    dt2_is_tdelta = dt2.kind == DTYPE_TIMEDELTA_KIND
    if dt1_is_tdelta and dt2_is_tdelta:
        # this may or may not work
        # TypeError: Cannot get a common metadata divisor for NumPy datetime metadata [D] and [Y] because they have incompatible nonlinear base time units
        try:
            return np.result_type(dt1, dt2)
        except TypeError:
            return DTYPE_OBJECT

    dt1_is_bool = dt1.type is np.bool_
    dt2_is_bool = dt2.type is np.bool_

    # if any one is a string or a bool, we have to go to object; we handle both cases being the same above; result_type gives a string in mixed cases
    if (dt1_is_str or dt2_is_str
            or dt1_is_bool or dt2_is_bool
            or dt1_is_dt or dt2_is_dt
            or dt1_is_tdelta or dt2_is_tdelta
            ):
        return DTYPE_OBJECT

    # if not a string or an object, can use result type
    return np.result_type(dt1, dt2)

def resolve_dtype_iter(dtypes: tp.Iterable[np.dtype]) -> np.dtype:
    '''Given an iterable of one or more dtypes, do pairwise comparisons to determine compatible overall type. Once we get to object we can stop checking and return object.

    Args:
        dtypes: iterable of one or more dtypes.
    '''
    dtypes = iter(dtypes)
    dt_resolve = next(dtypes)

    for dt in dtypes:
        dt_resolve = resolve_dtype(dt_resolve, dt)
        if dt_resolve == DTYPE_OBJECT:
            return dt_resolve
    return dt_resolve



def concat_resolved(
        arrays: tp.Iterable[np.ndarray],
        axis: int = 0) -> np.ndarray:
    '''
    Concatenation of 2D arrays that uses resolved dtypes to avoid truncation.

    Axis 0 stacks rows (extends columns); axis 1 stacks columns (extends rows).

    No shape manipulation will happen, so it is always assumed that all dimensionalities will be common.
    '''
    #all the input array dimensions except for the concatenation axis must match exactly
    if axis is None:
        raise NotImplementedError('no handling of concatenating flattened arrays')

    # first pass to determine shape and resolvved type
    arrays_iter = iter(arrays)
    first = next(arrays_iter)

    ndim = first.ndim
    dt_resolve = first.dtype
    shape = list(first.shape)

    for array in arrays_iter:
        if dt_resolve != DTYPE_OBJECT:
            dt_resolve = resolve_dtype(array.dtype, dt_resolve)
        shape[axis] += array.shape[axis]

    out = np.empty(shape=shape, dtype=dt_resolve)
    np.concatenate(arrays, out=out, axis=axis)
    out.flags.writeable = False
    return out


def full_for_fill(
        dtype: np.dtype,
        shape: tp.Union[int, tp.Tuple[int, ...]],
        fill_value: object) -> np.ndarray:
    '''
    Return a "full" NP array for the given fill_value
    Args:
        dtype: target dtype, which may or may not be possible given the fill_value.
    '''
    dtype = resolve_dtype(dtype, np.array(fill_value).dtype)
    return np.full(shape, fill_value, dtype=dtype)


def dtype_to_na(dtype: DtypeSpecifier) -> tp.Any:
    '''Given a dtype, return an appropriate and compatible null value.
    '''
    if not isinstance(dtype, np.dtype):
        # we permit things like object, float, etc.
        dtype = np.dtype(dtype)

    kind = dtype.kind

    if kind in DTYPE_INT_KIND:
        return 0 # cannot support NaN
    elif kind == 'b':
        return False
    elif kind in DTYPE_NAN_KIND:
        return np.nan
    elif kind == 'O':
        return None
    elif kind in DTYPE_STR_KIND:
        return ''
    elif kind in DTYPE_DATETIME_KIND:
        return NAT
    elif kind in DTYPE_TIMEDELTA_KIND:
        return EMPTY_TIMEDELTA

    raise NotImplementedError('no support for this dtype', kind)


def ufunc_axis_skipna(*,
        array: np.ndarray,
        skipna: bool,
        axis: int,
        ufunc: UFunc,
        ufunc_skipna: UFunc,
        out: tp.Optional[np.ndarray]=None
        ) -> np.ndarray:
    '''For ufunc array application, when two ufunc versions are available. Expected to always reduce dimensionality.
    '''

    if array.dtype.kind == 'O':
        # replace None with nan
        if skipna:
            is_not_none = np.not_equal(array, None)

        if array.ndim == 1:
            if skipna:
                v = array[is_not_none]
                if len(v) == 0: # all values were None
                    return np.nan
            else:
                v = array
        else:
            # for 2D array, replace None with NaN
            if skipna:
                v = array.copy() # already an object type
                v[~is_not_none] = np.nan
            else:
                v = array

    elif array.dtype.kind == 'M' or array.dtype.kind == 'm':
        # dates do not support skipna functions
        return ufunc(array, axis=axis, out=out)

    elif array.dtype.kind in DTYPE_STR_KIND and ufunc in UFUNC_AXIS_STR_TO_OBJ:
        v = array.astype(object)
    else:
        v = array

    if skipna:
        return ufunc_skipna(v, axis=axis, out=out)
    return ufunc(v, axis=axis, out=out)


def ufunc_unique(
        array: np.ndarray,
        axis: tp.Optional[int] = None
        ) -> tp.Union[tp.FrozenSet[tp.Any], np.ndarray]:
    '''
    Extended functionality of the np.unique ufunc, to handle cases of mixed typed objects, where NP will fail in finding unique values for a hetergenous object type.
    '''
    if array.dtype.kind == 'O':
        if axis is None or array.ndim < 2:
            try:
                return np.unique(array)
            except TypeError: # if unorderable types
                pass
            # this may or may not work, depending on contained types
            if array.ndim > 1: # need to flatten
                array_iter = array.flat
            else:
                array_iter = array
            return frozenset(array_iter)

        # ndim == 2 and axis is not None
        # np.unique will give TypeError: The axis argument to unique is not supported for dtype object
        if axis == 0:
            array_iter = array
        else:
            array_iter = array.T
        return frozenset(tuple(x) for x in array_iter)
    # all other types, use the main ufunc
    return np.unique(array, axis=axis)


def roll_1d(array: np.ndarray,
            shift: int
            ) -> np.ndarray:
    '''
    Specialized form of np.roll that, by focusing on the 1D solution, is at least four times faster.
    '''
    size = len(array)
    if size <= 1:
        return array.copy()

    shift = shift % size
    if shift == 0:
        return array.copy()

    post = np.empty(size, dtype=array.dtype)
    if shift > 0:
        post[0:shift] = array[-shift:]
        post[shift:] = array[0:-shift]
        return post
    # shift is negative, negate to flip
    post[0:size+shift] = array[-shift:]
    post[size+shift:None] = array[:-shift]
    return post


def roll_2d(array: np.ndarray,
            shift: int,
            axis: int
            ) -> np.ndarray:
    '''
    Specialized form of np.roll that, by focusing on the 2D solution
    '''
    post = np.empty(array.shape, dtype=array.dtype)

    if axis == 0: # roll rows
        size = array.shape[0]
        if size <= 1:
            return array.copy()

        shift = shift % size
        if shift == 0:
            return array.copy()

        if shift > 0:
            post[0:shift, :] = array[-shift:, :]
            post[shift:, :] = array[0:-shift, :]
            return post
        # shift is negative, negate to flip
        post[0:size+shift, :] = array[-shift:, :]
        post[size+shift:None, :] = array[:-shift, :]

    elif axis == 1: # roll columns
        size = array.shape[1]
        if size <= 1:
            return array.copy()

        shift = shift % size
        if shift == 0:
            return array.copy()

        if shift > 0:
            post[:, 0:shift] = array[:, -shift:]
            post[:, shift:] = array[:, 0:-shift]
            return post
        # shift is negative, negate to flip
        post[:, 0:size+shift] = array[:, -shift:]
        post[:, size+shift:None] = array[:, :-shift]
        return post

    raise NotImplementedError()


#-------------------------------------------------------------------------------
# array constructors


def is_gen_copy_values(values: tp.Iterable[tp.Any]) -> tp.Tuple[bool, bool]:
    '''
    Returns:
        copy_values: True if values cannot be used in an np.array constructor.
    '''
    is_gen = not hasattr(values, '__len__')
    copy_values = is_gen
    if not is_gen:
        is_dictlike = isinstance(values, DICTLIKE_TYPES)
        copy_values |= is_dictlike
        if not is_dictlike:
            is_iifa = isinstance(values, INVALID_ITERABLE_FOR_ARRAY)
            copy_values |= is_iifa
    return is_gen, copy_values


def resolve_type_iter(
        values: tp.Iterable[tp.Any],
        sample_size: int = 10,
        ) -> tp.Tuple[DtypeSpecifier, bool, tp.Sequence[tp.Any]]:
    '''
    Determine an appropriate DtypeSpecifier for values in an iterable. This does not try to determine the actual dtype, but instead, if the DtypeSpecifier needs to be object rather than None (which lets NumPy auto detect).

    Args:
        values: can be a generator that will be exhausted in processing; if a generator, a copy will be made and returned as values
        sample_size: number or elements to examine to determine DtypeSpecifier.
    Returns:
        resolved, has_tuple, values
    '''

    is_gen, copy_values = is_gen_copy_values(values)

    if not is_gen:
        values = tp.cast(tp.Sequence[tp.Any], values)
        if len(values) == 0:
            return None, False, values

    v_iter = iter(values)

    if copy_values:
        # will copy in loop below; check for empty iterables and exit early
        try:
            front = next(v_iter)
        except StopIteration:
            # if no values, can return a float-type array
            return None, False, EMPTY_TUPLE

        v_iter = chain((front,), v_iter)
        # do not create list unless we are sure we have more than 1 value
        values_post = []

    resolved = None # None is valid specifier if the type is not ambiguous
    has_tuple = False
    has_str = False
    has_non_str = False

    for i, v in enumerate(v_iter, start=1):
        if copy_values:
            # if a generator, have to make a copy while iterating
            # for array construcdtion, cannot use dictlike, so must convert to list
            values_post.append(v)

        if resolved != object:

            value_type = type(v)

            if value_type == tuple:
                has_tuple = True
            elif value_type == str or value_type == np.str_:
                # must compare to both sring types
                has_str = True
            else:
                has_non_str = True

            if has_tuple or (has_str and has_non_str):
                resolved = object

        else: # resolved is object, can exit once has_tuple is known
            if has_tuple:
                # can end if we have found a tuple
                if copy_values:
                    values_post.extend(v_iter)
                break

        if i >= sample_size:
            if copy_values:
                values_post.extend(v_iter)
            break

    # NOTE: we break before finding a tuple, but our treatment of object types, downstream, will always assign them in the appropriate way
    if copy_values:
        return resolved, has_tuple, values_post

    return resolved, has_tuple, tp.cast(tp.Sequence[tp.Any], values)




def iterable_to_array(
        values: tp.Iterable[tp.Any],
        dtype: DtypeSpecifier=None
        ) -> tp.Tuple[np.ndarray, bool]:
    '''
    Convert an arbitrary Python iterable to a NumPy array without any undesirable type coercion.

    Returns:
        pair of array, Boolean, where the Boolean can be used when necessary to establish uniqueness.
    '''
    if isinstance(values, np.ndarray):
        if dtype is not None and dtype != values.dtype:
            raise RuntimeError('supplied dtype not set on supplied array')
        return values, len(values) <= 1

    # values for construct will only be a copy when necessary in iteration to find type
    if dtype is None:
        # this gives as dtype only None, or object, letting array constructor do the rest
        dtype, has_tuple, values_for_construct = resolve_type_iter(values)

        if len(values_for_construct) == 0:
            return EMPTY_ARRAY, True # no dtype given, so return empty float array

        # dtype_is_object = dtype in DTYPE_SPECIFIERS_OBJECT

    else: # dtype given, do not do full iteration
        is_gen, copy_values = is_gen_copy_values(values)

        if copy_values:
            # we have to realize into sequence for numpy creation
            values_for_construct = tuple(values)
        else:
            values_for_construct = tp.cast(tp.Sequence[tp.Any], values)

        if len(values_for_construct) == 0:
            # dtype was given, return an empty array with that dtype
            v = np.empty(0, dtype=dtype)
            v.flags.writeable = False
            return v, True

        #as we have not iterated iterable, assume that there might be tuples if the dtype is object
        has_tuple = dtype in DTYPE_SPECIFIERS_OBJECT

    if len(values_for_construct) == 1 or isinstance(values, DICTLIKE_TYPES):
        # check values for dictlike, not values_for_construct
        is_unique = True
    else:
        is_unique = False

    # construction
    if has_tuple:
        # this is the only way to assign from a sequence that contains a tuple; this does not work for dict or set (they must be copied into an iterabel), and is little slower than creating array directly
        v = np.empty(len(values_for_construct), dtype=DTYPE_OBJECT)
        v[NULL_SLICE] = values_for_construct

    elif dtype == int:
        # large python ints can overflow default NumPy int type
        try:
            v = np.array(values_for_construct, dtype=dtype)
        except OverflowError:
            v = np.array(values_for_construct, dtype=DTYPE_OBJECT)
    else:
        # if dtype was None, we might have discovered this was object and but no tuples; faster to do this constructor instead of null slice assignment
        v = np.array(values_for_construct, dtype=dtype)

    v.flags.writeable = False
    return v, is_unique

#-------------------------------------------------------------------------------

def slice_to_ascending_slice(
        key: slice,
        size: int
        ) -> slice:
    '''
    Given a slice, return a slice that, with ascending integers, covers the same values.
    '''
    if key.step is None or key.step > 0:
        return key

    stop = key.start if key.start is None else key.start + 1

    if key.step == -1:
        # if 6, 1, -1, then
        start = key.stop if key.stop is None else key.stop + 1
        return slice(start, stop, 1)

    # if 6, 1, -2: 6, 4, 2; then
    start = next(reversed(range(*key.indices(size))))
    return slice(start, stop, -key.step)

#-------------------------------------------------------------------------------
# dates

_DT64_DAY = np.dtype('datetime64[D]')
_DT64_MONTH = np.dtype('datetime64[M]')
_DT64_YEAR = np.dtype('datetime64[Y]')
_DT64_S = np.dtype('datetime64[s]')
_DT64_MS = np.dtype('datetime64[ms]')

_TD64_DAY = np.timedelta64(1, 'D')
_TD64_MONTH = np.timedelta64(1, 'M')
_TD64_YEAR = np.timedelta64(1, 'Y')
_TD64_S = np.timedelta64(1, 's')
_TD64_MS = np.timedelta64(1, 'ms')

_DT_NOT_FROM_INT = (_DT64_DAY, _DT64_MONTH)

def to_datetime64(
        value: DateInitializer,
        dtype: tp.Optional[np.dtype] = None
        ) -> np.datetime64:
    '''
    Convert a value ot a datetime64; this must be a datetime64 so as to be hashable.
    '''
    # for now, only support creating from a string, as creation from integers is based on offset from epoch
    if not isinstance(value, np.datetime64):
        if dtype is None:
            # let constructor figure it out
            dt = np.datetime64(value)
        else: # assume value is single value;
            # note that integers will be converted to units from epoch
            if isinstance(value, int):
                if dtype == _DT64_YEAR:
                    # convert to string as that is likely what is wanted
                    value = str(value)
                elif dtype in _DT_NOT_FROM_INT:
                    raise RuntimeError('attempting to create {} from an integer, which is generally not desired as the result will be offset from the epoch.'.format(dtype))
            # cannot use the datetime directly
            if dtype != np.datetime64:
                dt = np.datetime64(value, np.datetime_data(dtype)[0])
            else: # cannot use a generic datetime type
                dt = np.datetime64(value)
    else: # if a dtype was explicitly given, check it
        # value is an instance of a datetime64, and has a dtype attr
        dt = value
        if dtype:
            # dtype can be either generic, or a matching specific dtype
            if dtype != np.datetime64 and dtype != dt.dtype:
                raise RuntimeError('not supported dtype', dt, dtype)
    return dt

def to_timedelta64(value: datetime.timedelta) -> np.timedelta64:
    '''
    Convert a datetime.timedelta into a NumPy timedelta64. This approach is better than using np.timedelta64(value), as that reduces all values to microseconds.
    '''
    return reduce(operator.add,
        (np.timedelta64(getattr(value, attr), code) for attr, code in TIME_DELTA_ATTR_MAP if getattr(value, attr) > 0))

def _slice_to_datetime_slice_args(key: slice, dtype: tp.Optional[np.dtype] = None) -> tp.Iterator[tp.Optional[np.datetime64]]:
    '''
    Given a slice representing a datetime region, convert to arguments for a new slice, possibly using the appropriate dtype for conversion.
    '''
    for attr in SLICE_ATTRS:
        value = getattr(key, attr)
        if value is None:
            yield None
        else:
            yield to_datetime64(value, dtype=dtype)

def key_to_datetime_key(
        key: GetItemKeyType,
        dtype: np.dtype = np.datetime64) -> GetItemKeyType:
    '''
    Given an get item key for a Date index, convert it to np.datetime64 representation.
    '''
    if isinstance(key, slice):
        return slice(*_slice_to_datetime_slice_args(key, dtype=dtype))

    if isinstance(key, np.datetime64):
        return key

    if isinstance(key, str):
        return to_datetime64(key, dtype=dtype)

    if isinstance(key, np.ndarray):
        if key.dtype.kind == 'b' or key.dtype.kind == 'M':
            return key
        return key.astype(dtype)

    if hasattr(key, '__len__'):
        # use dtype via array constructor to determine type; or just use datetime64 to parse to the passed-in representationn
        return np.array(key, dtype=dtype)

    if hasattr(key, '__next__'): # a generator-like
        return np.array(tuple(tp.cast(tp.Iterator[tp.Any], key)), dtype=dtype)

    # for now, return key unaltered
    return key

#-------------------------------------------------------------------------------

def array_to_groups_and_locations(
        array: np.ndarray,
        unique_axis: tp.Optional[int] = 0) -> tp.Tuple[np.ndarray, np.ndarray]:
    '''Locations are index positions for each group.
    '''
    try:
        groups, locations = np.unique(
                array,
                return_inverse=True,
                axis=unique_axis)
    except TypeError:
        # group by string representations, necessary when types are not comparable
        _, group_index, locations = np.unique(
                array.astype(str),
                return_index=True,
                return_inverse=True,
                axis=unique_axis)
        # groups here are the strings; need to restore to values
        groups = array[group_index]

    return groups, locations


def isna_element(value: tp.Any) -> bool:
    '''Return Boolean if value is an NA.
    '''

    try:
        return tp.cast(bool, np.isnan(value))
    except TypeError:
        pass
    try:
        return tp.cast(bool, np.isnat(value))
    except TypeError:
        pass

    return value is None


def isna_array(array: np.ndarray) -> np.ndarray:
    '''Given an np.ndarray, return a bolean array setting True for missing values.

    Note: the returned array is not made immutable.
    '''
    kind = array.dtype.kind
    # matches all floating point types
    if kind in DTYPE_NAN_KIND:
        return np.isnan(array)
    elif kind in DTYPE_NAT_KIND:
        return np.isnat(array)
    # match everything that is not an object; options are: biufcmMOSUV
    elif kind != 'O':
        return np.full(array.shape, False, dtype=bool)
    # only check for None if we have an object type
    return np.not_equal(array, array) | np.equal(array, None)

    # try: # this will only work for arrays that do not have strings
    #     # astype: None gets converted to nan if possible
    #     # cannot use can_cast to reliabily identify arrays with non-float-castable elements
    #     return np.isnan(array.astype(float))
    # except ValueError:
    #     # this Exception means there was a character or something not castable to float
    #     # this is a big perforamnce hit; problem is cannot find np.nan in numpy object array
    #     if array.ndim == 1:
    #         return np.fromiter((x is None or x is np.nan for x in array),
    #                 count=array.size,
    #                 dtype=bool)

    #     return np.fromiter((x is None or x is np.nan for x in array.flat),
    #             count=array.size,
    #             dtype=bool).reshape(array.shape)



def binary_transition(
        array: np.ndarray,
        axis: int = 0
        ) -> np.ndarray:
    '''
    Given a Boolean 1D array, return the index positions (integers) at False values where that False was previously True, or will be True

    Returns:
        For a 1D input, a 1D array of integers; for a 2D input, a 1D object array of lists, where each position corresponds to a found index position. Returning a list is undesirable, but more efficient as a list will be neede for selection downstream.
    '''

    if len(array) == 0:
        # NOTE: on some platforms this may not be the same dtype as returned from np.nonzero
        return EMPTY_ARRAY_INT

    not_array = ~array

    if array.ndim == 1:
        # non-nan values that go (from left to right) to NaN
        target_sel_leading = (array ^ roll_1d(array, -1)) & not_array
        target_sel_leading[-1] = False # wrap around observation invalid
        # non-nan values that were previously NaN (from left to right)
        target_sel_trailing = (array ^ roll_1d(array, 1)) & not_array
        target_sel_trailing[0] = False # wrap around observation invalid

        return np.nonzero(target_sel_leading | target_sel_trailing)[0]

    elif array.ndim == 2:
        # if axis == 0, we compare rows going down/up, looking at column values
        # non-nan values that go (from left to right) to NaN
        target_sel_leading = (array ^ roll_2d(array, -1, axis=axis)) & not_array
        # non-nan values that were previously NaN (from left to right)
        target_sel_trailing = (array ^ roll_2d(array, 1, axis=axis)) & not_array

        # wrap around observation invalid
        if axis == 0:
            # process an entire row
            target_sel_leading[-1, :] = False
            target_sel_trailing[0, :] = False
        else:
            # process entire column
            target_sel_leading[:, -1] = False
            target_sel_trailing[:, 0] = False

        # this dictionary could be very sparse compared to axis dimensionality
        indices_by_axis: tp.DefaultDict[int, tp.List[int]] = defaultdict(list)
        for y, x in zip(*np.nonzero(target_sel_leading | target_sel_trailing)):
            if axis == 0:
                # store many rows values for each column
                indices_by_axis[x].append(y)
            else:
                indices_by_axis[y].append(x)

        # if axis is 0, return column width, else return row height
        post = np.empty(dtype=object, shape=array.shape[not axis])
        for k, v in indices_by_axis.items():
            post[k] = v

        return post

    raise NotImplementedError(f'no handling for array with ndim: {array.ndim}')


#-------------------------------------------------------------------------------
# tools for handling duplicates

def _array_to_duplicated_hashable(
        array: np.ndarray,
        axis: int = 0,
        exclude_first: bool = False,
        exclude_last: bool = False) -> np.ndarray:
    '''
    Algorithm for finding duplicates in unsortable arrays for hashables. This will always be an object array.
    '''
    # np.unique fails under the same conditions that sorting fails, so there is no need to try np.unique: must go to set drectly.
    len_axis = array.shape[axis]

    if array.ndim == 1:
        value_source = array
        to_hashable = None
    else:
        if axis == 0:
            value_source = array # will iterate rows
        else:
            value_source = (array[:, i] for i in range(len_axis))
        # values will be arrays; must convert to tuples to make hashable
        to_hashable = tuple


    is_dupe = np.full(len_axis, False)

    # could exit early with a set, but would have to hash all array twice to go to set and dictionary
    # creating a list for each entry and tracking indices would be very expensive

    unique_to_first: tp.Dict[tp.Hashable, int] = {} # value to first occurence
    dupe_to_first: tp.Dict[tp.Hashable, int] = {}
    dupe_to_last: tp.Dict[tp.Hashable, int] = {}

    for idx, v in enumerate(value_source):

        # import ipdb; ipdb.set_trace()
        if to_hashable:
            v = to_hashable(v)

        if v not in unique_to_first:
            unique_to_first[v] = idx
        else:
            # v has been seen before; upate Boolean array
            is_dupe[idx] = True

            # if no entry in dupe to first, no update with value in unique to first, which is the index this values was first seen
            if v not in dupe_to_first:
                dupe_to_first[v] = unique_to_first[v]
            # always update last
            dupe_to_last[v] = idx

    if exclude_last: # overwrite with False
        is_dupe[list(dupe_to_last.values())] = False

    if not exclude_first: # add in first values
        is_dupe[list(dupe_to_first.values())] = True

    return is_dupe


def _array_to_duplicated_sortable(
        array: np.ndarray,
        axis: int = 0,
        exclude_first: bool = False,
        exclude_last: bool = False) -> np.ndarray:
    '''
    Algorithm for finding duplicates in sortable arrays. This may or may not be an object array, as some object arrays (those of compatible types) are sortable.
    '''
    # based in part on https://stackoverflow.com/questions/11528078/determining-duplicate-values-in-an-array
    # https://stackoverflow.com/a/43033882/388739
    # indices to sort and sorted array
    # a right roll on the sorted array, comparing to the original sorted array. creates a boolean array, with all non-first duplicates marked as True

    # NOTE: this is not compatible with heterogenous typed object arrays, raises TypeError

    if array.ndim == 1:
        o_idx = np.argsort(array, axis=None, kind=DEFAULT_STABLE_SORT_KIND)
        array_sorted = array[o_idx]
        opposite_axis = 0
        # f_flags is True where there are duplicated values in the sorted array
        f_flags = array_sorted == roll_1d(array_sorted, 1)
    else:
        if axis == 0: # sort rows
            # first should be last
            arg = [array[:, x] for x in range(array.shape[1] - 1, -1, -1)]
            o_idx = np.lexsort(arg)
            array_sorted = array[o_idx]
        elif axis == 1: # sort columns
            arg = [array[x] for x in range(array.shape[0] - 1, -1, -1)]
            o_idx = np.lexsort(arg)
            array_sorted = array[:, o_idx]
        else:
            raise NotImplementedError(f'no handling for axis: {axis}')

        opposite_axis = int(not bool(axis))
        # rolling axis 1 rotates columns; roll axis 0 rotates rows
        match = array_sorted == roll_2d(array_sorted, 1, axis=axis)
        f_flags = match.all(axis=opposite_axis)

    if not f_flags.any():
        # we always return a 1 dim array
        return np.full(len(f_flags), False)

    # The first element of f_flags should always be False.
    # In certain edge cases, this doesn't happen naturally.
    # Index 0 should always exist, due to `.any()` behavior.
    f_flags[0] = np.False_

    if exclude_first and not exclude_last:
        dupes = f_flags
    else:
        # non-LAST duplicates is a left roll of the non-first flags.
        l_flags = roll_1d(f_flags, -1)

        if not exclude_first and exclude_last:
            dupes = l_flags
        elif not exclude_first and not exclude_last:
            # all duplicates is the union.
            dupes = f_flags | l_flags
        else:
            # all non-first, non-last duplicates is the intersection.
            dupes = f_flags & l_flags

    # undo the sort: get the indices to extract Booleans from dupes; in some cases r_idx is the same as o_idx, but not all
    r_idx = np.argsort(o_idx, axis=None, kind=DEFAULT_STABLE_SORT_KIND)
    return dupes[r_idx]



def array_to_duplicated(
        array: np.ndarray,
        axis: int = 0,
        exclude_first: bool = False,
        exclude_last: bool = False) -> np.ndarray:
    '''Given a numpy array (1D or 2D), return a Boolean array along the specified axis that shows which values are duplicated. By default, all duplicates are indicated. For 2d arrays, axis 0 compares rows and returns a row-length Boolean array; axis 1 compares columns and returns a column-length Boolean array.

    Args:
        exclude_first: Mark as True all duplicates except the first encountared.
        exclude_last: Mark as True all duplicates except the last encountared.
    '''
    try:
        return _array_to_duplicated_sortable(
                array=array,
                axis=axis,
                exclude_first=exclude_first,
                exclude_last=exclude_last
                )
    except TypeError: # raised if not sorted
        return _array_to_duplicated_hashable(
                array=array,
                axis=axis,
                exclude_first=exclude_first,
                exclude_last=exclude_last
                )


#-------------------------------------------------------------------------------
def array_shift(*,
        array: np.ndarray,
        shift: int,
        axis: int, # 0 is rows, 1 is columns
        wrap: bool,
        fill_value: tp.Any = np.nan) -> np.ndarray:
    '''
    Apply an np-style roll to a 1D or 2D array; if wrap is False, fill values out-shifted values with fill_value.

    Args:
        fill_value: only used if wrap is False.
    '''

    # works for all shapes
    if shift > 0:
        shift_mod = shift % array.shape[axis]
    elif shift < 0:
        # do negative modulo to force negative value
        shift_mod = shift % -array.shape[axis]
    else:
        shift_mod = 0

    if (not wrap and shift == 0) or (wrap and shift_mod == 0):
        # must copy so as not let caller mutate arguement
        return array.copy()

    if wrap:
        # roll functions will handle finding noop rolls
        if array.ndim == 1:
            return roll_1d(array, shift_mod)
        return roll_2d(array, shift_mod, axis=axis)

    # will insure that the result can contain the fill and the original values
    result = full_for_fill(array.dtype, array.shape, fill_value)

    if axis == 0:
        if shift > 0:
            result[shift:] = array[:-shift]
        elif shift < 0:
            result[:shift] = array[-shift:]
    elif axis == 1:
        if shift > 0:
            result[:, shift:] = array[:, :-shift]
        elif shift < 0:
            result[:, :shift] = array[:, -shift:]

    return result

def array2d_to_tuples(array: np.ndarray) -> tp.Iterator[tp.Tuple[tp.Any, ...]]:
    for row in array: # assuming 2d
        yield tuple(row)

#-------------------------------------------------------------------------------
# extension to union and intersection handling

def _ufunc_set_1d(
        func: tp.Callable[[np.ndarray, np.ndarray], np.ndarray],
        array: np.ndarray,
        other: np.ndarray,
        *,
        assume_unique: bool=False
        ) -> np.ndarray:
    '''
    Peform 1D set operations. When possible, short-circuit comparison and return array with original order.

    Args:
        assume_unique: if arguments are assumed unique, can implement optional identity filtering, which retains order (un sorted) for opperands that are equal. This is important in numerous operations on the matching Indices where order should not be perterbed.
    '''
    if func == np.intersect1d:
        is_union = False
    elif func == np.union1d:
        is_union = True
    else:
        raise NotImplementedError('unexpected func', func)

    dtype = resolve_dtype(array.dtype, other.dtype)

    # optimizations for empty arrays
    if not is_union: # intersection with empty
        if len(array) == 0 or len(other) == 0:
            # not sure what DTYPE is correct to return here
            return np.array(EMPTY_TUPLE, dtype=dtype)

    if assume_unique:
        # can only return arguments, and use length to determine unique comparison condition, if arguments are assumed to already be unique
        if is_union:
            if len(array) == 0:
                return other
            elif len(other) == 0:
                return array

        if len(array) == len(other):
            compare = array == other
            if isinstance(compare, BOOL_TYPES) and compare:
                return array
            elif isinstance(compare, np.ndarray) and compare.all(axis=None):
                return array

    set_compare = False
    array_is_str = array.dtype.kind in DTYPE_STR_KIND
    other_is_str = other.dtype.kind in DTYPE_STR_KIND

    if array_is_str ^ other_is_str:
        # if only one is string
        set_compare = True

    if set_compare or dtype.kind == 'O':
        if is_union:
            result = set(array) | set(other)
        else:
            result = set(array) & set(other)
        v, _ = iterable_to_array(result, dtype)
        return v

    return func(array, other)


def _ufunc_set_2d(
        func: tp.Callable[[np.ndarray, np.ndarray], np.ndarray],
        array: np.ndarray,
        other: np.ndarray,
        *,
        assume_unique: bool=False
        ) -> np.ndarray:
    '''
    Peform 2D set operations. When possible, short-circuit comparison and return array with original order.

    Args:
        func: a 1d set operation
        array: can be a 2D array, or a 1D object array of tuples.
        other: can be a 2D array, or a 1D object array of tuples.
        assume_unique: if True, array operands are assumed unique and order is preserved for matching operands.
    Returns:
        Either a 2D array, or a 1D object array of tuples.
    '''
    if func == np.intersect1d:
        is_union = False
    elif func == np.union1d:
        is_union = True
    else:
        raise NotImplementedError('unexpected func', func)

    # if either are object, or combination resovle to object, get object
    dtype = resolve_dtype(array.dtype, other.dtype)

    # optimizations for empty arrays
    if not is_union: # intersection with empty
        if len(array) == 0 or len(other) == 0:
            # not sure what DTYPE is correct to return here
            return np.array(EMPTY_TUPLE, dtype=dtype)

    if assume_unique:
        # can only return arguments, and use length to determine unique comparison condition, if arguments are assumed to already be unique
        if is_union:
            if len(array) == 0:
                return other
            elif len(other) == 0:
                return array

        # will not match a 2D array of integers and 1D array of tuples containing integers (would have to do a post-set comparison, but would loose order)
        if array.shape == other.shape:
            compare = array == other
            if isinstance(compare, BOOL_TYPES) and compare:
                return array
            elif isinstance(compare, np.ndarray) and compare.all(axis=None):
                return array

    if dtype.kind == 'O':
        # assume that 1D arrays arrays are arrays of tuples
        if array.ndim == 1:
            array_set = set(array)
        else: # assume row-wise comparison
            array_set = set(tuple(row) for row in array)

        if other.ndim == 1:
            other_set = set(other)
        else: # assume row-wise comparison
            other_set = set(tuple(row) for row in other)

        if is_union:
            result = array_set | other_set
        else:
            result = array_set & other_set

        # NOTE: this sort may not always be succesful
        try:
            values: tp.Sequence[tp.Tuple[tp.Hashable, ...]] = sorted(result)
        except TypeError:
            values = tuple(result)

        # returns a 1D object array of tuples
        post = np.empty(len(values), dtype=object)
        post[:] = values
        return post

    # from here, we assume we have two 2D arrays
    if array.ndim != 2 or other.ndim != 2:
        raise RuntimeError('non-object arrays have to both be 2D')

    # number of columns must be the same, as doing row-wise comparison, and determines the length of each row
    assert array.shape[1] == other.shape[1]
    width = array.shape[1]

    if array.dtype != dtype:
        array = array.astype(dtype)
    if other.dtype != dtype:
        other = other.astype(dtype)

    if width == 1:
        # let the function flatten the array, then reshape into 2D
        post = func(array, other)
        return post.reshape(len(post), width)

    # this approach based on https://stackoverflow.com/questions/9269681/intersection-of-2d-numpy-ndarrays
    # we can use a the 1D function on the rows, once converted to a structured array

    dtype_view = [('', array.dtype)] * width
    # creates a view of tuples for 1D operation
    array_view = array.view(dtype_view)
    other_view = other.view(dtype_view)

    return func(array_view, other_view).view(dtype).reshape(-1, width)


def union1d(array: np.ndarray,
        other: np.ndarray,
        assume_unique: bool=False
        ) -> np.ndarray:
    '''
    Union on 1D array, handling diverse types and short-circuiting to preserve order where appropriate.
    '''
    return _ufunc_set_1d(np.union1d,
            array,
            other,
            assume_unique=assume_unique)

def intersect1d(
        array: np.ndarray,
        other: np.ndarray,
        assume_unique: bool=False
        ) -> np.ndarray:
    '''
    Intersect on 1D array, handling diverse types and short-circuiting to preserve order where appropriate.
    '''
    return _ufunc_set_1d(np.intersect1d,
            array,
            other,
            assume_unique=assume_unique)

def union2d(array: np.ndarray,
        other: np.ndarray,
        *,
        assume_unique: bool=False
        ) -> np.ndarray:
    '''
    Union on 2D array, handling diverse types and short-circuiting to preserve order where appropriate.
    '''
    return _ufunc_set_2d(np.union1d,
            array,
            other,
            assume_unique=assume_unique)

def intersect2d(array: np.ndarray,
        other: np.ndarray,
        *,
        assume_unique: bool=False
        ) -> np.ndarray:
    '''
    Intersect on 2D array, handling diverse types and short-circuiting to preserve order where appropriate.
    '''
    return _ufunc_set_2d(np.intersect1d,
            array,
            other,
            assume_unique=assume_unique)


def ufunc_set_iter(
        arrays: tp.Iterable[np.ndarray],
        union: bool = False,
        *,
        assume_unique: bool=False
        ) -> np.ndarray:
    '''
    Iteratively apply a set operation ufunc to 1D or 2D arrays; if all are equal, no operation is performed and order is retained.

    Args:
        arrays: iterator of arrays; can be a Generator.
        union: if True, a union is taken, else, an intersection.
    '''
    arrays = iter(arrays)
    result = next(arrays)

    # will detect ndim by first value, but insure that all other arrays have the same ndim
    if result.ndim == 1:
        ufunc = union1d if union else intersect1d
        ndim = 1
    else: # ndim == 2
        ufunc = union2d if union else intersect2d # type: ignore
        ndim = 2

    for array in arrays:
        if array.ndim != ndim:
            raise RuntimeError('arrays do not all have the same ndim')

        # to retain order on identity, assume_unique must be True
        result = ufunc(result, array, assume_unique=assume_unique)

        if not union and len(result) == 0:
            # short circuit intersection that results in no common values
            return result

    return result

#-------------------------------------------------------------------------------

def slices_from_targets(
        target_index: tp.Sequence[int],
        target_values: tp.Sequence[tp.Any],
        length: int,
        directional_forward: bool,
        limit: int,
        slice_condition: tp.Callable[[slice], bool]
        ) -> tp.Iterator[tp.Tuple[slice, tp.Any]]:
    '''
    Utility function used in fillna_directional implementations for Series and Frame. Yields slices and values for setting contiguous ranges of values.

    NOTE: slice_condition is still needed to check if a slice actually has missing values; see if there is a way to determine these cases in advance, so as to not call a function on each slice.

    Args:
        target_index: iterable of integers, where integers are positions where (as commonly used) values along an axis were previously NA, or will be NA. Often the result of binary_transition()
        target_values: values found at the index positions
        length: the maximum lengh in the target array
        directional_forward: determine direction
        limit: set a max size for all slices
        slice_condition: optional function for filtering slices.
    '''
    if directional_forward:
        target_slices = (
                slice(start+1, stop)
                for start, stop in
                zip_longest(target_index, target_index[1:], fillvalue=length)
                )
    else:
        # NOTE: usage of None here is awkward; try to use zero
        target_slices = (
                slice((start+1 if start is not None else start), stop)
                for start, stop in
                zip(chain((None,), target_index[:-1]), target_index)
                )

    for target_slice, value in zip(target_slices, target_values):

        # all conditions that are noop slices
        if target_slice.start == target_slice.stop:
            continue
        elif (directional_forward
                and target_slice.start is not None
                and target_slice.start >= length):
            continue
        elif (not directional_forward
                and target_slice.start is None
                and target_slice.stop == 0):
            continue
        elif target_slice.stop is None:
            # stop value should never be None
            raise NotImplementedError('unexpected slice', target_slice)

        # only process if first value of slice is NaN
        if slice_condition(target_slice):

            if limit > 0:
                # get the length of the range resulting from the slice; if bigger than limit, reduce the by that amount
                shift = len(range(*target_slice.indices(length))) - limit
                if shift > 0:

                    if directional_forward:
                        target_slice = slice(
                                target_slice.start,
                                target_slice.stop - shift)
                    else:
                        target_slice = slice(
                                (target_slice.start or 0) + shift,
                                target_slice.stop)

            yield target_slice, value



#-------------------------------------------------------------------------------
# URL handling, file downloading, file writing

def _read_url(fp: str) -> str:
    with request.urlopen(fp) as response:
        return tp.cast(str, response.read().decode('utf-8'))


def write_optional_file(
        content: str,
        fp: tp.Optional[FilePathOrFileLike] = None,
        ) -> tp.Optional[str]:

    fd = f = None
    if not fp: # get a temp file
        fd, fp = tempfile.mkstemp(suffix='.html', text=True)
    elif isinstance(fp, StringIO):
        f = fp
        fp = None
    # nothing to do if we have an fp

    if f is None: # do not have a file object
        try:
            assert isinstance(fp, str)
            with tp.cast(StringIO, open(fp, 'w')) as f:
                f.write(content)
        finally:
            if fd is not None:
                os.close(fd)
    else: # string IO
        f.write(content)
        f.seek(0)
    return tp.cast(str, fp)

#-------------------------------------------------------------------------------

TContainer = tp.TypeVar('TContainer', 'Index', 'Series', 'Frame', 'TypeBlocks')
GetItemFunc = tp.TypeVar('GetItemFunc', bound=tp.Callable[[GetItemKeyType], TContainer])

class InterfaceGetItem(tp.Generic[TContainer]):

    __slots__ = ('_func',)

    def __init__(self, func: tp.Callable[[GetItemKeyType], TContainer]) -> None:
        self._func: tp.Callable[[GetItemKeyType], TContainer] = func

    def __getitem__(self, key: GetItemKeyType) -> TContainer:
        return self._func(key)

#-------------------------------------------------------------------------------

class InterfaceSelection1D(tp.Generic[TContainer]):
    '''An instance to serve as an interface to all of iloc and loc
    '''

    __slots__ = (
            '_func_iloc',
            '_func_loc',
            )

    def __init__(self, *,
            func_iloc: GetItemFunc,
            func_loc: GetItemFunc) -> None:

        self._func_iloc = func_iloc
        self._func_loc = func_loc

    @property
    def iloc(self) -> InterfaceGetItem[TContainer]:
        return InterfaceGetItem(self._func_iloc)

    @property
    def loc(self) -> InterfaceGetItem[TContainer]:
        return InterfaceGetItem(self._func_loc)


#-------------------------------------------------------------------------------

class InterfaceSelection2D(tp.Generic[TContainer]):
    '''An instance to serve as an interface to all of iloc, loc, and __getitem__ extractors.
    '''

    __slots__ = (
            '_func_iloc',
            '_func_loc',
            '_func_getitem'
            )

    def __init__(self, *,
            func_iloc: GetItemFunc,
            func_loc: GetItemFunc,
            func_getitem: GetItemFunc) -> None:

        self._func_iloc = func_iloc
        self._func_loc = func_loc
        self._func_getitem = func_getitem

    def __getitem__(self, key: GetItemKeyType) -> tp.Any:
        return self._func_getitem(key)

    @property
    def iloc(self) -> InterfaceGetItem[TContainer]:
        return InterfaceGetItem(self._func_iloc)

    @property
    def loc(self) -> InterfaceGetItem[TContainer]:
        return InterfaceGetItem(self._func_loc)

#-------------------------------------------------------------------------------

class InterfaceAsType:
    '''An instance to serve as an interface to __getitem__ extractors.
    '''

    __slots__ = ('_func_getitem',)

    def __init__(self, func_getitem: tp.Callable[[GetItemKeyType], 'FrameAsType']) -> None:
        '''
        Args:
            _func_getitem: a callable that expects a _func_getitem key and returns a FrameAsType interface; for example, Frame._extract_getitem_astype.
        '''
        self._func_getitem = func_getitem

    def __getitem__(self, key: GetItemKeyType) -> 'FrameAsType':
        return self._func_getitem(key)

    def __call__(self, dtype: np.dtype) -> 'Frame':
        return self._func_getitem(NULL_SLICE)(dtype)


