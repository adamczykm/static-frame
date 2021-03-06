

import unittest
import datetime
import typing as tp

import numpy as np

from static_frame.core.util import isna_array
from static_frame.core.util import resolve_dtype
from static_frame.core.util import resolve_dtype_iter
from static_frame.core.util import array_to_duplicated
from static_frame.core.util import ufunc_set_iter

from static_frame.core.util import intersect2d
from static_frame.core.util import union2d
from static_frame.core.util import concat_resolved
from static_frame.core.util import _isin_1d
from static_frame.core.util import _isin_2d
from static_frame.core.util import isin

from static_frame.core.util import _gen_skip_middle
from static_frame.core.util import dtype_to_na
from static_frame.core.util import key_to_datetime_key
from static_frame.core.util import column_1d_filter
from static_frame.core.util import row_1d_filter

from static_frame.core.container import _ufunc_logical_skipna

from static_frame.core.util import _read_url
from static_frame.core.util import _ufunc_set_2d

# from static_frame import Index

# from static_frame.core.util import _dict_to_sorted_items
from static_frame.core.util import iterable_to_array_1d
from static_frame.core.util import iterable_to_array_2d

# from static_frame.core.util import collection_and_dtype_to_array



from static_frame.core.util import slice_to_ascending_slice
from static_frame.core.util import array_shift
from static_frame.core.util import ufunc_unique
from static_frame.core.util import ufunc_axis_skipna
from static_frame.core.util import to_timedelta64
from static_frame.core.util import binary_transition

from static_frame.core.util import roll_1d
from static_frame.core.util import roll_2d

from static_frame.core.util import union1d
from static_frame.core.util import intersect1d

from static_frame.core.util import to_datetime64
from static_frame.core.util import _DT64_YEAR
from static_frame.core.util import _DT64_DAY

from static_frame.core.util import resolve_type_iter

from static_frame.core.util import argmin_1d
from static_frame.core.util import argmax_1d
from static_frame.core.util import argmin_2d
from static_frame.core.util import argmax_2d

from static_frame.core.util import _array_to_duplicated_sortable
from static_frame.core.util import _ufunc_set_1d

from static_frame.test.test_case import TestCase
from static_frame.test.test_case import UnHashable


class TestUnit(TestCase):

    def test_gen_skip_middle_a(self) -> None:

        forward = lambda: [3, 2, 5]
        reverse = lambda: [3, 2, 5]

        post = _gen_skip_middle(
                forward_iter=forward,
                forward_count=3,
                reverse_iter=reverse,
                reverse_count=3,
                center_sentinel=-1)

        self.assertEqual(list(post), [3, 2, 5, -1, 5, 2, 3])

        post = _gen_skip_middle(
                forward_iter=forward,
                forward_count=2,
                reverse_iter=reverse,
                reverse_count=2,
                center_sentinel=0)

        self.assertEqual(list(post), [3, 2, 0, 2, 3])




    def test_ufunc_logical_skipna_a(self) -> None:

        # empty arrays
        a1 = np.array([], dtype=float)
        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=False), True)

        a1 = np.array([], dtype=float)
        self.assertEqual(_ufunc_logical_skipna(a1, np.any, skipna=False), False)


        # float arrays 1d
        a1 = np.array([2.4, 5.4], dtype=float)
        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=True), True)

        a1 = np.array([2.4, 0], dtype=float)
        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=False), False)

        a1 = np.array([0, np.nan, 0], dtype=float)
        self.assertEqual(_ufunc_logical_skipna(a1, np.any, skipna=True), False)

        a1 = np.array([0, np.nan, 0], dtype=float)
        self.assertEqual(_ufunc_logical_skipna(a1, np.any, skipna=False), True)


        # float arrays 2d
        a1 = np.array([[2.4, 5.4, 3.2], [2.4, 5.4, 3.2]], dtype=float)
        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=False, axis=0).tolist(),
                [True, True, True])


        a1 = np.array([[2.4, 5.4, 3.2], [2.4, 5.4, 3.2]], dtype=float)
        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=False, axis=1).tolist(),
                [True, True])

        a1 = np.array([[2.4, 5.4, 0], [2.4, 5.4, 3.2]], dtype=float)
        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=False, axis=0).tolist(),
                [True, True, False])

        a1 = np.array([[2.4, 5.4, 0], [2.4, 5.4, 3.2]], dtype=float)
        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=False, axis=1).tolist(),
                [False, True])


        # object arrays
        a1 = np.array([[2.4, 5.4, 0], [2.4, None, 3.2]], dtype=object)

        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=False, axis=1).tolist(),
                [False, False])
        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=False, axis=0).tolist(),
                [True, False, False])


        a1 = np.array([[2.4, 5.4, 0], [2.4, np.nan, 3.2]], dtype=object)
        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=False, axis=0).tolist(),
                [True, True, False])


    def test_ufunc_logical_skipna_b(self) -> None:
        # object arrays

        a1 = np.array([['sdf', '', 'wer'], [True, False, True]], dtype=object)

        self.assertEqual(
                _ufunc_logical_skipna(a1, np.all, skipna=False, axis=0).tolist(),
                [True, False, True]
                )
        self.assertEqual(
                _ufunc_logical_skipna(a1, np.all, skipna=False, axis=1).tolist(),
                [False, False]
                )


        # string arrays
        a1 = np.array(['sdf', ''], dtype=str)
        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=False, axis=0), False)
        self.assertEqual(_ufunc_logical_skipna(a1, np.all, skipna=True, axis=0), False)


        a1 = np.array([['sdf', '', 'wer'], ['sdf', '', 'wer']], dtype=str)
        self.assertEqual(
                _ufunc_logical_skipna(a1, np.all, skipna=False, axis=0).tolist(),
                [True,  False,  True])

        self.assertEqual(
                _ufunc_logical_skipna(a1, np.all, skipna=False, axis=1).tolist(),
                [False, False])

        self.assertEqual(
                _ufunc_logical_skipna(a1, np.any, skipna=False, axis=0).tolist(),
                [True,  False,  True])

        self.assertEqual(
                _ufunc_logical_skipna(a1, np.any, skipna=False, axis=1).tolist(),
                [True, True])


    def test_ufunc_logical_skipna_c(self) -> None:

        a1 = np.array([], dtype=float)
        with self.assertRaises(NotImplementedError):
            _ufunc_logical_skipna(a1, np.sum, skipna=True)


    def test_ufunc_logical_skipna_d(self) -> None:

        a1 = np.array(['2018-01-01', '2018-02-01'], dtype=np.datetime64)
        post = _ufunc_logical_skipna(a1, np.all, skipna=True)
        self.assertTrue(post)


    def test_ufunc_logical_skipna_e(self) -> None:

        a1 = np.array([['2018-01-01', '2018-02-01'],
                ['2018-01-01', '2018-02-01']], dtype=np.datetime64)
        post = _ufunc_logical_skipna(a1, np.all, skipna=True)
        self.assertEqual(post.tolist(), [True, True])




    def test_resolve_dtype_a(self) -> None:

        a1 = np.array([1, 2, 3])
        a2 = np.array([False, True, False])
        a3 = np.array(['b', 'c', 'd'])
        a4 = np.array([2.3, 3.2])
        a5 = np.array(['test', 'test again'], dtype='S')
        a6 = np.array([2.3,5.4], dtype='float32')

        self.assertEqual(resolve_dtype(a1.dtype, a1.dtype), a1.dtype)

        self.assertEqual(resolve_dtype(a1.dtype, a2.dtype), np.object_)
        self.assertEqual(resolve_dtype(a2.dtype, a3.dtype), np.object_)
        self.assertEqual(resolve_dtype(a2.dtype, a4.dtype), np.object_)
        self.assertEqual(resolve_dtype(a3.dtype, a4.dtype), np.object_)
        self.assertEqual(resolve_dtype(a3.dtype, a6.dtype), np.object_)

        self.assertEqual(resolve_dtype(a1.dtype, a4.dtype), np.float64)
        self.assertEqual(resolve_dtype(a1.dtype, a6.dtype), np.float64)
        self.assertEqual(resolve_dtype(a4.dtype, a6.dtype), np.float64)

    def test_resolve_dtype_b(self) -> None:

        self.assertEqual(
                resolve_dtype(np.array('a').dtype, np.array('aaa').dtype),
                np.dtype(('U', 3))
                )



    def test_resolve_dtype_c(self) -> None:


        a1 = np.array(['2019-01', '2019-02'], dtype=np.datetime64)
        a2 = np.array(['2019-01-01', '2019-02-01'], dtype=np.datetime64)
        a3 = np.array([0, 1], dtype='datetime64[ns]')
        a4 = np.array([0, 1])

        self.assertEqual(str(resolve_dtype(a1.dtype, a2.dtype)),
                'datetime64[D]')
        self.assertEqual(resolve_dtype(a1.dtype, a3.dtype),
                np.dtype('<M8[ns]'))

        self.assertEqual(resolve_dtype(a1.dtype, a4.dtype),
                np.dtype('O'))





    def test_resolve_dtype_iter_a(self) -> None:

        a1 = np.array([1, 2, 3])
        a2 = np.array([False, True, False])
        a3 = np.array(['b', 'c', 'd'])
        a4 = np.array([2.3, 3.2])
        a5 = np.array(['test', 'test again'], dtype='S')
        a6 = np.array([2.3,5.4], dtype='float32')

        self.assertEqual(resolve_dtype_iter((a1.dtype, a1.dtype)), a1.dtype)
        self.assertEqual(resolve_dtype_iter((a2.dtype, a2.dtype)), a2.dtype)

        # boolean with mixed types
        self.assertEqual(resolve_dtype_iter((a2.dtype, a2.dtype, a3.dtype)), np.object_)
        self.assertEqual(resolve_dtype_iter((a2.dtype, a2.dtype, a5.dtype)), np.object_)
        self.assertEqual(resolve_dtype_iter((a2.dtype, a2.dtype, a6.dtype)), np.object_)

        # numerical types go to float64
        self.assertEqual(resolve_dtype_iter((a1.dtype, a4.dtype, a6.dtype)), np.float64)

        # add in bool or str, goes to object
        self.assertEqual(resolve_dtype_iter((a1.dtype, a4.dtype, a6.dtype, a2.dtype)), np.object_)
        self.assertEqual(resolve_dtype_iter((a1.dtype, a4.dtype, a6.dtype, a5.dtype)), np.object_)

        # mixed strings go to the largest
        self.assertEqual(resolve_dtype_iter((a3.dtype, a5.dtype)), np.dtype('<U10'))



    def test_isna_array_a(self) -> None:

        a1 = np.array([1, 2, 3])
        a2 = np.array([False, True, False])
        a3 = np.array(['b', 'c', 'd'])
        a4 = np.array([2.3, 3.2])
        a5 = np.array(['test', 'test again'], dtype='S')
        a6 = np.array([2.3, 5.4], dtype='float32')

        self.assertEqual(isna_array(a1).tolist(), [False, False, False])
        self.assertEqual(isna_array(a2).tolist(), [False, False, False])
        self.assertEqual(isna_array(a3).tolist(), [False, False, False])
        self.assertEqual(isna_array(a4).tolist(), [False, False])
        self.assertEqual(isna_array(a5).tolist(), [False, False])
        self.assertEqual(isna_array(a6).tolist(), [False, False])

        a1 = np.array([1, 2, 3, None])
        a2 = np.array([False, True, False, None])
        a3 = np.array(['b', 'c', 'd', None])
        a4 = np.array([2.3, 3.2, None])
        a5 = np.array(['test', 'test again', None])
        a6 = np.array([2.3, 5.4, None])

        self.assertEqual(isna_array(a1).tolist(), [False, False, False, True])
        self.assertEqual(isna_array(a2).tolist(), [False, False, False, True])
        self.assertEqual(isna_array(a3).tolist(), [False, False, False, True])
        self.assertEqual(isna_array(a4).tolist(), [False, False, True])
        self.assertEqual(isna_array(a5).tolist(), [False, False, True])
        self.assertEqual(isna_array(a6).tolist(), [False, False, True])

        a1 = np.array([1, 2, 3, np.nan])
        a2 = np.array([False, True, False, np.nan])
        a3 = np.array(['b', 'c', 'd', np.nan], dtype=object)
        a4 = np.array([2.3, 3.2, np.nan], dtype=object)
        a5 = np.array(['test', 'test again', np.nan], dtype=object)
        a6 = np.array([2.3, 5.4, np.nan], dtype='float32')

        self.assertEqual(isna_array(a1).tolist(), [False, False, False, True])
        self.assertEqual(isna_array(a2).tolist(), [False, False, False, True])
        self.assertEqual(isna_array(a3).tolist(), [False, False, False, True])
        self.assertEqual(isna_array(a4).tolist(), [False, False, True])
        self.assertEqual(isna_array(a5).tolist(), [False, False, True])
        self.assertEqual(isna_array(a6).tolist(), [False, False, True])


    def test_isna_array_b(self) -> None:

        a1 = np.array([[1, 2], [3, 4]])
        a2 = np.array([[False, True, False], [False, True, False]])
        a3 = np.array([['b', 'c', 'd'], ['b', 'c', 'd']])
        a4 = np.array([[2.3, 3.2, np.nan], [2.3, 3.2, np.nan]])
        a5 = np.array([['test', 'test again', np.nan],
                ['test', 'test again', np.nan]], dtype=object)
        a6 = np.array([[2.3, 5.4, np.nan], [2.3, 5.4, np.nan]], dtype='float32')

        self.assertEqual(isna_array(a1).tolist(),
                [[False, False], [False, False]])

        self.assertEqual(isna_array(a2).tolist(),
                [[False, False, False], [False, False, False]])

        self.assertEqual(isna_array(a3).tolist(),
                [[False, False, False], [False, False, False]])

        self.assertEqual(isna_array(a4).tolist(),
                [[False, False, True], [False, False, True]])

        self.assertEqual(isna_array(a5).tolist(),
                [[False, False, True], [False, False, True]])

        self.assertEqual(isna_array(a6).tolist(),
                [[False, False, True], [False, False, True]])


    def test_array_to_duplicated_a(self) -> None:
        a = array_to_duplicated(
                np.array([0,1,2,2,1,4,5,3,4,5,5,6]),
                exclude_first=False,
                exclude_last=False
                )
        self.assertEqual(a.tolist(),
                [False, True, True, True, True, True, True, False, True, True, True, False])

        a = array_to_duplicated(
                np.array([0,1,2,2,1,4,5,3,4,5,5,6]),
                exclude_first=True,
                exclude_last=False
                )
        self.assertEqual(a.tolist(),
                [False, False, False, True, True, False, False, False, True, True, True, False])


    def test_array_to_duplicated_b(self) -> None:
        a = np.array([[50, 50, 32, 17, 17], [2,2,1,3,3]])
        # find duplicate rows
        post = array_to_duplicated(a, axis=0)
        self.assertEqual(post.tolist(),
                [False, False])

        post = array_to_duplicated(a, axis=1)
        self.assertEqual(post.tolist(),
                [True, True, False, True, True])

        post = array_to_duplicated(a, axis=1, exclude_first=True)
        self.assertEqual(post.tolist(),
                [False, True, False, False, True])


    def test_array_to_duplicated_c(self) -> None:
        a = np.array([[50, 50, 32, 17, 17], [2,2,1,3,3]])
        with self.assertRaises(NotImplementedError):
            # axis cannot be None
            array_to_duplicated(a, axis=None)  # type: ignore


    def test_array_to_duplicated_d(self) -> None:
        c = array_to_duplicated(
                np.array(['q','q','q', 'a', 'w', 'w'], dtype=object),
                exclude_first=False,
                exclude_last=False
                )
        self.assertEqual(c.tolist(), [True, True, True, False, True, True])


    def test_array_to_duplicated_e(self) -> None:
        # NOTE: these cases fail with hetergenous types as we cannot sort
        a1 = np.array([0,0,1,0,None,None,0,1,None], dtype=object)
        a2 = np.array([0,0,1,0,'q','q',0,1,'q'], dtype=object)

        for array in (a1, a2):
            post1 = array_to_duplicated(
                    array,
                    exclude_first=False,
                    exclude_last=False
                    )
            self.assertEqual(post1.tolist(),
                [True, True, True, True, True, True, True, True, True])

            post2 = array_to_duplicated(
                    array,
                    exclude_first=True,
                    exclude_last=False
                    )
            self.assertEqual(post2.tolist(),
                [False, True, False, True, False, True, True, True, True])

            post3 = array_to_duplicated(
                    array,
                    exclude_first=False,
                    exclude_last=True
                    )
            self.assertEqual(post3.tolist(),
                [True, True, True, True, True, True, False, False, False])

            post4 = array_to_duplicated(
                    array,
                    exclude_first=True,
                    exclude_last=True
                    )
            self.assertEqual(post4.tolist(),
                [False, True, False, True, False, True, False, False, False])



    def test_array_to_duplicated_f(self) -> None:

        array = np.array([
                [None, None, None, 32, 17, 17],
                [2,2,2,False,'q','q'],
                [2,2,2,False,'q','q'],
                ], dtype=object)

        post1 = array_to_duplicated(
                array,
                exclude_first=False,
                exclude_last=False
                )
        self.assertEqual(post1.tolist(),
            [False, True, True])

        post2 = array_to_duplicated(
                array,
                exclude_first=True,
                exclude_last=False
                )
        self.assertEqual(post2.tolist(),
            [False, False, True])

        post3 = array_to_duplicated(
                array,
                exclude_first=False,
                exclude_last=True
                )
        self.assertEqual(post3.tolist(),
            [False, True, False])

        post4 = array_to_duplicated(
                array,
                exclude_first=True,
                exclude_last=True
                )
        self.assertEqual(post4.tolist(),
            [False, False, False])




    def test_array_to_duplicated_g(self) -> None:

        array = np.array([
                [None, None, None, 32, 17, 17],
                [2,2,2,False,'q','q'],
                [2,2,2,False,'q','q'],
                ], dtype=object)

        post1 = array_to_duplicated(
                array,
                axis=1,
                exclude_first=False,
                exclude_last=False
                )
        self.assertEqual(post1.tolist(),
            [True, True, True, False, True, True])

        post2 = array_to_duplicated(
                array,
                axis=1,
                exclude_first=True,
                exclude_last=False
                )
        self.assertEqual(post2.tolist(),
            [False, True, True, False, False, True])

        post3 = array_to_duplicated(
                array,
                axis=1,
                exclude_first=False,
                exclude_last=True
                )
        self.assertEqual(post3.tolist(),
            [True, True, False, False, True, False])

        post4 = array_to_duplicated(
                array,
                axis=1,
                exclude_first=True,
                exclude_last=True
                )
        self.assertEqual(post4.tolist(),
            [False, True, False, False, False, False])




    def test_array_set_ufunc_many_a(self) -> None:

        # this shows that identical arrays return the same ordering
        a1 = np.array([3, 2, 1])
        a2 = np.array([3, 2, 1])
        a3 = np.array([3, 2, 1])
        a4 = np.array([3, 2, 1])

        post = ufunc_set_iter((a1, a2, a3, a4), union=False, assume_unique=True)
        self.assertEqual(post.tolist(), [3, 2, 1])

        post = ufunc_set_iter((a1, a2, a3, a4), union=True, assume_unique=True)
        self.assertEqual(post.tolist(), [3, 2, 1])


    def test_array_set_ufunc_many_b(self) -> None:
        a1 = np.array([3, 2, 1])
        a2 = np.array([3, 2])
        a3 = np.array([5, 3, 2, 1])
        a4 = np.array([2])

        post = ufunc_set_iter((a1, a2, a3, a4), union=False, assume_unique=True)
        self.assertEqual(post.tolist(), [2])

        post = ufunc_set_iter((a1, a2, a3, a4), union=True, assume_unique=True)
        self.assertEqual(post.tolist(), [1, 2, 3, 5])


    def test_array_set_ufunc_many_c(self) -> None:
        a1 = np.array([[3, 2, 1], [1, 2, 3]])
        a2 = np.array([[5, 2, 1], [1, 2, 3]])
        a3 = np.array([[10, 20, 30], [1, 2, 3]])

        post = ufunc_set_iter((a1, a2, a3), union=False)
        self.assertEqual(post.tolist(), [[1, 2, 3]])

        post = ufunc_set_iter((a1, a2, a3), union=True)
        self.assertEqual(post.tolist(),
                [[1, 2, 3], [3, 2, 1], [5, 2, 1], [10, 20, 30]])


    def test_array_set_ufunc_many_d(self) -> None:
        a1 = np.array([3, 2, 1])
        a2 = np.array([[5, 2, 1], [1, 2, 3]])

        with self.assertRaises(Exception):
            post = ufunc_set_iter((a1, a2), union=False)


    def test_array_set_ufunc_many_e(self) -> None:
        a1 = np.array([3, 2, 1])
        a2 = np.array([30, 20])

        post = ufunc_set_iter((a1, a2), union=False)
        self.assertEqual(post.tolist(), [])


    def test_union1d_a(self) -> None:
        a1 = np.array([3, 2, 1])
        a2 = np.array(['3', '2', '1'])

        # need to avoid this
        # ipdb> np.union1d(a1, a2)                                                             # array(['1', '2', '3'], dtype='<U21')
        self.assertEqual(set(union1d(a1, a2)),
                {1, 2, 3, '2', '1', '3'}
                )

        self.assertEqual(
                union1d(np.array(['a', 'b', 'c']), np.array(['aaa', 'bbb', 'ccc'])).tolist(),
                ['a', 'aaa', 'b', 'bbb', 'c', 'ccc']
                )

        self.assertEqual(
                set(union1d(np.array([1, 2, 3]), np.array([None, False]))),
                {False, 2, 3, None, 1}
                )

        self.assertEqual(
                set(union1d(np.array([False, True]), np.array([None, 'a']))),
                {False, True, None, 'a'}
                )

        self.assertEqual(set(union1d(np.array([None, 1, 'd']), np.array([None, 3, 'ff']))),
                {'d', 1, 3, None, 'ff'}
                )


    def test_union1d_b(self) -> None:
        a1 = np.array([False, True, False])
        a2 = np.array([2, 3])
        self.assertEqual(union1d(a1, a2).tolist(),
                [False, True, 2, 3])

    def test_union1d_c(self) -> None:
        a1 = np.array([])
        a2 = np.array([9007199254740993], dtype=np.uint64)

        # if we cannot asume unique, the result is a rounded float
        self.assertEqual(union1d(a1, a2, assume_unique=True).tolist(),
                [9007199254740993])


    def test_intersect1d_a(self) -> None:

        a1 = np.array([3, 2, 1])
        a2 = np.array(['3', '2', '1'])

        self.assertEqual(len(intersect1d(a1, a2)), 0)

        self.assertEqual(
                len(intersect1d(np.array([1, 2, 3]), np.array([None, False]))), 0)

        self.assertEqual(
                set(intersect1d(np.array(['a', 'b', 'c']), np.array(['aa', 'bbb', 'c']))),
                {'c'}
                )

    def test_intersect1d_b(self) -> None:
        # long way of
        a1 = np.empty(4, dtype=object)
        a1[:] = [(0, 0), (0, 1), (0, 2), (0, 3)]

        a2 = np.empty(3, dtype=object)
        a2[:] = [(0, 1), (0, 3), (4, 5)]

        # must get an array of tuples back
        post = intersect1d(a1, a2)
        self.assertEqual(post.tolist(),
                [(0, 1), (0, 3)])



    def test_union2d_a(self) -> None:
        a1 = np.array([[3, 1], [0, 1]])
        a2 = np.array([[3, 1], [0, 1]])

        post1 = union2d(a1, a2, assume_unique=True)
        self.assertEqual(post1.tolist(),
                [[3, 1], [0, 1]])

        # result will get sorted
        post2 = union2d(a1, a2, assume_unique=False)
        self.assertEqual(post2.tolist(),
                [[0, 1], [3, 1]])


    def test_union2d_b(self) -> None:
        a1 = np.array([[3, 1], [0, 1]])
        a2 = np.array([['3', '1'], ['0', '1']])

        post1 = union2d(a1, a2, assume_unique=True)
        self.assertEqual(
                set(tuple(x) for x in post1),
                set(((0, 1), ('0', '1'), (3, 1), ('3', '1')))
                )

    def test_union2d_c(self) -> None:
        a1 = np.array([[3, 1], [0, 1]])
        a2 = np.array([[3, 1], [10, 20]])

        post1 = union2d(a1, a2, assume_unique=True)
        self.assertEqual(
                set(tuple(x) for x in post1),
                set(((0, 1), (3, 1), (10, 20)))
                )

    def test_union2d_d(self) -> None:
        a1 = np.array([None, None], dtype=object)
        a1[:] = ((3, 1), (20, 10))
        a2 = np.array([[3, 1], [10, 20]])


        post1 = union2d(a1, a2, assume_unique=True)
        self.assertEqual(
                set(tuple(x) for x in post1),
                set(((20, 10), (3, 1), (10, 20)))
                )



    def test_intersect2d_a(self) -> None:
        a = np.array([('a', 'b'), ('c', 'd'), ('e', 'f')])
        b = np.array([('a', 'g'), ('c', 'd'), ('e', 'f')])

        post = intersect2d(a, b)
        self.assertEqual([list(x) for x in post],
                [['c', 'd'], ['e', 'f']]
                )

        post = intersect2d(a.astype(object), b.astype(object))
        self.assertEqual([list(x) for x in post],
                [['c', 'd'], ['e', 'f']]
                )

        post = union2d(a, b)
        self.assertEqual([list(x) for x in post],
                [['a', 'b'], ['a', 'g'], ['c', 'd'], ['e', 'f']]
                )
        post = union2d(a.astype(object), b.astype(object))
        self.assertEqual([list(x) for x in post],
                [['a', 'b'], ['a', 'g'], ['c', 'd'], ['e', 'f']]
                )


    def test_intersect2d_b(self) -> None:
        a1 = np.array([None, None], dtype=object)
        a1[:] = ((3, 1), (20, 10))
        a2 = np.array([[3, 1], [10, 20]])

        post1 = intersect2d(a1, a2, assume_unique=True)
        self.assertEqual(
                set(tuple(x) for x in post1),
                set(((3, 1),))
                )


    def test_intersect2d_c(self) -> None:
        a1 = np.array([None, None], dtype=object)
        a1[:] = ((3, 1), (20, 10))

        a2 = np.array([None, None], dtype=object)
        a2[:] = ((3, 1), (1, 2))

        post1 = intersect2d(a1, a2)
        self.assertEqual(
                set(tuple(x) for x in post1),
                set(((3, 1),))
                )


    #---------------------------------------------------------------------------
    def test_isin_non_empty(self) -> None:
        # Tests isin's ability to fallback to numpy's isin when the UnHashable types are present in either the frame itself or the iterable being compared against
        '''
        Each test in the matrix is run for both 1D and 2D arrays
        ----------------------------------------------------
        |   Matrix  |  All Match | Some Match | None Match |
        |---------------------------------------------------
        | None Hash |      .     |      .     |     .      |
        | Some Hash |      .     |      .     |     .      |
        |  All Hash |      .     |      .     |     .      |
        ----------------------------------------------------
        '''
        a_1 = np.array([UnHashable(1), UnHashable(2), UnHashable(3), UnHashable(4)])
        a_2 = np.array([UnHashable(1), 2, UnHashable(3), 4])
        a_3 = np.array([1, 2, 3, 4])

        # All
        match_all_s1 = [UnHashable(1), UnHashable(2), UnHashable(3), UnHashable(4)]
        match_all_s2 = (UnHashable(1), 2, UnHashable(3), 4)
        match_all_s3 = np.array([1, 2, 3, 4])
        expected_match_all = np.array([True, True, True, True])
        # 1D
        self.assertTrue(np.array_equal(expected_match_all, isin(a_1, match_all_s1)))
        self.assertTrue(np.array_equal(expected_match_all, isin(a_2, match_all_s2)))
        self.assertTrue(np.array_equal(expected_match_all, isin(a_3, match_all_s3)))
        # 2D
        self.assertTrue(np.array_equal(expected_match_all.reshape(2,2), isin(a_1.reshape(2, 2), match_all_s1)))
        self.assertTrue(np.array_equal(expected_match_all.reshape(2,2), isin(a_2.reshape(2, 2), match_all_s2)))
        self.assertTrue(np.array_equal(expected_match_all.reshape(2,2), isin(a_3.reshape(2, 2), match_all_s3)))

        # Some
        match_some_s1 = (UnHashable(1), UnHashable(20), UnHashable(30), UnHashable(4))
        match_some_s2 = np.array([UnHashable(1), 20, UnHashable(30), 4])
        match_some_s3 = [1, 20, 30, 4]
        expected_match_some = np.array([True, False, False, True])
        # 1D
        self.assertTrue(np.array_equal(expected_match_some, isin(a_1, match_some_s1)))
        self.assertTrue(np.array_equal(expected_match_some, isin(a_2, match_some_s2)))
        self.assertTrue(np.array_equal(expected_match_some, isin(a_3, match_some_s3)))
        # 2D
        self.assertTrue(np.array_equal(expected_match_some.reshape(2,2), isin(a_1.reshape(2, 2), match_some_s1)))
        self.assertTrue(np.array_equal(expected_match_some.reshape(2,2), isin(a_2.reshape(2, 2), match_some_s2)))
        self.assertTrue(np.array_equal(expected_match_some.reshape(2,2), isin(a_3.reshape(2, 2), match_some_s3)))

        # None
        match_none_s1 = np.array([UnHashable(10), UnHashable(20), UnHashable(30), UnHashable(40)])
        match_none_s2 = [UnHashable(10), 20, UnHashable(30), 40]
        match_none_s3 = (10, 20, 30, 40)
        expected_match_none = np.array([False, False, False, False])
        # 1D
        self.assertTrue(np.array_equal(expected_match_none, isin(a_1, match_none_s1)))
        self.assertTrue(np.array_equal(expected_match_none, isin(a_2, match_none_s2)))
        self.assertTrue(np.array_equal(expected_match_none, isin(a_3, match_none_s3)))
        # 2D
        self.assertTrue(np.array_equal(expected_match_none.reshape(2,2), isin(a_1.reshape(2, 2), match_none_s1)))
        self.assertTrue(np.array_equal(expected_match_none.reshape(2,2), isin(a_2.reshape(2, 2), match_none_s2)))
        self.assertTrue(np.array_equal(expected_match_none.reshape(2,2), isin(a_3.reshape(2, 2), match_none_s3)))

    def test_isin_empty(self) -> None:
        arr = np.array([1, 2, 3, 4])
        expected = np.array([False, False, False, False])

        # 1D
        self.assertTrue(np.array_equal(expected, isin(arr, tuple())))
        self.assertTrue(np.array_equal(expected, isin(arr, [])))
        self.assertTrue(np.array_equal(expected, isin(arr, np.array([]))))
        # 2D
        self.assertTrue(np.array_equal(expected.reshape(2,2), isin(arr.reshape(2,2), tuple())))
        self.assertTrue(np.array_equal(expected.reshape(2,2), isin(arr.reshape(2,2), [])))
        self.assertTrue(np.array_equal(expected.reshape(2,2), isin(arr.reshape(2,2), np.array([]))))

    def test_isin_1d(self) -> None:
        arr_1d = np.array([1, 2, 3, 4, 5])

        s1 = frozenset({1, 3, 4})
        expected = np.array([True, False, True, True, False])
        self.assertTrue(np.array_equal(expected, _isin_1d(arr_1d, s1)))

        s2 = frozenset({7, 8, 9})
        expected = np.array([False, False, False, False, False])
        self.assertTrue(np.array_equal(expected, _isin_1d(arr_1d, s2)))

        s3 = frozenset({1, 2, 3, 4, 5})
        expected = np.array([True, True, True, True, True])
        self.assertTrue(np.array_equal(expected, _isin_1d(arr_1d, s3)))

        arr_2d = np.array( [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        with self.assertRaises(TypeError):
            _isin_1d(arr_2d, s3)

    def test_isin_2d(self) -> None:
        arr_2d = np.array( [[1, 2, 3], [4, 5, 6], [7, 8, 9]])

        s1 = frozenset({1, 3, 4, 9})
        expected = np.array([[True, False, True], [True, False, False], [False, False, True]])
        self.assertTrue(np.array_equal(expected, _isin_2d(arr_2d, s1)))

        s2 = frozenset({10, 11, 12})
        expected = np.array([[False, False, False], [False, False, False], [False, False, False]])
        self.assertTrue(np.array_equal(expected, _isin_2d(arr_2d, s2)))

        s3 = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9})
        expected = np.array([[True, True, True], [True, True, True], [True, True, True]])
        self.assertTrue(np.array_equal(expected, _isin_2d(arr_2d, s3)))

        arr_1d = np.array([1, 2, 3, 4, 5])
        with self.assertRaises(ValueError):
            _isin_2d(arr_1d, s3)



    #---------------------------------------------------------------------------

    @unittest.skip('requires network')
    def test_read_url(self) -> None:
        url = 'https://jsonplaceholder.typicode.com/todos'
        post = _read_url(url)


    def test_slice_to_ascending_slice_a(self) -> None:

        a1 = np.arange(10)

        def compare(slc: slice) -> None:
            slc_asc = slice_to_ascending_slice(slc, len(a1))
            self.assertEqual(sorted(a1[slc]), list(a1[slc_asc]))

        compare(slice(4,))
        compare(slice(6, 1, -1))
        compare(slice(6, 1, -2))
        compare(slice(6, None, -3))
        compare(slice(6, 2, -2))
        compare(slice(None, 1, -1))


    def test_array_shift_a(self) -> None:
        a1 = np.arange(6)


        self.assertEqual(array_shift(array=a1, shift=2, axis=0, wrap=True).tolist(),
                [4, 5, 0, 1, 2, 3])
        self.assertEqual(array_shift(array=a1, shift=-2, axis=0, wrap=True).tolist(),
                [2, 3, 4, 5, 0, 1])

        self.assertEqual(array_shift(array=a1, shift=5, axis=0, wrap=True).tolist(),
                [1, 2, 3, 4, 5, 0])

        self.assertEqual(
                array_shift(array=a1, shift=2, axis=0, wrap=False, fill_value=-1).tolist(),
                [-1, -1, 0, 1, 2, 3])

        self.assertEqual(
                array_shift(array=a1, shift=2, axis=0, wrap=False, fill_value=1.5).tolist(),
                [1.5, 1.5, 0, 1, 2, 3])

        self.assertEqual(
                array_shift(array=a1, shift=-2, axis=0, wrap=False, fill_value=1.5).tolist(),
                [2, 3, 4, 5, 1.5, 1.5])


    def test_array_shift_b(self) -> None:
        a1 = np.array([('a', 'b', 'e', 'd'),
                ('c', 'd', 'f', 'w'),
                ('e', 'f', 's', 'q')])

        self.assertEqual(array_shift(array=a1, shift=2, axis=0, wrap=True).tolist(),
                [['c', 'd', 'f', 'w'], ['e', 'f', 's', 'q'], ['a', 'b', 'e', 'd']])

        self.assertEqual(array_shift(array=a1, shift=-2, axis=0, wrap=True).tolist(),
                [['e', 'f', 's', 'q'], ['a', 'b', 'e', 'd'], ['c', 'd', 'f', 'w']])


        self.assertEqual(
                array_shift(array=a1, shift=-2, axis=0, wrap=False, fill_value='XX').dtype,
                np.dtype('<U2')
                )

        self.assertEqual(
                array_shift(array=a1, shift=-2, axis=0, wrap=False, fill_value='XX').tolist(),
                [['e', 'f', 's', 'q'],
                ['XX', 'XX', 'XX', 'XX'],
                ['XX', 'XX', 'XX', 'XX']])

        self.assertEqual(
                array_shift(array=a1, shift=2, axis=1, wrap=False, fill_value='XX').tolist(),
                [['XX', 'XX', 'a', 'b'],
                ['XX', 'XX', 'c', 'd'],
                ['XX', 'XX', 'e', 'f']])

        self.assertEqual(
                array_shift(array=a1, shift=-2, axis=1, wrap=False, fill_value='XX').tolist(),
                [['e', 'd', 'XX', 'XX'],
                ['f', 'w', 'XX', 'XX'],
                ['s', 'q', 'XX', 'XX']])


    def test_array_shift_c(self) -> None:
        a1 = np.arange(6)
        post = array_shift(array=a1, shift=0, axis=0, wrap=False)
        self.assertEqual(a1.tolist(), post.tolist())


    def test_ufunc_skipna_1d_a(self) -> None:

        a1 = np.array([
                (2, 2, 3, 4.23, np.nan),
                (30, 34, None, 80.6, 90.123),
                ], dtype=object)

        a2 = ufunc_axis_skipna(array=a1,
                skipna=True,
                axis=0,
                ufunc=np.sum,
                ufunc_skipna=np.nansum
                )
        self.assertEqual(a2.tolist(),
                [32, 36, 3, 84.83, 90.123])

        a3 = ufunc_axis_skipna(array=a1,
                skipna=True,
                axis=1,
                ufunc=np.sum,
                ufunc_skipna=np.nansum
                )
        self.assertEqual(a3.tolist(),
                [11.23, 234.723]
                )


    def test_ufunc_skipna_1d_b(self) -> None:

        a1 = np.array((None, None), dtype=object)

        post = ufunc_axis_skipna(array=a1,
                skipna=True,
                axis=0,
                ufunc=np.sum,
                ufunc_skipna=np.nansum
                )
        self.assertTrue(np.isnan(post))


    def test_ufunc_unique_a(self) -> None:

        a1 = np.array([1, 1, 1, 2, 2])
        post = ufunc_unique(a1)
        assert isinstance(post, np.ndarray)
        self.assertEqual(post.tolist(), [1, 2])

        a2 = np.array([1, 1, 1, 2, 2], dtype=object)
        post = ufunc_unique(a2)
        assert isinstance(post, np.ndarray)
        self.assertEqual(post.tolist(), [1, 2])

        a3 = np.array([1, 'x', 1, None, 2], dtype=object)
        post = ufunc_unique(a3)
        # order is as used
        self.assertEqual(post.tolist(), [1, 'x', None, 2])


    def test_ufunc_unique_b(self) -> None:

        a1 = np.array([[1, 1], [1, 2], [1, 2]])
        post = ufunc_unique(a1)
        assert isinstance(post, np.ndarray)
        self.assertEqual(post.tolist(), [1, 2])

        post = ufunc_unique(a1, axis=0)
        assert isinstance(post, np.ndarray)
        self.assertEqual(post.tolist(), [[1, 1], [1, 2]])

        post = ufunc_unique(a1, axis=1)
        assert isinstance(post, np.ndarray)
        self.assertEqual(post.tolist(), [[1, 1], [1, 2], [1, 2]])


    def test_ufunc_unique_c(self) -> None:

        a1 = np.array([[1, 'x', 1], [1, None, 1], [1, 'x', 1]], dtype=object)

        post = ufunc_unique(a1)
        self.assertEqual(post.tolist(), [1, 'x', None])

        post = ufunc_unique(a1, axis=0)
        self.assertEqual(post.tolist(), [(1, 'x', 1), (1, None, 1)])

        post = ufunc_unique(a1, axis=1)
        self.assertEqual(post.tolist(), [(1, 1, 1), ('x', None, 'x')])


    def test_concat_resolved_a(self) -> None:
        a1 = np.array([[3,4,5],[0,0,0]])
        a2 = np.array([1,2,3]).reshape((1,3))
        a3 = np.array([('3', '4', '5'),('1','1','1')])
        a4 = np.array(['3', '5'])
        a5 = np.array([1, 1, 1])

        post = concat_resolved((a1, a3))
        self.assertEqual(
                post.tolist(),
                [[3, 4, 5], [0, 0, 0], ['3', '4', '5'], ['1', '1', '1']]
                )

        post = concat_resolved((a3, a1, a2))
        self.assertEqual(post.tolist(),
                [['3', '4', '5'], ['1', '1', '1'], [3, 4, 5], [0, 0, 0], [1, 2, 3]])

        self.assertEqual(concat_resolved((a1, a3), axis=1).tolist(),
                [[3, 4, 5, '3', '4', '5'], [0, 0, 0, '1', '1', '1']]
                )

        self.assertEqual(concat_resolved((a4, a5)).tolist(),
                ['3', '5', 1, 1, 1])


    def test_concat_resolved_b(self) -> None:
        a1 = np.array([[3,4,5],[0,0,0]])
        a2 = np.array([1,2,3]).reshape((1,3))

        with self.assertRaises(Exception):
            concat_resolved((a1, a2), axis=None)  # type: ignore


    def test_dtype_to_na_a(self) -> None:

        self.assertEqual(dtype_to_na(np.dtype(int)), 0)
        self.assertTrue(np.isnan(dtype_to_na(np.dtype(float))))
        self.assertEqual(dtype_to_na(np.dtype(bool)), False)
        self.assertEqual(dtype_to_na(np.dtype(object)), None)
        self.assertEqual(dtype_to_na(np.dtype(str)), '')

        with self.assertRaises(NotImplementedError):
            _ = dtype_to_na(np.dtype('V'))

    #---------------------------------------------------------------------------

    def test_key_to_datetime_key_a(self) -> None:

        post = key_to_datetime_key(slice('2018-01-01', '2019-01-01'))  # type: ignore  # https://github.com/python/typeshed/pull/3024
        self.assertEqual(post,
                slice(np.datetime64('2018-01-01'),
                np.datetime64('2019-01-01'), None))

        post = key_to_datetime_key(np.datetime64('2019-01-01'))
        self.assertEqual(post, np.datetime64('2019-01-01'))

        post = key_to_datetime_key('2019-01-01')
        self.assertEqual(post, np.datetime64('2019-01-01'))

        a1 = np.array(('2019-01-01'), dtype='M')
        post = key_to_datetime_key(a1)
        self.assertEqual(post, a1)

        post = key_to_datetime_key(np.array(['2018-01-01', '2019-01-01']))
        a2 = np.array(['2018-01-01', '2019-01-01'], dtype='datetime64[D]')
        assert isinstance(post, np.ndarray)
        self.assertEqual(post.tolist(), a2.tolist())

        post = key_to_datetime_key(['2018-01-01', '2019-01-01'])
        a3 = np.array(['2018-01-01', '2019-01-01'], dtype='datetime64[D]')
        assert isinstance(post, np.ndarray)
        self.assertEqual(post.tolist(), a3.tolist())

        post = key_to_datetime_key(['2018-01', '2019-01'])
        a4 = np.array(['2018-01', '2019-01'], dtype='datetime64[M]')
        assert isinstance(post, np.ndarray)
        self.assertEqual(post.tolist(), a4.tolist())


        post = key_to_datetime_key(str(x) for x in range(2012, 2015))
        a5 = np.array(['2012', '2013', '2014'], dtype='datetime64[Y]')
        assert isinstance(post, np.ndarray)
        self.assertEqual(post.tolist(), a5.tolist())

        post = key_to_datetime_key(None)
        self.assertEqual(post, None)

    def test_key_to_datetime_key_b(self) -> None:

        d = datetime.datetime(2018, 2, 1, 5, 40)
        self.assertEqual(key_to_datetime_key(d), np.datetime64(d))
        self.assertEqual(key_to_datetime_key(d.date()), np.datetime64(d.date()))

    #---------------------------------------------------------------------------

    def test_set_ufunc2d_a(self) -> None:
        # fails due wrong function
        a1 = np.array([1, 1, 1])
        with self.assertRaises(NotImplementedError):
            _ufunc_set_2d(np.sum, a1, a1)


    def test_set_ufunc2d_b(self) -> None:

        a1 = np.array([['a', 'b'], ['b', 'c']])
        a2 = np.array([['b', 'cc'], ['dd', 'ee']])

        post = _ufunc_set_2d(np.union1d, a1, a2)
        self.assertEqual(len(post), 4)
        self.assertEqual(str(post.dtype), '<U2')

        post = _ufunc_set_2d(np.union1d, a2, a1)
        self.assertEqual(len(post), 4)
        self.assertEqual(str(post.dtype), '<U2')

    def test_set_ufunc2d_c(self) -> None:

        # these values, as tuples, are equivalent and hash to the same value in Python, thus we get one result
        a1 = np.array([[False]])
        a2 = np.array([[0]])

        post = _ufunc_set_2d(np.union1d, a1, a2)
        self.assertEqual(post.tolist(), [(False,)])


    def test_set_ufunc2d_d(self) -> None:
        a1 = np.array([[3], [2], [1]])
        a2 = np.array([[30], [20], [2], [1]])

        post1 = _ufunc_set_2d(np.union1d, a1, a2)
        self.assertEqual(post1.tolist(),
                [[1], [2], [3], [20], [30]])

        post2 = _ufunc_set_2d(np.intersect1d, a1, a2)
        self.assertEqual(post2.tolist(),
                [[1], [2]])


    def test_set_ufunc2d_e(self) -> None:

        a1 = np.array([[0, 1], [-1, -2]])
        a2 = np.array([])

        post1 = _ufunc_set_2d(np.union1d, a1, a2, assume_unique=True)
        self.assertEqual(id(a1), id(post1))

        post2 = _ufunc_set_2d(np.union1d, a2, a1, assume_unique=True)
        self.assertEqual(id(a1), id(post2))



    def test_set_ufunc2d_f(self) -> None:

        a1 = np.array([[0, 1], [-1, -2]])
        a2 = np.array([])

        # intersect with 0 results in 0
        post1 = _ufunc_set_2d(np.intersect1d, a1, a2)
        self.assertEqual(len(post1), 0)

        post2 = _ufunc_set_2d(np.intersect1d, a2, a1)
        self.assertEqual(len(post2), 0)



    def test_ufunc_set_2d_g(self) -> None:
        post1 = _ufunc_set_2d(np.union1d,
                np.arange(4).reshape((2, 2)),
                np.arange(4).reshape((2, 2)),
                assume_unique=True)

        self.assertEqual(post1.tolist(),
                [[0, 1], [2, 3]])


    def test_ufunc_set_2d_h(self) -> None:
        with self.assertRaises(RuntimeError):
            post1 = _ufunc_set_2d(np.union1d,
                    np.arange(4).reshape((2, 2)),
                    np.arange(4),
                    assume_unique=True)



    #---------------------------------------------------------------------------



    def test_to_timedelta64_a(self) -> None:
        timedelta = datetime.timedelta

        self.assertEqual(
                to_timedelta64(timedelta(days=4)),
                np.timedelta64(4, 'D'))

        self.assertEqual(
                to_timedelta64(timedelta(seconds=4)),
                np.timedelta64(4, 's'))

        self.assertEqual(
                to_timedelta64(timedelta(minutes=4)),
                np.timedelta64(240, 's'))

    def test_binary_transition_a(self) -> None:
        a1 = np.array([False, True, True, False, False, True, True, False])
        self.assertEqual(binary_transition(a1).tolist(), [0, 3, 4, 7])

        a1 = np.array([False, False, True, False, True, True, True, True])
        self.assertEqual(binary_transition(a1).tolist(), [1, 3])


        a1 = np.array([True, False, True])
        self.assertEqual(binary_transition(a1).tolist(), [1])

        a1 = np.array([False, True, False])
        self.assertEqual(binary_transition(a1).tolist(), [0, 2])

        a1 = np.array([True])
        self.assertEqual(binary_transition(a1).tolist(), [])

        a1 = np.array([False])
        self.assertEqual(binary_transition(a1).tolist(), [])

        a1 = np.array([False, True])
        self.assertEqual(binary_transition(a1).tolist(), [0])

        a1 = np.array([True, False])
        self.assertEqual(binary_transition(a1).tolist(), [1])


    def test_binary_transition_b(self) -> None:
        # return index per axis (column or row) at False values where False was True, or will be True
        a1 = np.array([[False, False, True, False],
                       [True, False, True, False],
                       [False, False, False, True]
                       ])

        self.assertEqual(
                binary_transition(a1, axis=0).tolist(),
                [[0, 2], None, [2,], [1,]]
                )

        self.assertEqual(
                binary_transition(a1, axis=1).tolist(),
                [[1, 3], [1, 3], [2,]]
                )

    def test_binary_transition_c(self) -> None:
        # return index per axis (column or row) at False values where False was True, or will be True
        a1 = np.array([[False, False, True, False],
                       [True, False, True, False],
                       [True, False, True, False],
                       [True, False, False, True],
                       [False, False, False, True]
                       ])

        self.assertEqual(
                binary_transition(a1, axis=0).tolist(),
                [[0, 4], None, [3,], [2,]]
                )

        self.assertEqual(
                binary_transition(a1, axis=1).tolist(),
                [[1, 3], [1, 3], [1, 3], [1, 2], [2,]]
                )


    def test_binary_transition_d(self) -> None:
        with self.assertRaises(NotImplementedError):
            binary_transition(np.arange(12).reshape((2, 2, 3)), 0)


    #---------------------------------------------------------------------------

    def test_roll_1d_a(self) -> None:

        a1 = np.arange(12)

        for i in range(len(a1) + 1):
            post = roll_1d(a1, i)
            self.assertEqual(post.tolist(), np.roll(a1, i).tolist())

            post = roll_1d(a1, -i)
            self.assertEqual(post.tolist(), np.roll(a1, -i).tolist())

    def test_roll_1d_b(self) -> None:
        post = roll_1d(np.array([]), -4)
        self.assertEqual(len(post), 0)


    def test_roll_1d_c(self) -> None:
        a1 = np.array([3, 4, 5, 6])
        self.assertEqual(roll_1d(a1, 1).tolist(), [6, 3, 4, 5])
        self.assertEqual(roll_1d(a1, -1).tolist(), [4, 5, 6, 3])

    #---------------------------------------------------------------------------

    def test_roll_2d_a(self) -> None:

        a1 = np.arange(12).reshape((3,4))

        for i in range(a1.shape[0] + 1):
            post = roll_2d(a1, i, axis=0)
            self.assertEqual(post.tolist(), np.roll(a1, i, axis=0).tolist())

            post = roll_2d(a1, -i, axis=0)
            self.assertEqual(post.tolist(), np.roll(a1, -i, axis=0).tolist())

        for i in range(a1.shape[1] + 1):
            post = roll_2d(a1, i, axis=1)
            self.assertEqual(post.tolist(), np.roll(a1, i, axis=1).tolist())

            post = roll_2d(a1, -i, axis=1)
            self.assertEqual(post.tolist(), np.roll(a1, -i, axis=1).tolist())

    def test_roll_2d_b(self) -> None:
        post = roll_2d(np.array([[]]), -4, axis=1)
        self.assertEqual(post.shape, (1, 0))


    def test_roll_2d_c(self) -> None:

        a1 = np.arange(12).reshape((3,4))

        self.assertEqual(roll_2d(a1, -2, axis=0).tolist(),
                [[8, 9, 10, 11], [0, 1, 2, 3], [4, 5, 6, 7]])

        self.assertEqual(roll_2d(a1, -2, axis=1).tolist(),
                [[2, 3, 0, 1], [6, 7, 4, 5], [10, 11, 8, 9]])

    def test_roll_2d_d(self) -> None:

        a1 = np.arange(6).reshape((2, 3))

        self.assertEqual(roll_2d(a1, 1, axis=1).tolist(),
                [[2, 0, 1], [5, 3, 4]])
        self.assertEqual(roll_2d(a1, -1, axis=1).tolist(),
                [[1, 2, 0], [4, 5, 3]])


    def test_roll_2d_e(self) -> None:

        a1 = np.arange(6).reshape((3, 2))

        self.assertEqual(roll_2d(a1, 1, axis=0).tolist(),
                [[4, 5], [0, 1], [2, 3]]
                )
        self.assertEqual(roll_2d(a1, -1, axis=0).tolist(),
                [[2, 3], [4, 5], [0, 1]]
                )


    def test_roll_2d_f(self) -> None:

        with self.assertRaises(NotImplementedError):
            roll_2d(np.arange(4).reshape((2, 2)), 1, axis=2)

    #---------------------------------------------------------------------------


    def test_to_datetime64_a(self) -> None:

        dt = to_datetime64('2019')
        self.assertEqual(dt, np.datetime64('2019'))

        dt = to_datetime64('2019', dtype=np.dtype('datetime64[D]'))
        self.assertEqual(dt, np.datetime64('2019-01-01'))

        dt = to_datetime64(np.datetime64('2019'), dtype=np.dtype('datetime64[Y]'))
        self.assertEqual(dt, np.datetime64('2019'))

        with self.assertRaises(RuntimeError):
            dt = to_datetime64(np.datetime64('2019'), dtype=np.dtype('datetime64[D]'))


    def test_to_datetime64_b(self) -> None:

        dt = to_datetime64(2019, _DT64_YEAR)
        self.assertEqual(dt, np.datetime64('2019'))

        with self.assertRaises(RuntimeError):
            _ = to_datetime64(2019, _DT64_DAY)



    def test_resolve_type_iter_a(self) -> None:

        v1 = ('a', 'b', 'c')
        resolved, has_tuple, values = resolve_type_iter(v1)
        self.assertEqual(resolved, None)

        v22 = ('a', 'b', 3)
        resolved, has_tuple, values = resolve_type_iter(v22)
        self.assertEqual(resolved, object)

        v3 = ('a', 'b', (1, 2))
        resolved, has_tuple, values = resolve_type_iter(v3)
        self.assertEqual(resolved, object)
        self.assertTrue(has_tuple)

        v4 = (1, 2, 4.3, 2)
        resolved, has_tuple, values = resolve_type_iter(v4)
        self.assertEqual(resolved, None)


        v5 = (1, 2, 4.3, 2, None)
        resolved, has_tuple, values = resolve_type_iter(v5)
        self.assertEqual(resolved, None)


        v6 = (1, 2, 4.3, 2, 'g')
        resolved, has_tuple, values = resolve_type_iter(v6)
        self.assertEqual(resolved, object)

        v7 = ()
        resolved, has_tuple, values = resolve_type_iter(v7)
        self.assertEqual(resolved, None)


    def test_resolve_type_iter_b(self) -> None:

        v1 = iter(('a', 'b', 'c'))
        resolved, has_tuple, values = resolve_type_iter(v1)
        self.assertEqual(resolved, None)

        v2 = iter(('a', 'b', 3))
        resolved, has_tuple, values = resolve_type_iter(v2)
        self.assertEqual(resolved, object)

        v3 = iter(('a', 'b', (1, 2)))
        resolved, has_tuple, values = resolve_type_iter(v3)
        self.assertEqual(resolved, object)
        self.assertTrue(has_tuple)

        v4 = range(4)
        resolved, has_tuple, values = resolve_type_iter(v4)
        self.assertEqual(resolved, None)


    def test_resolve_type_iter_c(self) -> None:

        a = [True, False, True]
        resolved, has_tuple, values = resolve_type_iter(a)
        self.assertEqual(id(a), id(values))

        resolved, has_tuple, values = resolve_type_iter(iter(a))
        self.assertNotEqual(id(a), id(values))

        self.assertEqual(resolved, None)
        self.assertEqual(has_tuple, False)


    def test_resolve_type_iter_d(self) -> None:

        a = [3, 2, (3,4)]
        resolved, has_tuple, values = resolve_type_iter(a)
        self.assertEqual(id(a), id(values))
        self.assertTrue(has_tuple)

        resolved, has_tuple, values = resolve_type_iter(iter(a))
        self.assertNotEqual(id(a), id(values))

        self.assertEqual(resolved, object)
        self.assertEqual(has_tuple, True)


    def test_resolve_type_iter_e(self) -> None:

        a = [300000000000000002, 5000000000000000001]
        resolved, has_tuple, values = resolve_type_iter(a)
        self.assertEqual(id(a), id(values))

        resolved, has_tuple, values = resolve_type_iter(iter(a))
        self.assertNotEqual(id(a), id(values))
        self.assertEqual(resolved, None)
        self.assertEqual(has_tuple, False)

    def test_resolve_type_iter_f(self) -> None:

        def a() -> tp.Iterator[tp.Any]:
            for i in range(3):
                yield i
            yield None

        resolved, has_tuple, values = resolve_type_iter(a())
        self.assertEqual(values, [0, 1, 2, None])
        self.assertEqual(resolved, None)
        self.assertEqual(has_tuple, False)

    def test_resolve_type_iter_g(self) -> None:

        def a() -> tp.Iterator[tp.Any]:
            yield None
            for i in range(3):
                yield i

        resolved, has_tuple, values = resolve_type_iter(a())
        self.assertEqual(values, [None, 0, 1, 2])
        self.assertEqual(resolved, None)
        self.assertEqual(has_tuple, False)

    def test_resolve_type_iter_h(self) -> None:

        def a() -> tp.Iterator[tp.Any]:
            yield 10
            yield None
            for i in range(3):
                yield i
            yield (3,4)

        resolved, has_tuple, values = resolve_type_iter(a())
        self.assertEqual(values, [10, None, 0, 1, 2, (3,4)])
        self.assertEqual(resolved, object)
        # we stop evaluation after finding object
        self.assertEqual(has_tuple, True)

        post = iterable_to_array_1d(a())
        self.assertEqual(post[0].tolist(),
                [10, None, 0, 1, 2, (3, 4)]
                )


    def test_resolve_type_iter_i(self) -> None:
        a0 = range(3, 7)
        resolved, has_tuple, values = resolve_type_iter(a0)
        # a copy is not made
        self.assertEqual(id(a0), id(values))
        self.assertEqual(resolved, None)

        post = iterable_to_array_1d(a0)
        self.assertEqual(post[0].tolist(),
                [3, 4, 5, 6])



    def test_resolve_type_iter_j(self) -> None:
        # this case was found through hypothesis
        a0 = [0.0, 36_028_797_018_963_969]
        resolved, has_tuple, values = resolve_type_iter(a0)
        self.assertEqual(resolved, object)



    def test_resolve_type_iter_k(self) -> None:
        resolved, has_tuple, values = resolve_type_iter((x for x in ())) #type: ignore
        self.assertEqual(resolved, None)
        self.assertEqual(len(values), 0)
        self.assertEqual(has_tuple, False)

    #---------------------------------------------------------------------------

    def test_iterable_to_array_a(self) -> None:
        a1, is_unique = iterable_to_array_1d({3,4,5})
        self.assertTrue(is_unique)
        self.assertEqual(set(a1.tolist()), {3,4,5})

        a2, is_unique = iterable_to_array_1d({None: 3, 'f': 4, 39: 0})
        self.assertTrue(is_unique)
        self.assertEqual(set(a2.tolist()), {None, 'f', 39})

        a3, is_unique = iterable_to_array_1d((x*10 for x in range(1,4)))
        self.assertFalse(is_unique)
        self.assertEqual(a3.tolist(), [10, 20, 30])

        a1, is_unique = iterable_to_array_1d({3,4,5}, dtype=np.dtype(int))
        self.assertEqual(set(a1.tolist()), {3,4,5})

        a1, is_unique = iterable_to_array_1d((3,4,5), dtype=np.dtype(object))
        self.assertTrue(a1.dtype == object)
        self.assertEqual(a1.tolist(), [3,4,5])

        x = [(0, 0), (0, 1), (0, 2), (0, 3)]
        a1, is_unique = iterable_to_array_1d(x, np.dtype(object))
        self.assertEqual(a1.tolist(), [(0, 0), (0, 1), (0, 2), (0, 3)])
        # must get an array of tuples back

        x = [(0, 0), (0, 1), (0, 2), (0, 3)]
        a1, is_unique = iterable_to_array_1d(iter(x))
        self.assertEqual(a1.tolist(), [(0, 0), (0, 1), (0, 2), (0, 3)])

        a4 = np.array([np.nan, 0j], dtype=object)
        post, _ = iterable_to_array_1d(a4)
        self.assertAlmostEqualValues(a4, post)


        self.assertEqual(iterable_to_array_1d((1, 1.1))[0].dtype,
                np.dtype('float64'))

        self.assertEqual(iterable_to_array_1d((1.1, 0, -29))[0].dtype,
                np.dtype('float64'))


    def test_iterable_to_array_b(self) -> None:

        iterable: tp.Iterable[tp.Any]

        for iterable in (  # type: ignore
                [1, 2, 3],
                dict(a=1, b=2, c=3).values(),
                dict(a=1, b=2, c=3).keys(),
                {1, 2, 3},
                frozenset((1, 2, 3)),
                ('a', 3, None),
                (1, 2, 'e', 1.1)
                ):

            a1, _ = iterable_to_array_1d(iterable)
            self.assertEqual(set(a1), set(iterable))

            a2, _ = iterable_to_array_1d(iter(iterable))
            self.assertEqual(set(a2), set(iterable))


    def test_iterable_to_array_c(self) -> None:

        iterable: tp.Iterable[tp.Any]

        for iterable, dtype in (  # type: ignore
                ([1, 2, 3], int),
                (dict(a=1, b=2, c=3).values(), int),
                (dict(a=1, b=2, c=3).keys(), str),
                ({1, 2, 3}, int),
                (frozenset((1, 2, 3)), int),
                (('a', 3, None), object),
                ((1, 2, 'e', 1.1), object),
                ):
            a1, _ = iterable_to_array_1d(iterable, dtype=dtype)
            self.assertEqual(set(a1), set(iterable))

            a2, _ = iterable_to_array_1d(iter(iterable), dtype=dtype)
            self.assertEqual(set(a2), set(iterable))


    def test_iterable_to_array_d(self) -> None:

        self.assertEqual(
                iterable_to_array_1d((True, False, True))[0].dtype,
                np.dtype('bool')
        )

        self.assertEqual(
                iterable_to_array_1d((0, 1, 0), dtype=bool)[0].dtype,
                np.dtype('bool')
        )

        self.assertEqual(
                iterable_to_array_1d((1, 2, 'w'))[0].dtype,
                np.dtype('O')
        )

        self.assertEqual(iterable_to_array_1d(((2,3), (3,2)))[0].tolist(),
                [(2, 3), (3, 2)]
        )


    def test_iterable_to_array_e(self) -> None:

        # this result is surprising but is a result of NumPy's array constructor
        post = iterable_to_array_1d('cat')
        self.assertEqual(post[0].tolist(), ['cat'])
        self.assertEqual(post[1], True)


    def test_iterable_to_array_f(self) -> None:


        post1, _ = iterable_to_array_1d([[3,],[4,]])
        self.assertEqual(post1.dtype, object)
        self.assertEqual(post1.ndim, 1)
        self.assertEqual(post1.tolist(), [[3], [4]])

        post2, _ = iterable_to_array_1d([[3,],[4,]], dtype=object)
        self.assertEqual(post2.dtype, object)
        self.assertEqual(post2.ndim, 1)
        self.assertEqual(post2.tolist(), [[3], [4]])



    def test_iterable_to_array_g(self) -> None:

        # this result is surprising but is a result of NumPy's array constructor
        with self.assertRaises(RuntimeError):
            _ = iterable_to_array_1d(np.array([None, None]), dtype=np.dtype(float))



    def test_iterable_to_array_h(self) -> None:

        sample = [10000000000000000000000]
        post = iterable_to_array_1d(sample, dtype=np.dtype(int))
        self.assertEqual(post[0].dtype, object)
        self.assertEqual(post[0].tolist(), sample)


    #---------------------------------------------------------------------------

    def test_iterable_to_array_2d_a(self) -> None:

        values1: tp.Iterable[tp.Iterable[tp.Any]] = [[3, 'a', 1, None], [4, 'b', 2, False]]
        post1 = iterable_to_array_2d(values1)
        self.assertEqual(post1.shape, (2, 4))
        self.assertEqual(post1.dtype, object)

        # this would return all string
        values2: tp.Iterable[tp.Iterable[tp.Any]] = [['a', 'b', 'c'], [1, 2, 3]]
        post2 = iterable_to_array_2d(values2)
        self.assertEqual(post2.shape, (2, 3))
        self.assertEqual(post2.dtype, object)

        values3: tp.Iterable[tp.Iterable[tp.Any]] = [[1, 3, 10], [1.1, 2.1, 3.4]]
        post3 = iterable_to_array_2d(values3)
        self.assertEqual(post3.shape, (2, 3))
        self.assertEqual(post3.dtype, np.float64)

    def test_iterable_to_array_2d_b(self) -> None:
        post = iterable_to_array_2d(np.arange(4).reshape((2, 2)))
        self.assertEqual(post.tolist(), [[0, 1], [2, 3]])

    def test_iterable_to_array_2d_c(self) -> None:
        with self.assertRaises(RuntimeError):
            # looks like a 2d array enough to get past type sampling
            post = iterable_to_array_2d(['asd', 'wer'])

    #---------------------------------------------------------------------------
    def test_argmin_1d_a(self) -> None:


        self.assertEqual(argmin_1d(np.array([3,-2,0,1])), 1)
        self.assertEqualWithNaN(argmin_1d(np.array([np.nan, np.nan])), np.nan)

        self.assertEqual(argmin_1d(np.array([np.nan,-2,0,1])), 1)

        self.assertEqualWithNaN(
                argmin_1d(np.array([np.nan,-2,0,1]), skipna=False), np.nan)


    def test_argmax_1d_a(self) -> None:
        self.assertEqual(argmax_1d(np.array([3,-2,0,1])), 0)
        self.assertEqualWithNaN(argmax_1d(np.array([np.nan, np.nan])), np.nan)

        self.assertEqual(argmax_1d(np.array([np.nan,-2,0,1])), 3)

        self.assertEqualWithNaN(
                argmax_1d(np.array([np.nan,-2,0,1]), skipna=False), np.nan)




    def test_argmin_2d_a(self) -> None:
        a1 = np.array([[1, 2, -1], [-1, np.nan, 20]])

        self.assertEqual(argmin_2d(a1, axis=1).tolist(),
                [2, 0]
                )

        self.assertAlmostEqualValues(
                argmin_2d(a1, axis=1, skipna=False).tolist(),
                [2, np.nan]
                )

        self.assertEqual(argmin_2d(a1, axis=0).tolist(),
                [1, 0, 0]
                )

        self.assertAlmostEqualValues(argmin_2d(a1, axis=0, skipna=False).tolist(),
                [1, np.nan, 0]
                )

    def test_argmin_2d_b(self) -> None:
        a1 = np.array([[np.nan, 2, -1], [-1, np.nan, 20]])

        self.assertAlmostEqualValues(
                argmin_2d(a1, axis=1, skipna=False).tolist(),
                [np.nan, np.nan]
                )

        self.assertAlmostEqualValues(
                argmin_2d(a1, axis=1, skipna=True).tolist(),
                [2, 0]
                )

    def test_argmax_2d_a(self) -> None:
        a1 = np.array([[1, 2, -1], [-1, np.nan, 20]])

        self.assertEqual(argmax_2d(a1, axis=1).tolist(),
                [1, 2]
                )

        self.assertAlmostEqualValues(
                argmax_2d(a1, axis=1, skipna=False).tolist(),
                [1, np.nan]
                )

        self.assertEqual(argmax_2d(a1, axis=0).tolist(),
                [0, 0, 1]
                )

        self.assertAlmostEqualValues(argmax_2d(a1, axis=0, skipna=False).tolist(),
                [0, np.nan, 1]
                )


    def test_column_1d_filter_a(self) -> None:
        a1 = np.arange(4)
        a2 = np.arange(4).reshape(4, 1)
        self.assertEqual(column_1d_filter(a1).shape, (4,))
        self.assertEqual(column_1d_filter(a2).shape, (4,))


    def test_row_1d_filter_a(self) -> None:
        a1 = np.arange(4)
        a2 = np.arange(4).reshape(1, 4)
        self.assertEqual(row_1d_filter(a1).shape, (4,))
        self.assertEqual(row_1d_filter(a2).shape, (4,))


    def test_array_to_duplicated_sortable_a(self) -> None:

        post1 = _array_to_duplicated_sortable(np.array([2, 3, 3, 3, 4]),
                exclude_first=True,
                exclude_last=True)
        self.assertEqual(post1.tolist(),
                [False, False, True, False, False])

        post2 = _array_to_duplicated_sortable(np.array([2, 3, 3, 3, 4]),
                exclude_first=False,
                exclude_last=True)
        self.assertEqual(post2.tolist(),
                [False, True, True, False, False])

        post3 = _array_to_duplicated_sortable(np.array([2, 3, 3, 3, 4]),
                exclude_first=True,
                exclude_last=False)
        self.assertEqual(post3.tolist(),
                [False, False, True, True, False])

        post4 = _array_to_duplicated_sortable(np.array([2, 3, 3, 3, 4]),
                exclude_first=False,
                exclude_last=False)
        self.assertEqual(post4.tolist(),
                [False, True, True, True, False])


    def test_ufunc_set_1d_a(self) -> None:
        with self.assertRaises(NotImplementedError):
            _ufunc_set_1d(np.any, np.arange(3), np.arange(3))


    def test_ufunc_set_1d_b(self) -> None:
        post1 = _ufunc_set_1d(np.union1d, np.arange(3), np.array(()), assume_unique=True)
        self.assertEqual(post1.tolist(), [0, 1, 2])

        post2 = _ufunc_set_1d(np.union1d, np.arange(3), np.arange(3), assume_unique=True)
        self.assertEqual(post1.tolist(), [0, 1, 2])


if __name__ == '__main__':
    unittest.main()
