
import unittest
from collections import OrderedDict
from io import StringIO
import string
import pickle
import typing as tp

import numpy as np

from static_frame.test.test_case import TestCase
from static_frame.test.test_case import temp_file

import static_frame as sf
# assuming located in the same directory
from static_frame import Index
from static_frame import IndexGO
from static_frame import Series
from static_frame import Frame
from static_frame import FrameGO
# from static_frame import TypeBlocks
# from static_frame import Display
from static_frame import mloc
from static_frame import DisplayConfig
from static_frame import IndexHierarchy
from static_frame import IndexHierarchyGO
from static_frame import IndexDate
from static_frame import IndexSecond
from static_frame import IndexYearMonth
from static_frame import IndexAutoFactory

from static_frame import HLoc

from static_frame.core.exception import AxisInvalid
from static_frame.core.exception import ErrorInitSeries

nan = np.nan

LONG_SAMPLE_STR = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'


class TestUnit(TestCase):

    #---------------------------------------------------------------------------
    # test series

    def test_series_slotted_a(self) -> None:
        s1 = Series.from_element(10, index=('a', 'b', 'c', 'd'))

        with self.assertRaises(AttributeError):
            s1.g = 30 #pylint: disable=E0237
        with self.assertRaises(AttributeError):
            s1.__dict__ #pylint: disable=W0104

    def test_series_init_a(self) -> None:
        s1 = Series.from_element(np.nan, index=('a', 'b', 'c', 'd'))

        self.assertTrue(s1.dtype == float)
        self.assertTrue(len(s1) == 4)

        s2 = Series.from_element(False, index=('a', 'b', 'c', 'd'))

        self.assertTrue(s2.dtype == bool)
        self.assertTrue(len(s2) == 4)

        s3 = Series.from_element(None, index=('a', 'b', 'c', 'd'))

        self.assertTrue(s3.dtype == object)
        self.assertTrue(len(s3) == 4)


    def test_series_init_b(self) -> None:
        s1 = Series(['a', 'b', 'c', 'd'], index=('a', 'b', 'c', 'd'))
        self.assertEqual(s1.to_pairs(),
                (('a', 'a'), ('b', 'b'), ('c', 'c'), ('d', 'd')))

        # testing direct specification of string type
        s2 = Series(['a', 'b', 'c', 'd'], index=('a', 'b', 'c', 'd'), dtype=str)
        self.assertEqual(s2.to_pairs(),
                (('a', 'a'), ('b', 'b'), ('c', 'c'), ('d', 'd')))

    def test_series_init_c(self) -> None:

        s1 = Series.from_dict(OrderedDict([('b', 4), ('a', 1)]), dtype=np.int64)
        self.assertEqual(s1.to_pairs(),
                (('b', 4), ('a', 1)))

    def test_series_init_d(self) -> None:
        # single element, when the element is a string
        s1 = Series.from_element('abc', index=range(4))
        self.assertEqual(s1.to_pairs(),
                ((0, 'abc'), (1, 'abc'), (2, 'abc'), (3, 'abc')))

        # this is an array with shape == (), or a single element
        s2 = Series(np.array('abc'), index=range(4))
        self.assertEqual(s2.to_pairs(),
                ((0, 'abc'), (1, 'abc'), (2, 'abc'), (3, 'abc')))

        # single element, generator index
        s3 = Series.from_element(None, index=(x * 10 for x in (1,2,3)))
        self.assertEqual(s3.to_pairs(),
                ((10, None), (20, None), (30, None))
                )

    def test_series_init_e(self) -> None:
        s1 = Series.from_dict(dict(a=1, b=2, c=np.nan, d=None), dtype=object)
        self.assertEqual(s1.to_pairs(),
                (('a', 1), ('b', 2), ('c', nan), ('d', None))
                )
        with self.assertRaises(ValueError):
            s1.values[1] = 23

    def test_series_init_f(self) -> None:
        s1 = Series.from_dict({'a': 'x', 'b': 'y', 'c': 'z'})
        self.assertEqual(s1.to_pairs(), (('a', 'x'), ('b', 'y'), ('c', 'z')))

    def test_series_init_g(self) -> None:
        with self.assertRaises(RuntimeError):
            s1 = Series(range(4), own_index=True, index=None)  # type: ignore

    def test_series_init_h(self) -> None:
        s1 = Series(range(4), index_constructor=IndexSecond)
        self.assertEqual(s1.to_pairs(),
            ((np.datetime64('1970-01-01T00:00:00'), 0),
            (np.datetime64('1970-01-01T00:00:01'), 1),
            (np.datetime64('1970-01-01T00:00:02'), 2),
            (np.datetime64('1970-01-01T00:00:03'), 3)))

    def test_series_init_i(self) -> None:
        s1 = Series((3, 4, 'a'))
        self.assertEqual(s1.values.tolist(),
                [3, 4, 'a']
                )

    def test_series_init_j(self) -> None:
        s1 = Series((3, 4, 'a'), index=IndexAutoFactory)
        self.assertEqual(s1.to_pairs(),
                ((0, 3), (1, 4), (2, 'a')))

    def test_series_init_k(self) -> None:
        s1 = Series.from_element('cat', index=(1, 2, 3))
        self.assertEqual(s1.to_pairs(),
                ((1, 'cat'), (2, 'cat'), (3, 'cat'))
                )

    def test_series_init_l(self) -> None:
        s1 = Series(([None], [1, 2], ['a', 'b']), index=(1, 2, 3))
        self.assertEqual(s1[2:].to_pairs(),
                ((2, [1, 2]), (3, ['a', 'b'])))
        self.assertEqual((s1 * 2).to_pairs(),
                ((1, [None, None]), (2, [1, 2, 1, 2]), (3, ['a', 'b', 'a', 'b']))
                )

    def test_series_init_m(self) -> None:

        # if index is None or IndexAutoFactory, we supply an index of 0
        s1 = Series.from_element('a', index=(0,))
        self.assertEqual(s1.to_pairs(),
                ((0, 'a'),))

        # an element with an explicitl empty index results in an empty series
        s2 = Series.from_element('a', index=())
        self.assertEqual(s2.to_pairs(), ())

    def test_series_init_n(self) -> None:
        with self.assertRaises(RuntimeError):
            s1 = Series(np.array([['a', 'b']]))

        s2 = Series([['a', 'b']], dtype=object)
        self.assertEqual(s2.to_pairs(),
            ((0, ['a', 'b']),)
            )

    def test_series_init_o(self) -> None:
        with self.assertRaises(ErrorInitSeries):
            s1 = Series('T', index=range(3))

        s1 = Series.from_element('T', index=())
        self.assertEqual(s1.to_pairs(), ())


    def test_series_init_p(self) -> None:
        # 3d array raises exception
        a1 = np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])
        with self.assertRaises(RuntimeError):
            s1 = Series(a1)


    def test_series_init_q(self) -> None:
        with self.assertRaises(RuntimeError):
            s1 = Series(dict(a=3, b=4))


    def test_series_init_r(self) -> None:
        with self.assertRaises(RuntimeError):
            s1 = Series(np.array((3, 4, 5)), dtype=object)


    def test_series_init_s(self) -> None:
        s1 = Series(np.array('a'))
        self.assertEqual(s1.to_pairs(), ((0, 'a'),))



    #---------------------------------------------------------------------------

    def test_series_slice_a(self) -> None:
        # create a series from a single value
        # s0 = Series(3, index=('a',))

        # generator based construction of values and index
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))

        # self.assertEqual(s1['b'], 1)
        # self.assertEqual(s1['d'], 3)

        s2 = s1['a':'c']   # type: ignore  # https://github.com/python/typeshed/pull/3024  # with Pandas this is inclusive
        self.assertEqual(s2.values.tolist(), [0, 1, 2])
        self.assertTrue(s2['b'] == s1['b'])

        s3 = s1['c':]  # type: ignore  # https://github.com/python/typeshed/pull/3024
        self.assertEqual(s3.values.tolist(), [2, 3])
        self.assertTrue(s3['d'] == s1['d'])

        self.assertEqual(s1['b':'d'].values.tolist(), [1, 2, 3])  # type: ignore  # https://github.com/python/typeshed/pull/3024

        self.assertEqual(s1[['a', 'c']].values.tolist(), [0, 2])


    def test_series_keys_a(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        self.assertEqual(list(s1.keys()), ['a', 'b', 'c', 'd'])

    def test_series_iter_a(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        self.assertEqual(list(s1), ['a', 'b', 'c', 'd'])

    def test_series_items_a(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        self.assertEqual(list(s1.items()), [('a', 0), ('b', 1), ('c', 2), ('d', 3)])


    def test_series_intersection_a(self) -> None:
        # create a series from a single value
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        s3 = s1['c':]  # type: ignore  # https://github.com/python/typeshed/pull/3024
        self.assertEqual(s1.index.intersection(s3.index).values.tolist(),
            ['c', 'd'])


    def test_series_intersection_b(self) -> None:
        # create a series from a single value
        idxa = IndexGO(('a', 'b', 'c'))
        idxb = IndexGO(('b', 'c', 'd'))

        self.assertEqual(idxa.intersection(idxb).values.tolist(),
            ['b', 'c'])

        self.assertEqual(idxa.union(idxb).values.tolist(),
            ['a', 'b', 'c', 'd'])

    #---------------------------------------------------------------------------


    def test_series_binary_operator_a(self) -> None:
        '''Test binary operators where one operand is a numeric.
        '''
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))

        self.assertEqual(list((s1 * 3).items()),
                [('a', 0), ('b', 3), ('c', 6), ('d', 9)])

        self.assertEqual(list((s1 / .5).items()),
                [('a', 0.0), ('b', 2.0), ('c', 4.0), ('d', 6.0)])

        self.assertEqual(list((s1 ** 3).items()),
                [('a', 0), ('b', 1), ('c', 8), ('d', 27)])


    def test_series_binary_operator_b(self) -> None:
        '''Test binary operators with Series of same index
        '''
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        s2 = Series((x * 2 for x in range(4)), index=('a', 'b', 'c', 'd'))

        self.assertEqual(list((s1 + s2).items()),
                [('a', 0), ('b', 3), ('c', 6), ('d', 9)])

        self.assertEqual(list((s1 * s2).items()),
                [('a', 0), ('b', 2), ('c', 8), ('d', 18)])


    def test_series_binary_operator_c(self) -> None:
        '''Test binary operators with Series of different index
        '''
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        s2 = Series((x * 2 for x in range(4)), index=('c', 'd', 'e', 'f'))

        self.assertAlmostEqualItems(list((s1 * s2).items()),
                [('a', nan), ('b', nan), ('c', 0), ('d', 6), ('e', nan), ('f', nan)]
                )


    def test_series_binary_operator_d(self) -> None:
        s1 = Series(range(4), index=list('abcd'))
        s2 = Series(range(3), index=list('abc'))
        s3 = s1 + s2

        self.assertEqual(s3.fillna(None).to_pairs(),
                (('a', 0), ('b', 2), ('c', 4), ('d', None))
                )

        s1 = Series((False, True, False, True), index=list('abcd'))
        s2 = Series([True] * 3, index=list('abc'))

        # NOTE: for now, we cannot resolve this case, as after reindexing we get an object array that is not compatible with Boolean array for the NaN4
        with self.assertRaises(TypeError):
            s3 = s1 | s2


    def test_series_binary_operator_e(self) -> None:

        s1 = Series((False, True, False, True), index=list('abcd'))
        s2 = Series([True] * 3, index=list('abc'))

        self.assertEqual((s1 == -1).to_pairs(),
                (('a', False), ('b', False), ('c', False), ('d', False)))

        self.assertEqual((s1 == s2).to_pairs(),
                (('a', False), ('b', True), ('c', False), ('d', False)))

        self.assertEqual((s1 == True).to_pairs(),
                (('a', False), ('b', True), ('c', False), ('d', True)))

        # NOTE: these are unexpected results that derive from NP Boolean operator behaviors

        self.assertEqual((s1 == (True,)).to_pairs(),
                (('a', False), ('b', True), ('c', False), ('d', True)))

        self.assertEqual((s1 == (True, False)).to_pairs(),
                (('a', False), ('b', False), ('c', False), ('d', False)))

        # as this is samed sized, NP does element wise comparison
        self.assertEqual((s1 == (False, True, False, True)).to_pairs(),
                (('a', True), ('b', True), ('c', True), ('d', True)))

        self.assertEqual((s1 == (False, True, False, True, False)).to_pairs(),
                (('a', False), ('b', False), ('c', False), ('d', False)))

    def test_series_binary_operator_f(self) -> None:
        r = Series(['100312', '101376', '100828', '101214', '100185'])
        c = Series(['100312', '101376', '101092', '100828', '100185'],
                index=['100312', '101376', '101092', '100828', '100185'])
        post = r == c

        # import ipdb; ipdb.set_trace()

        self.assertEqual(set(post.to_pairs()),
                set(((0, False), (1, False), (2, False), (3, False), (4, False), ('101376', False), ('101092', False), ('100828', False), ('100312', False), ('100185', False)))
                )


    def test_series_binary_operator_g(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))

        self.assertEqual(
                (s1 - 1).to_pairs(),
                (('a', -1), ('b', 0), ('c', 1), ('d', 2))
                )


        self.assertEqual((1 - s1).to_pairs(),
                (('a', 1), ('b', 0), ('c', -1), ('d', -2))
                )


    def test_series_binary_operator_h(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))

        self.assertEqual(
                s1 @ sf.Series([3, 4, 1, 2], index=('a', 'b', 'c', 'd')),
                12
                )
        self.assertEqual(
                s1 @ sf.Series([3, 4, 1, 2], index=('a', 'c', 'b', 'd')),
                15
                )

    def test_series_binary_operator_i(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        post = [3, 4, 1, 2] @ s1 #type: ignore
        self.assertEqual(post, 12)



    def test_series_binary_operator_j(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        with self.assertRaises(NotImplementedError):
            _ = s1 + np.arange(4).reshape((2, 2))



    #---------------------------------------------------------------------------


    def test_series_reindex_a(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))

        s2 = s1.reindex(('c', 'd', 'a'))
        self.assertEqual(list(s2.items()), [('c', 2), ('d', 3), ('a', 0)])

        s3 = s1.reindex(['a','b'])
        self.assertEqual(list(s3.items()), [('a', 0), ('b', 1)])


        # an int-valued array is hard to provide missing values for

        s4 = s1.reindex(['b', 'q', 'g', 'a'], fill_value=None)
        self.assertEqual(list(s4.items()),
                [('b', 1), ('q', None), ('g', None), ('a', 0)])

        # by default this gets float because filltype is nan by default
        s5 = s1.reindex(['b', 'q', 'g', 'a'])
        self.assertAlmostEqualItems(list(s5.items()),
                [('b', 1), ('q', nan), ('g', nan), ('a', 0)])


    def test_series_reindex_b(self) -> None:
        s1 = Series(range(4), index=IndexHierarchy.from_product(('a', 'b'), ('x', 'y')))
        s2 = Series(range(4), index=IndexHierarchy.from_product(('b', 'c'), ('x', 'y')))

        s3 = s1.reindex(s2.index, fill_value=None)

        self.assertEqual(s3.to_pairs(),
                ((('b', 'x'), 2), (('b', 'y'), 3), (('c', 'x'), None), (('c', 'y'), None)))

        # can reindex with a different dimensionality if no matches
        self.assertEqual(
                s1.reindex((3,4,5,6), fill_value=None).to_pairs(),
                ((3, None), (4, None), (5, None), (6, None)))

        self.assertEqual(
                s1.reindex((('b', 'x'),4,5,('a', 'y')), fill_value=None).to_pairs(),
                ((('b', 'x'), 2), (4, None), (5, None), (('a', 'y'), 1)))



    def test_series_reindex_c(self) -> None:
        s1 = Series(('a', 'b', 'c', 'd'), index=((0, x) for x in range(4)))
        self.assertEqual(s1.loc[(0, 2)], 'c')

        s1.reindex(((0, 1), (0, 3), (4,5)))

        self.assertEqual(
                s1.reindex(((0, 1), (0, 3), (4,5)), fill_value=None).to_pairs(),
                (((0, 1), 'b'), ((0, 3), 'd'), ((4, 5), None)))


        s2 = s1.reindex(('c', 'd', 'a'))
        self.assertEqual(sorted(s2.index.values.tolist()), ['a', 'c', 'd'])


    def test_series_reindex_d(self) -> None:

        s1 = Series(range(4), index=('a', 'b', 'c', 'd'), name='foo')
        s2 = s1.reindex(('c', 'd', 'a'))
        self.assertEqual(s2.index.values.tolist(), ['c', 'd', 'a'])
        self.assertEqual(s2.name, 'foo')

    def test_series_reindex_e(self) -> None:

        s1 = Series(range(4), index=('a', 'b', 'c', 'd'), name='foo')
        idx = Index(('c', 'd', 'a'))
        s2 = s1.reindex(idx, own_index=True)
        self.assertEqual(s2.index.values.tolist(), ['c', 'd', 'a'])
        self.assertEqual(s2.name, 'foo')
        # we owned the index, so have the same instance
        self.assertEqual(id(s2.index), id(idx))


    def test_series_isnull_a(self) -> None:

        s1 = Series((234.3, 3.2, 6.4, np.nan), index=('a', 'b', 'c', 'd'))
        s2 = Series((234.3, None, 6.4, np.nan), index=('a', 'b', 'c', 'd'))
        s3 = Series((234.3, 5, 6.4, -234.3), index=('a', 'b', 'c', 'd'))
        s4 = Series((234.3, None, None, None), index=('a', 'b', 'c', 'd'))
        s5 = Series(('p', 'q', 'e', 'g'), index=('a', 'b', 'c', 'd'))
        s6 = Series((False, True, False, True), index=('a', 'b', 'c', 'd'))

        self.assertEqual(list(s1.isna().items()),
                [('a', False), ('b', False), ('c', False), ('d', True)]
                )
        self.assertEqual(list(s2.isna().items()),
                [('a', False), ('b', True), ('c', False), ('d', True)])

        self.assertEqual(list(s3.isna().items()),
                [('a', False), ('b', False), ('c', False), ('d', False)])

        self.assertEqual(list(s4.isna().items()),
                [('a', False), ('b', True), ('c', True), ('d', True)])

        # those that are always false
        self.assertEqual(list(s5.isna().items()),
                [('a', False), ('b', False), ('c', False), ('d', False)])

        self.assertEqual(list(s6.isna().items()),
                [('a', False), ('b', False), ('c', False), ('d', False)])



    def test_series_isnull_b(self) -> None:

        # NOTE: this is a problematic case as it as a string with numerics and None
        s1 = Series((234.3, 'a', None, 6.4, np.nan), index=('a', 'b', 'c', 'd', 'e'))

        self.assertEqual(list(s1.isna().items()),
                [('a', False), ('b', False), ('c', True), ('d', False), ('e', True)]
                )

    def test_series_notnull(self) -> None:

        s1 = Series((234.3, 3.2, 6.4, np.nan), index=('a', 'b', 'c', 'd'))
        s2 = Series((234.3, None, 6.4, np.nan), index=('a', 'b', 'c', 'd'))
        s3 = Series((234.3, 5, 6.4, -234.3), index=('a', 'b', 'c', 'd'))
        s4 = Series((234.3, None, None, None), index=('a', 'b', 'c', 'd'))
        s5 = Series(('p', 'q', 'e', 'g'), index=('a', 'b', 'c', 'd'))
        s6 = Series((False, True, False, True), index=('a', 'b', 'c', 'd'))

        self.assertEqual(list(s1.notna().items()),
                [('a', True), ('b', True), ('c', True), ('d', False)]
                )
        self.assertEqual(list(s2.notna().items()),
                [('a', True), ('b', False), ('c', True), ('d', False)])

        self.assertEqual(list(s3.notna().items()),
                [('a', True), ('b', True), ('c', True), ('d', True)])

        self.assertEqual(list(s4.notna().items()),
                [('a', True), ('b', False), ('c', False), ('d', False)])

        # those that are always false
        self.assertEqual(list(s5.notna().items()),
                [('a', True), ('b', True), ('c', True), ('d', True)])

        self.assertEqual(list(s6.notna().items()),
                [('a', True), ('b', True), ('c', True), ('d', True)])


    def test_series_dropna_a(self) -> None:

        s1 = Series((234.3, 3.2, 6.4, np.nan), index=('a', 'b', 'c', 'd'))
        s2 = Series((234.3, None, 6.4, np.nan), index=('a', 'b', 'c', 'd'))
        s4 = Series((234.3, None, None, None), index=('a', 'b', 'c', 'd'))
        s5 = Series(('p', 'q', 'e', 'g'), index=('a', 'b', 'c', 'd'))
        s6 = Series((False, True, False, True), index=('a', 'b', 'c', 'd'))

        self.assertEqual(s1.dropna().to_pairs(),
                (('a', 234.3), ('b', 3.2), ('c', 6.4)))
        self.assertEqual(list(s2.dropna().items()),
                [('a', 234.3), ('c', 6.4)])
        self.assertEqual(s4.dropna().to_pairs(),
                (('a', 234.3),))
        self.assertEqual(s5.dropna().to_pairs(),
                (('a', 'p'), ('b', 'q'), ('c', 'e'), ('d', 'g')))
        self.assertEqual(s6.dropna().to_pairs(),
                (('a', False), ('b', True), ('c', False), ('d', True)))

    def test_series_dropna_b(self) -> None:
        s1 = sf.Series.from_element(np.nan, index=sf.IndexHierarchy.from_product(['A', 'B'], [1, 2]))
        s2 = s1.dropna()
        self.assertEqual(len(s2), 0)
        self.assertEqual(s1.__class__, s2.__class__)

    def test_series_dropna_c(self) -> None:
        s1 = sf.Series([1, np.nan, 2, np.nan],
                index=sf.IndexHierarchy.from_product(['A', 'B'], [1, 2]))
        s2 = s1.dropna()
        self.assertEqual(s2.to_pairs(), ((('A', 1), 1.0), (('B', 1), 2.0)))

    #---------------------------------------------------------------------------

    def test_series_fillna_a(self) -> None:

        s1 = Series((234.3, 3.2, 6.4, np.nan), index=('a', 'b', 'c', 'd'))
        s2 = Series((234.3, None, 6.4, np.nan), index=('a', 'b', 'c', 'd'))
        s3 = Series((234.3, 5, 6.4, -234.3), index=('a', 'b', 'c', 'd'))
        s4 = Series((234.3, None, None, None), index=('a', 'b', 'c', 'd'))
        s5 = Series(('p', 'q', 'e', 'g'), index=('a', 'b', 'c', 'd'))
        s6 = Series((False, True, False, True), index=('a', 'b', 'c', 'd'))
        s7 = Series((10, 20, 30, 40), index=('a', 'b', 'c', 'd'))
        s8 = Series((234.3, None, 6.4, np.nan, 'q'), index=('a', 'b', 'c', 'd', 'e'))


        self.assertEqual(s1.fillna(0.0).values.tolist(),
                [234.3, 3.2, 6.4, 0.0])

        self.assertEqual(s1.fillna(-1).values.tolist(),
                [234.3, 3.2, 6.4, -1.0])

        # given a float array, inserting None, None is casted to nan
        self.assertEqual(s1.fillna(None).values.tolist(),
                [234.3, 3.2, 6.4, None])

        post = s1.fillna('wer')
        self.assertEqual(post.dtype, object)
        self.assertEqual(post.values.tolist(),
                [234.3, 3.2, 6.4, 'wer'])


        post = s7.fillna(None)
        self.assertEqual(post.dtype, int)


    def test_series_fillna_b(self) -> None:

        s1 = Series(())
        s2 = s1.fillna(0)
        self.assertTrue(len(s2) == 0)


    def test_series_fillna_c(self) -> None:

        s1 = Series((np.nan, 3, np.nan))
        with self.assertRaises(RuntimeError):
            _ = s1.fillna(np.arange(3))


    def test_series_fillna_d(self) -> None:

        s1 = Series((np.nan, 3, np.nan, 4), index=tuple('abcd'))
        s2 = Series((100, 200), index=tuple('ca'))
        s3 = s1.fillna(s2)
        self.assertEqual(s3.dtype, float)
        self.assertEqual(s3.to_pairs(),
                (('a', 200.0), ('b', 3.0), ('c', 100.0), ('d', 4.0))
                )

    def test_series_fillna_e(self) -> None:

        s1 = Series((None, None, 'foo', 'bar'), index=tuple('abcd'))
        s2 = Series((100, 200), index=tuple('ca'))
        s3 = s1.fillna(s2)
        self.assertEqual(s3.dtype, object)
        self.assertEqual(type(s3['a']), int)
        self.assertEqual(s3.to_pairs(),
                (('a', 200), ('b', None), ('c', 'foo'), ('d', 'bar'))
                )


    def test_series_fillna_f(self) -> None:

        s1 = Series((None, None, 'foo', 'bar'), index=tuple('abcd'))
        s2 = Series((100, 200))
        s3 = s1.fillna(s2)
        # no alignment, return the same Series
        self.assertEqual(id(s3), id(s1))



    def test_series_fillna_g(self) -> None:

        s1 = Series((np.nan, 3, np.nan, 4), index=tuple('abcd'))
        s2 = Series((False, True), index=tuple('ba'))
        s3 = s1.fillna(s2)
        self.assertEqual(s3.dtype, object)
        self.assertEqual(s3.fillna(-1).to_pairs(),
                (('a', True), ('b', 3.0), ('c', -1), ('d', 4.0))
                )


    #---------------------------------------------------------------------------

    def test_series_fillna_directional_a(self) -> None:

        a1 = np.array((3, 4))
        a2 = Series._fillna_directional(
                array=a1,
                directional_forward=True,
                limit=2)

        self.assertEqual(id(a1), id(a2))


    def test_series_fillna_sided_a(self) -> None:

        a1 = np.array((np.nan, 3, np.nan))

        with self.assertRaises(RuntimeError):
            _ = Series._fillna_sided(
                    array=a1,
                    value=a1,
                    sided_leading=True)



    #---------------------------------------------------------------------------

    def test_series_fillna_leading_a(self) -> None:

        s1 = Series((234.3, 3.2, 6.4, np.nan), index=('a', 'b', 'c', 'd'))
        s2 = Series((np.nan, None, 6, np.nan), index=('a', 'b', 'c', 'd'))
        s3 = Series((np.nan, np.nan, np.nan, 4), index=('a', 'b', 'c', 'd'))
        s4 = Series((None, None, None, None), index=('a', 'b', 'c', 'd'))

        self.assertEqual(s1.fillna_leading(-1).fillna(0).to_pairs(),
                (('a', 234.3), ('b', 3.2), ('c', 6.4), ('d', 0.0)))

        self.assertEqual(s2.fillna_leading(0).fillna(-1).to_pairs(),
                (('a', 0), ('b', 0), ('c', 6), ('d', -1)))

        self.assertEqual(s3.fillna_leading('a').to_pairs(),
                (('a', 'a'), ('b', 'a'), ('c', 'a'), ('d', 4.0)))

        self.assertEqual(s4.fillna_leading('b').to_pairs(),
                (('a', 'b'), ('b', 'b'), ('c', 'b'), ('d', 'b')))


    def test_series_fillna_leading_b(self) -> None:

        s1 = Series((3.2, 6.4), index=('a', 'b',))
        s2 = s1.fillna_leading(0)
        self.assertTrue(s1.to_pairs() == s2.to_pairs())


    def test_series_fillna_trailing_a(self) -> None:

        s1 = Series((234.3, 3.2, np.nan, np.nan), index=('a', 'b', 'c', 'd'))
        s2 = Series((np.nan, None, 6.4, np.nan), index=('a', 'b', 'c', 'd'))
        s3 = Series((np.nan, 2.3, 6.4, 4), index=('a', 'b', 'c', 'd'))
        s4 = Series((None, None, None, None), index=('a', 'b', 'c', 'd'))

        self.assertEqual(s1.fillna_trailing(0).to_pairs(),
                (('a', 234.3), ('b', 3.2), ('c', 0.0), ('d', 0.0)))

        self.assertEqual(s2.fillna_trailing(0).fillna(-1).to_pairs(),
                (('a', -1), ('b', -1), ('c', 6.4), ('d', 0)))

        self.assertEqual(s3.fillna_trailing(2).fillna(-1).to_pairs(),
                (('a', -1.0), ('b', 2.3), ('c', 6.4), ('d', 4.0)))

        self.assertEqual(s4.fillna_trailing('c').to_pairs(),
                (('a', 'c'), ('b', 'c'), ('c', 'c'), ('d', 'c')))



    def test_series_fillna_forward_a(self) -> None:

        index = tuple(string.ascii_lowercase[:8])

        # target_index [0 3 6]
        s1 = Series((3, None, None, 4, None, None, 5, 6), index=index)
        self.assertEqual(s1.fillna_forward().to_pairs(),
                (('a', 3), ('b', 3), ('c', 3), ('d', 4), ('e', 4), ('f', 4), ('g', 5), ('h', 6)))

        # target_index [3]
        s2 = Series((None, None, None, 4, None, None, None, None), index=index)
        self.assertEqual(s2.fillna_forward().to_pairs(),
                (('a', None), ('b', None), ('c', None), ('d', 4), ('e', 4), ('f', 4), ('g', 4), ('h', 4)))

        # target_index [0 6]
        s3 = Series((1, None, None, None, None, None, 4, None), index=index)
        self.assertEqual(s3.fillna_forward().to_pairs(),
                (('a', 1), ('b', 1), ('c', 1), ('d', 1), ('e', 1), ('f', 1), ('g', 4), ('h', 4)))

        # target_index [0 7]
        s4 = Series((1, None, None, None, None, None, None, 4), index=index)
        self.assertEqual(s4.fillna_forward().to_pairs(),
                (('a', 1), ('b', 1), ('c', 1), ('d', 1), ('e', 1), ('f', 1), ('g', 1), ('h', 4)))

        # target_index [7]
        s5 = Series((None, None, None, None, None, None, None, 4), index=index)
        self.assertEqual(s5.fillna_forward().to_pairs(),
                (('a', None), ('b', None), ('c', None), ('d', None), ('e', None), ('f', None), ('g', None), ('h', 4)))

        # target index = array([0, 3, 6])
        s6 = Series((2, None, None, 3, 4, 5, 6, None), index=index)
        self.assertEqual(s6.fillna_forward().to_pairs(),
                (('a', 2), ('b', 2), ('c', 2), ('d', 3), ('e', 4), ('f', 5), ('g', 6), ('h', 6))
                )
        # target_index [6]
        s7 = Series((2, 1, 0, 3, 4, 5, 6, None), index=index)
        self.assertEqual(s7.fillna_forward().to_pairs(),
                (('a', 2), ('b', 1), ('c', 0), ('d', 3), ('e', 4), ('f', 5), ('g', 6), ('h', 6)))

        s8 = Series((2, None, None, None, 4, None, 6, None), index=index)
        self.assertEqual(s8.fillna_forward().to_pairs(),
                (('a', 2), ('b', 2), ('c', 2), ('d', 2), ('e', 4), ('f', 4), ('g', 6), ('h', 6)))

        s9 = Series((None, 2, 3, None, 4, None, 6, 7), index=index)
        self.assertEqual(s9.fillna_forward().to_pairs(),
                (('a', None), ('b', 2), ('c', 3), ('d', 3), ('e', 4), ('f', 4), ('g', 6), ('h', 7)))


    def test_series_fillna_forward_b(self) -> None:

        index = tuple(string.ascii_lowercase[:8])

        # target_index [0 3 6]
        s1 = Series((3, None, None, None, 4, None, None, None), index=index)
        s2 = s1.fillna_forward(limit=2)

        self.assertEqual(s2.to_pairs(),
                (('a', 3), ('b', 3), ('c', 3), ('d', None), ('e', 4), ('f', 4), ('g', 4), ('h', None))
                )

        self.assertEqual(s1.fillna_forward(limit=1).to_pairs(),
                (('a', 3), ('b', 3), ('c', None), ('d', None), ('e', 4), ('f', 4), ('g', None), ('h', None)))

        self.assertEqual(s1.fillna_forward(limit=10).to_pairs(),
                (('a', 3), ('b', 3), ('c', 3), ('d', 3), ('e', 4), ('f', 4), ('g', 4), ('h', 4)))

    def test_series_fillna_forward_c(self) -> None:

        # this case shown to justify the slice_condition oassed to slices_from_targets
        index = tuple(string.ascii_lowercase[:8])
        s1 = Series((3, 2, None, 4, None, None, 5, 6), index=index)

        self.assertEqual(s1.fillna_forward().to_pairs(),
                (('a', 3), ('b', 2), ('c', 2), ('d', 4), ('e', 4), ('f', 4), ('g', 5), ('h', 6)))

        self.assertEqual(s1.fillna_backward().to_pairs(),
                (('a', 3), ('b', 2), ('c', 4), ('d', 4), ('e', 5), ('f', 5), ('g', 5), ('h', 6)))


    def test_series_fillna_backward_a(self) -> None:

        index = tuple(string.ascii_lowercase[:8])

        # target_index [0 3 6]
        s1 = Series((3, None, None, 4, None, None, 5, 6), index=index)
        self.assertEqual(s1.fillna_backward().to_pairs(),
                (('a', 3), ('b', 4), ('c', 4), ('d', 4), ('e', 5), ('f', 5), ('g', 5), ('h', 6)))

        s2 = Series((None, None, None, 4, None, None, None, None), index=index)
        self.assertEqual(s2.fillna_backward().to_pairs(),
                (('a', 4), ('b', 4), ('c', 4), ('d', 4), ('e', None), ('f', None), ('g', None), ('h', None)))

        s3 = Series((1, None, None, None, None, None, 4, None), index=index)
        self.assertEqual(s3.fillna_backward().to_pairs(),
                (('a', 1), ('b', 4), ('c', 4), ('d', 4), ('e', 4), ('f', 4), ('g', 4), ('h', None)))

        s4 = Series((1, None, None, None, None, None, None, 4), index=index)
        self.assertEqual(s4.fillna_backward().to_pairs(),
                (('a', 1), ('b', 4), ('c', 4), ('d', 4), ('e', 4), ('f', 4), ('g', 4), ('h', 4)))

        s5 = Series((None, None, None, None, None, None, None, 4), index=index)
        self.assertEqual(s5.fillna_backward().to_pairs(),
                (('a', 4), ('b', 4), ('c', 4), ('d', 4), ('e', 4), ('f', 4), ('g', 4), ('h', 4)))

        s6 = Series((2, None, None, 3, 4, 5, 6, None), index=index)
        self.assertEqual(s6.fillna_backward().to_pairs(),
                (('a', 2), ('b', 3), ('c', 3), ('d', 3), ('e', 4), ('f', 5), ('g', 6), ('h', None)))

        s7 = Series((None, 1, 0, 3, 4, 5, 6, 7), index=index)
        self.assertEqual(s7.fillna_backward().to_pairs(),
            (('a', 1), ('b', 1), ('c', 0), ('d', 3), ('e', 4), ('f', 5), ('g', 6), ('h', 7)))

        s8 = Series((2, None, None, None, 4, None, 6, None), index=index)
        self.assertEqual(s8.fillna_backward().to_pairs(),
            (('a', 2), ('b', 4), ('c', 4), ('d', 4), ('e', 4), ('f', 6), ('g', 6), ('h', None)))

        s9 = Series((None, 2, 3, None, 4, None, 6, 7), index=index)
        self.assertEqual(s9.fillna_backward().to_pairs(),
                (('a', 2), ('b', 2), ('c', 3), ('d', 4), ('e', 4), ('f', 6), ('g', 6), ('h', 7)))


    def test_series_fillna_backward_b(self) -> None:

        index = tuple(string.ascii_lowercase[:8])

        # target_index [0 3 6]
        s1 = Series((3, None, None, 4, None, None, 5, 6), index=index)
        self.assertEqual(s1.fillna_backward(1).to_pairs(),
                (('a', 3), ('b', None), ('c', 4), ('d', 4), ('e', None), ('f', 5), ('g', 5), ('h', 6)))

        s2 = Series((3, None, None, None, 4, None, None, None), index=index)
        self.assertEqual(s2.fillna_backward(2).to_pairs(),
                (('a', 3), ('b', None), ('c', 4), ('d', 4), ('e', 4), ('f', None), ('g', None), ('h', None)))

        s3 = Series((None, 1, None, None, None, None, None, 5), index=index)
        self.assertEqual(s3.fillna_backward(4).to_pairs(),
                (('a', 1), ('b', 1), ('c', None), ('d', 5), ('e', 5), ('f', 5), ('g', 5), ('h', 5)))


    #---------------------------------------------------------------------------
    def test_series_from_element_a(self) -> None:
        s1 = Series.from_element('a', index=range(3))
        self.assertEqual(s1.to_pairs(),
                ((0, 'a'), (1, 'a'), (2, 'a'))
                )


    def test_series_from_element_b(self) -> None:
        s1 = Series.from_element('a', index=Index((3, 4, 5)), own_index=True)
        self.assertEqual(s1.to_pairs(),
                ((3, 'a'), (4, 'a'), (5, 'a'))
                )


    #---------------------------------------------------------------------------
    def test_series_from_items_a(self) -> None:

        def gen() -> tp.Iterator[tp.Tuple[int, int]]:
            r1 = range(10)
            r2 = iter(range(10, 20))
            for x in r1:
                yield x, next(r2)

        s1 = Series.from_items(gen())
        self.assertEqual(s1.loc[7:9].values.tolist(), [17, 18, 19])

        s2 = Series.from_items(dict(a=30, b=40, c=50).items())
        self.assertEqual(s2['c'], 50)
        self.assertEqual(s2['b'], 40)
        self.assertEqual(s2['a'], 30)


    def test_series_from_items_b(self) -> None:

        s1 = Series.from_items(zip(list('abc'), (1,2,3)), dtype=str, name='foo')
        self.assertEqual(s1.name, 'foo')
        self.assertEqual(s1.values.tolist(), ['1', '2', '3'])

    def test_series_from_items_c(self) -> None:

        s1 = Series.from_items(zip(
                ((1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')), range(4)),
                index_constructor=IndexHierarchy.from_labels)
        self.assertEqual(s1[HLoc[:, 'b']].to_pairs(),
                (((1, 'b'), 1), ((2, 'b'), 3))
                )

    def test_series_from_items_d(self) -> None:

        with self.assertRaises(RuntimeError):
            s1 = Series.from_items(zip(
                    ((1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')), range(4)),
                    index_constructor=IndexHierarchyGO.from_labels)

    def test_series_from_items_e(self) -> None:
        s1 = Series.from_items(zip(('2017-11', '2017-12', '2018-01', '2018-02'),
                range(4)),
                index_constructor=IndexYearMonth)

        self.assertEqual(s1['2017'].to_pairs(),
                ((np.datetime64('2017-11'), 0),
                (np.datetime64('2017-12'), 1))
                )

        self.assertEqual(s1['2018'].to_pairs(),
                ((np.datetime64('2018-01'), 2),
                (np.datetime64('2018-02'), 3))
                )


    #---------------------------------------------------------------------------

    def test_series_contains_a(self) -> None:

        s1 = Series.from_items(zip(('a', 'b', 'c'), (10, 20, 30)))
        self.assertTrue('b' in s1)
        self.assertTrue('c' in s1)
        self.assertTrue('a' in s1)

        self.assertFalse('d' in s1)
        self.assertFalse('' in s1)

    #---------------------------------------------------------------------------


    def test_series_sum_a(self) -> None:

        s1 = Series.from_items(zip(('a', 'b', 'c'), (10, 20, 30)))
        self.assertEqual(s1.sum(), 60)

        s1 = Series.from_items(zip(('a', 'b', 'c', 'd'), (10, 20, 30, np.nan)))
        self.assertEqual(s1.sum(), 60)

        s1 = Series.from_items(zip(('a', 'b', 'c', 'd'), (10, 20, 30, None)))
        self.assertEqual(s1.sum(), 60)


    def test_series_sum_b(self) -> None:
        s1 = Series(list('abc'), dtype=object)
        self.assertEqual(s1.sum(), 'abc')
        # get the same result from character arrays
        s2 = sf.Series(list('abc'))
        self.assertEqual(s2.sum(), 'abc')


    def test_series_cumsum_a(self) -> None:

        s1 = Series.from_items(zip('abc', (10, 20, 30)))

        self.assertEqual(s1.cumsum().to_pairs(),
                (('a', 10), ('b', 30), ('c', 60))
                )

        s2 = Series.from_items(zip('abc', (10, np.nan, 30))).cumsum(skipna=False).fillna(None)
        self.assertEqual(s2.to_pairs(),
                (('a', 10.0), ('b', None), ('c', None))
                )


    def test_series_cumprod_a(self) -> None:

        s1 = Series.from_items(zip('abc', (10, 20, 30)))
        self.assertEqual(
                s1.cumprod().to_pairs(),
                (('a', 10), ('b', 200), ('c', 6000))
                )


    def test_series_median_a(self) -> None:

        s1 = Series.from_items(zip('abcde', (10, 20, 0, 15, 30)))
        self.assertEqual(s1.median(), 15)
        self.assertEqual(s1.median(skipna=False), 15)

        s2 = Series.from_items(zip('abcde', (10, 20, np.nan, 15, 30)))
        self.assertEqual(s2.median(), 17.5)
        self.assertTrue(np.isnan(s2.median(skipna=False)))

        with self.assertRaises(TypeError):
            # should raise with bad keyword argumenty
            s2.median(skip_na=False) #type: ignore

    #---------------------------------------------------------------------------

    def test_series_mask_a(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))

        self.assertEqual(
                s1.mask.loc[['b', 'd']].values.tolist(),
                [False, True, False, True])
        self.assertEqual(s1.mask.iloc[1:].values.tolist(),
                [False, True, True, True])

        self.assertEqual(s1.masked_array.loc[['b', 'd']].sum(), 2)
        self.assertEqual(s1.masked_array.loc[['a', 'b']].sum(), 5)



    def test_series_assign_a(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))


        self.assertEqual(
                s1.assign.loc[['b', 'd']](3000).values.tolist(),
                [0, 3000, 2, 3000])

        self.assertEqual(
                s1.assign['b':](300).values.tolist(),  # type: ignore  # https://github.com/python/typeshed/pull/3024
                [0, 300, 300, 300])


    def test_series_assign_b(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))

        self.assertEqual(list(s1.isin([2]).items()),
                [('a', False), ('b', False), ('c', True), ('d', False)])

        self.assertEqual(list(s1.isin({2, 3}).items()),
                [('a', False), ('b', False), ('c', True), ('d', True)])

        self.assertEqual(list(s1.isin(range(2, 4)).items()),
                [('a', False), ('b', False), ('c', True), ('d', True)])


    def test_series_assign_c(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        self.assertEqual(s1.assign.loc['c':](0).to_pairs(),  # type: ignore  # https://github.com/python/typeshed/pull/3024
                (('a', 0), ('b', 1), ('c', 0), ('d', 0))
                )
        self.assertEqual(s1.assign.loc['c':]((20, 30)).to_pairs(),  # type: ignore  # https://github.com/python/typeshed/pull/3024
                (('a', 0), ('b', 1), ('c', 20), ('d', 30)))

        self.assertEqual(s1.assign['c':](s1['c':] * 10).to_pairs(),  # type: ignore  # https://github.com/python/typeshed/pull/3024
                (('a', 0), ('b', 1), ('c', 20), ('d', 30)))

        self.assertEqual(s1.assign['c':](Series.from_dict({'d':40, 'c':60})).to_pairs(),  # type: ignore  # https://github.com/python/typeshed/pull/3024
                (('a', 0), ('b', 1), ('c', 60), ('d', 40)))


    def test_series_assign_d(self) -> None:
        s1 = Series(tuple('pqrs'), index=('a', 'b', 'c', 'd'))
        s2 = s1.assign['b'](None)
        self.assertEqual(s2.to_pairs(),
                (('a', 'p'), ('b', None), ('c', 'r'), ('d', 's')))
        self.assertEqual(s1.assign['b':](None).to_pairs(),  # type: ignore  # https://github.com/python/typeshed/pull/3024
                (('a', 'p'), ('b', None), ('c', None), ('d', None)))


    def test_series_assign_e(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        s2 = Series(range(2), index=('c', 'd'))
        self.assertEqual(
                s1.assign[s2.index](s2).to_pairs(),
                (('a', 0), ('b', 1), ('c', 0), ('d', 1))
                )
    def test_series_assign_f(self) -> None:
        s1 = Series(range(5), index=('a', 'b', 'c', 'd', 'e'))

        with self.assertRaises(Exception):
            # cannot have an assignment target that is not in the Series
            s1.assign[['f', 'd']](10)

        self.assertEqual(
                s1.assign[['d', 'c']](Series((10, 20), index=('d', 'c'))).to_pairs(),
                (('a', 0), ('b', 1), ('c', 20), ('d', 10), ('e', 4)))

        self.assertEqual(
                s1.assign[['c', 'd']](Series((10, 20), index=('d', 'c'))).to_pairs(),
                (('a', 0), ('b', 1), ('c', 20), ('d', 10), ('e', 4)))

        self.assertEqual(
                s1.assign[['c', 'd']](Series((10, 20, 30), index=('d', 'c', 'f'))).to_pairs(),
                (('a', 0), ('b', 1), ('c', 20), ('d', 10), ('e', 4)))


        self.assertEqual(
                s1.assign[['c', 'd', 'b']](Series((10, 20), index=('d', 'c')), fill_value=-1).to_pairs(),
                (('a', 0), ('b', -1), ('c', 20), ('d', 10), ('e', 4))
                )

    def test_series_assign_g(self) -> None:
        s1 = Series(range(5), index=('a', 'b', 'c', 'd', 'e'), name='x')

        s2 = Series(list('abc'), index=list('abc'), name='y')

        post = s1.assign[s2.index](s2)
        self.assertEqual(post.name, 'x')
        self.assertEqual(post.values.tolist(), ['a', 'b', 'c', 3, 4])


    def test_series_iloc_extract_a(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))

        self.assertEqual(s1.iloc[0], 0)

        self.assertEqual(s1.iloc[2:].to_pairs(), (('c', 2), ('d', 3)))



    def test_series_loc_extract_a(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        with self.assertRaises(KeyError):
            s1.loc[['c', 'd', 'e']] #pylint: disable=W0104

    def test_series_loc_extract_b(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'), name='foo')
        s2 = s1.loc[['b', 'd']]

        self.assertEqual(s2.to_pairs(), (('b', 1), ('d', 3)))
        self.assertEqual(s2.name, 'foo')

    def test_series_loc_extract_c(self) -> None:
        s = sf.Series(range(5),
                index=sf.IndexHierarchy.from_labels(
                (('a', 'a'), ('a', 'b'), ('b', 'a'), ('b', 'b'), ('b', 'c'))))

        # this selection returns just a single value
        # import ipdb; ipdb.set_trace()
        s2 = s.loc[sf.HLoc[:, 'c']]
        self.assertEqual(s2.__class__, s.__class__)
        self.assertEqual(s2.to_pairs(), ((('b', 'c'), 4),))

        # this selection yields a series
        self.assertEqual(s.loc[sf.HLoc[:, 'a']].to_pairs(),
                ((('a', 'a'), 0), (('b', 'a'), 2)))


    def test_series_loc_extract_d(self) -> None:
        s = sf.Series(range(5),
                index=sf.IndexHierarchy.from_labels(
                (('a', 'a'), ('a', 'b'), ('b', 'a'), ('b', 'b'), ('b', 'c'))))
        # leaf loc selection must be terminal; using a slice or list is an exception
        with self.assertRaises(RuntimeError):
            s.loc['a', :] #pylint: disable=W0104

        with self.assertRaises(RuntimeError):
            s.loc[['a', 'b'], 'b'] #pylint: disable=W0104


    def test_series_loc_extract_e(self) -> None:
        s1 = sf.Series(range(4), index=sf.IndexHierarchy.from_product(['A', 'B'], [1, 2]))

        self.assertEqual(s1.loc[('B', 1)], 2)
        self.assertEqual(s1.loc[sf.HLoc['B', 1]], 2)
        self.assertEqual(s1.iloc[2], 2)


    def test_series_loc_extract_f(self) -> None:
        s1 = sf.Series(range(4), index=sf.IndexHierarchy.from_product(['A', 'B'], [1, 2]))

        post1 = s1[HLoc['A', [2]]]
        self.assertEqual(post1.to_pairs(), ((('A', 2), 1),))

        post2 = s1[HLoc['A', 2]]
        self.assertEqual(post2, 1)


    #---------------------------------------------------------------------------

    def test_series_group_a(self) -> None:

        s1 = Series((0, 1, 0, 1), index=('a', 'b', 'c', 'd'))

        groups = tuple(s1.iter_group_items())

        self.assertEqual([g[0] for g in groups], [0, 1])

        self.assertEqual([g[1].to_pairs() for g in groups],
                [(('a', 0), ('c', 0)), (('b', 1), ('d', 1))])

    def test_series_group_b(self) -> None:

        s1 = Series(('foo', 'bar', 'foo', 20, 20),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        groups = tuple(s1.iter_group_items())


        self.assertEqual([g[0] for g in groups],
                [20, 'bar', 'foo'])
        self.assertEqual([g[1].to_pairs() for g in groups],
                [(('d', 20), ('e', 20)), (('b', 'bar'),), (('a', 'foo'), ('c', 'foo'))])


    def test_series_group_c(self) -> None:

        s1 = Series((10, 10, 10, 20, 20),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        groups = tuple(s1.iter_group())
        self.assertEqual([g.sum() for g in groups], [30, 40])

        self.assertEqual(
                s1.iter_group().apply(np.sum).to_pairs(),
                ((10, 30), (20, 40)))

        self.assertEqual(
                s1.iter_group_items().apply(lambda g, s: (g * s).values.tolist()).to_pairs(),
                ((10, [100, 100, 100]), (20, [400, 400])))


    #---------------------------------------------------------------------------

    def test_series_iter_element_a(self) -> None:

        s1 = Series((10, 3, 15, 21, 28),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        self.assertEqual([x for x in s1.iter_element()], [10, 3, 15, 21, 28])

        self.assertEqual([x for x in s1.iter_element_items()],
                        [('a', 10), ('b', 3), ('c', 15), ('d', 21), ('e', 28)])

        self.assertEqual(s1.iter_element().apply(lambda x: x * 20).to_pairs(),
                (('a', 200), ('b', 60), ('c', 300), ('d', 420), ('e', 560)))

        self.assertEqual(
                s1.iter_element_items().apply(lambda k, v: v * 20 if k == 'b' else 0).to_pairs(),
                (('a', 0), ('b', 60), ('c', 0), ('d', 0), ('e', 0)))


    def test_series_iter_element_b(self) -> None:

        s1 = Series((10, 3, 15, 21, 28, 50),
                index=IndexHierarchy.from_product(tuple('ab'), tuple('xyz')),
                dtype=object)
        s2 = s1.iter_element().apply(str)
        self.assertEqual(s2.index.__class__, IndexHierarchy)

        self.assertEqual(s2.to_pairs(),
                ((('a', 'x'), '10'), (('a', 'y'), '3'), (('a', 'z'), '15'), (('b', 'x'), '21'), (('b', 'y'), '28'), (('b', 'z'), '50')))


    #---------------------------------------------------------------------------

    def test_series_iter_element_map_any_a(self) -> None:

        s1 = Series((10, 3, 15, 21, 28),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        post = s1.iter_element().map_any({3: 100, 21: 101})

        self.assertEqual(post.to_pairs(),
                (('a', 10), ('b', 100), ('c', 15), ('d', 101), ('e', 28))
                )


    def test_series_iter_element_map_any_b(self) -> None:

        s1 = Series((10, 3, 15, 21, 28),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        s2 = Series((100, 101), index=(3, 21))

        post = s1.iter_element().map_any(s2)

        self.assertEqual(post.to_pairs(),
                (('a', 10), ('b', 100), ('c', 15), ('d', 101), ('e', 28))
                )


    def test_series_iter_element_map_any_c(self) -> None:

        s1 = Series((10, 3, 15, 21, 28),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        s2 = Series((100, 101), index=(3, 21))

        self.assertEqual(tuple(s2.iter_element().map_any_iter(s2)),
            (100, 101))
        self.assertEqual(tuple(s2.iter_element().map_any_iter_items(s2)),
            ((3, 100), (21, 101)))


    def test_series_iter_element_map_all_a(self) -> None:

        s1 = Series((10, 3, 15, 21, 28),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        with self.assertRaises(KeyError):
            post = s1.iter_element().map_all({3: 100, 21: 101})

        post = s1.iter_element().map_all({v: k for k, v in s1.items()})

        self.assertEqual(post.to_pairs(),
                (('a', 'a'), ('b', 'b'), ('c', 'c'), ('d', 'd'), ('e', 'e'))
                )

    def test_series_iter_element_map_all_b(self) -> None:

        s1 = Series((10, 3, 15, 21, 28),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        s2 = Series((100, 101), index=(3, 21))

        with self.assertRaises(KeyError):
            post = s1.iter_element().map_all(s2)

        s3 = Series.from_items((v, i) for i, v in enumerate(s1.values))

        self.assertEqual(s3.to_pairs(),
                ((10, 0), (3, 1), (15, 2), (21, 3), (28, 4))
                )

    def test_series_iter_element_map_all_c(self) -> None:

        s1 = Series((10, 3, 15, 21, 28),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        s2 = Series.from_items((v, i) for i, v in enumerate(s1.values))

        self.assertEqual(tuple(s1.iter_element().map_all_iter(s2)),
                (0, 1, 2, 3, 4))

        self.assertEqual(tuple(s1.iter_element().map_all_iter_items(s2)),
                (('a', 0), ('b', 1), ('c', 2), ('d', 3), ('e', 4))
                )

    def test_series_iter_element_map_fill_a(self) -> None:

        s1 = Series((10, 3, 15, 21, 28),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        post = s1.iter_element().map_fill({21: 100, 28: 101}, fill_value=-1)
        self.assertEqual(post.to_pairs(),
                (('a', -1), ('b', -1), ('c', -1), ('d', 100), ('e', 101))
                )

    def test_series_iter_element_map_fill_b(self) -> None:

        s1 = Series((10, 3, 15, 21, 28),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        s2 = Series((100, 101), index=(21, 28))

        post = s1.iter_element().map_fill(s2, fill_value=-1)
        self.assertEqual(post.to_pairs(),
                (('a', -1), ('b', -1), ('c', -1), ('d', 100), ('e', 101))
                )


    def test_series_iter_element_map_fill_c(self) -> None:

        s1 = Series((10, 3, 15, 21, 28),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        s2 = Series((100, 101), index=(21, 28))

        self.assertEqual(tuple(s1.iter_element().map_fill_iter(s2, fill_value=0)),
                (0, 0, 0, 100, 101))

        self.assertEqual(tuple(s1.iter_element().map_fill_iter_items(s2, fill_value=0)),
                (('a', 0), ('b', 0), ('c', 0), ('d', 100), ('e', 101))
                )



    #---------------------------------------------------------------------------
    def test_series_sort_index_a(self) -> None:

        s1 = Series((10, 3, 28, 21, 15),
                index=('a', 'c', 'b', 'e', 'd'),
                dtype=object,
                name='foo')

        s2 = s1.sort_index()
        self.assertEqual(s2.to_pairs(),
                (('a', 10), ('b', 28), ('c', 3), ('d', 15), ('e', 21)))
        self.assertEqual(s2.name, s1.name)

        s3 = s1.sort_values()
        self.assertEqual(s3.to_pairs(),
                (('c', 3), ('a', 10), ('d', 15), ('e', 21), ('b', 28)))
        self.assertEqual(s3.name, s1.name)


    def test_series_sort_index_b(self) -> None:

        index = IndexYearMonth.from_date_range('2017-12-15', '2018-03-15')
        s = Series(list('abcd'), index=index)

        post = s.sort_index(ascending=False)

        self.assertEqual(
                post.to_pairs(),
                ((np.datetime64('2018-03'), 'd'), (np.datetime64('2018-02'), 'c'), (np.datetime64('2018-01'), 'b'), (np.datetime64('2017-12'), 'a'))
                )

        self.assertEqual(post.index.__class__, IndexYearMonth)


    def test_series_sort_index_c(self) -> None:

        index = IndexHierarchy.from_product((0, 1), (10, 20))
        s = Series(list('abcd'), index=index)

        post = s.sort_index(ascending=False)

        self.assertEqual(post.to_pairs(),
            (((1, 20), 'd'), ((1, 10), 'c'), ((0, 20), 'b'), ((0, 10), 'a'))
            )
        self.assertEqual(post.index.__class__, IndexHierarchy)


    def test_series_sort_index_d(self) -> None:

        index = IndexHierarchy.from_product((0, 1), (10, 20), name='foo')
        s1 = Series(list('abcd'), index=index)
        s2 = s1.sort_index()
        self.assertEqual(s2.index.name, s1.index.name)





    #---------------------------------------------------------------------------
    def test_series_sort_values_a(self) -> None:

        index = IndexYearMonth.from_date_range('2017-12-15', '2018-03-15', name='foo')
        s = Series(list('abcd'), index=index)

        post = s.sort_values(ascending=False)

        self.assertEqual(
                post.to_pairs(),
                ((np.datetime64('2018-03'), 'd'), (np.datetime64('2018-02'), 'c'), (np.datetime64('2018-01'), 'b'), (np.datetime64('2017-12'), 'a'))
                )

        self.assertEqual(post.index.__class__, IndexYearMonth)
        self.assertEqual(post.index.name, 'foo')

    def test_series_sort_values_b(self) -> None:

        index = IndexHierarchy.from_product((0, 1), (10, 20))
        s = Series(list('abcd'), index=index)

        post = s.sort_values(ascending=False)

        self.assertEqual(post,
                (((1, 20), 'd'), ((1, 10), 'c'), ((0, 20), 'b'), ((0, 10), 'a'))
                )

        self.assertEqual(post.index.__class__, IndexHierarchy)



    def test_series_reversed(self) -> None:

        idx = tuple('abcd')
        s = Series(range(4), index=idx)
        self.assertTrue(tuple(reversed(s)) == tuple(reversed(idx)))

    #---------------------------------------------------------------------------

    def test_series_relabel_a(self) -> None:

        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))

        s2 = s1.relabel({'b': 'bbb'})
        self.assertEqual(s2.to_pairs(),
                (('a', 0), ('bbb', 1), ('c', 2), ('d', 3)))

        self.assertEqual(mloc(s2.values), mloc(s1.values))


    def test_series_relabel_b(self) -> None:

        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        s2 = s1.relabel({'a':'x', 'b':'y', 'c':'z', 'd':'q'})

        self.assertEqual(list(s2.items()),
            [('x', 0), ('y', 1), ('z', 2), ('q', 3)])


    def test_series_relabel_c(self) -> None:

        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        s2 = s1.relabel(IndexAutoFactory)
        self.assertEqual(
                s2.to_pairs(),
                ((0, 0), (1, 1), (2, 2), (3, 3))
                )

    def test_series_relabel_d(self) -> None:

        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        idx = IndexHierarchy.from_product(('a', 'b'), (1, 2))
        s2 = s1.relabel(idx)
        self.assertEqual(s2.to_pairs(),
            ((('a', 1), 0), (('a', 2), 1), (('b', 1), 2), (('b', 2), 3))
            )

    def test_series_relabel_e(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))

        s2 = s1.relabel(IndexAutoFactory)
        self.assertEqual(s2.to_pairs(),
                ((0, 0), (1, 1), (2, 2), (3, 3))
                )


    def test_series_relabel_f(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        # reuse the same instance
        s2 = s1.relabel(None)
        self.assertEqual(id(s1.index), id(s2.index))


    #---------------------------------------------------------------------------

    def test_series_rehierarch_a(self) -> None:

        colors = ('red', 'green')
        shapes = ('square', 'circle', 'triangle')
        textures = ('smooth', 'rough')

        s1 = sf.Series(range(12), index=sf.IndexHierarchy.from_product(shapes, colors, textures))

        s2 = s1.rehierarch((2,1,0))

        self.assertEqual(s2.to_pairs(),
                ((('smooth', 'red', 'square'), 0), (('smooth', 'red', 'circle'), 4), (('smooth', 'red', 'triangle'), 8), (('smooth', 'green', 'square'), 2), (('smooth', 'green', 'circle'), 6), (('smooth', 'green', 'triangle'), 10), (('rough', 'red', 'square'), 1), (('rough', 'red', 'circle'), 5), (('rough', 'red', 'triangle'), 9), (('rough', 'green', 'square'), 3), (('rough', 'green', 'circle'), 7), (('rough', 'green', 'triangle'), 11))
                )


    def test_series_rehierarch_b(self) -> None:
        s1 = sf.Series(range(8), index=sf.IndexHierarchy.from_product(('B', 'A'), (100, 2), ('iv', 'ii')))

        self.assertEqual(s1.rehierarch((2,1,0)).to_pairs(),
                ((('iv', 100, 'B'), 0), (('iv', 100, 'A'), 4), (('iv', 2, 'B'), 2), (('iv', 2, 'A'), 6), (('ii', 100, 'B'), 1), (('ii', 100, 'A'), 5), (('ii', 2, 'B'), 3), (('ii', 2, 'A'), 7))
                )

        self.assertEqual(s1.rehierarch((1,2,0)).to_pairs(),
                (((100, 'iv', 'B'), 0), ((100, 'iv', 'A'), 4), ((100, 'ii', 'B'), 1), ((100, 'ii', 'A'), 5), ((2, 'iv', 'B'), 2), ((2, 'iv', 'A'), 6), ((2, 'ii', 'B'), 3), ((2, 'ii', 'A'), 7))
                )


    def test_series_rehierarch_c(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        with self.assertRaises(RuntimeError):
            s1.rehierarch(())


    #---------------------------------------------------------------------------


    def test_series_get_a(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))
        self.assertEqual(s1.get('q'), None)
        self.assertEqual(s1.get('a'), 0)
        self.assertEqual(s1.get('f', -1), -1)


    def test_series_all_a(self) -> None:
        s1 = Series(range(4), index=('a', 'b', 'c', 'd'))

        self.assertEqual(s1.all(), False)
        self.assertEqual(s1.any(), True)


    def test_series_all_b(self) -> None:
        s1 = Series([True, True, np.nan, True], index=('a', 'b', 'c', 'd'), dtype=object)

        self.assertEqual(s1.all(skipna=False), True)
        self.assertEqual(s1.all(skipna=True), False)
        self.assertEqual(s1.any(), True)


    def test_series_unique_a(self) -> None:
        s1 = Series([10, 10, 2, 2], index=('a', 'b', 'c', 'd'), dtype=np.int64)

        self.assertEqual(s1.unique().tolist(), [2, 10])

        s2 = Series(['b', 'b', 'c', 'c'], index=('a', 'b', 'c', 'd'), dtype=object)
        self.assertEqual(s2.unique().tolist(), ['b', 'c'])


    def test_series_unique_b(self) -> None:
        s1 = Series([10, 10, 2, 2], index=('a', 'b', 'c', 'd'), dtype=np.int64)

        self.assertEqual(s1.unique().tolist(), [2, 10])

        s2 = Series(['b', 'b', 'c', 'c'], index=('a', 'b', 'c', 'd'), dtype=object)
        self.assertEqual(s2.unique().tolist(), ['b', 'c'])



    def test_series_duplicated_a(self) -> None:
        s1 = Series([1, 10, 10, 5, 2, 2],
                index=('a', 'b', 'c', 'd', 'e', 'f'), dtype=np.int64)

        # this is showing all duplicates, not just the first-found
        self.assertEqual(s1.duplicated().to_pairs(),
                (('a', False), ('b', True), ('c', True), ('d', False), ('e', True), ('f', True)))

        self.assertEqual(s1.duplicated(exclude_first=True).to_pairs(),
                (('a', False), ('b', False), ('c', True), ('d', False), ('e', False), ('f', True)))

        self.assertEqual(s1.duplicated(exclude_last=True).to_pairs(),
                (('a', False), ('b', True), ('c', False), ('d', False), ('e', True), ('f', False)))


    def test_series_duplicated_b(self) -> None:
        s1 = Series([5, 3, 3, 3, 7, 2, 2, 2, 1],
                index=('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'), dtype=np.int64)

        # this is showing all duplicates, not just the first-found
        self.assertEqual(s1.duplicated().to_pairs(),
                (('a', False), ('b', True), ('c', True),
                ('d', True), ('e', False), ('f', True),
                ('g', True), ('h', True), ('i', False),
                ))

        self.assertEqual(s1.duplicated(exclude_first=True).to_pairs(),
                (('a', False), ('b', False), ('c', True),
                ('d', True), ('e', False), ('f', False),
                ('g', True), ('h', True), ('i', False),
                ))

        self.assertEqual(s1.duplicated(exclude_last=True).to_pairs(),
                (('a', False), ('b', True), ('c', True),
                ('d', False), ('e', False), ('f', True),
                ('g', True), ('h', False), ('i', False),
                ))


    def test_series_drop_duplicated_a(self) -> None:
        s1 = Series([5, 3, 3, 3, 7, 2, 2, 2, 1],
                index=('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'), dtype=int)

        self.assertEqual(s1.drop_duplicated().to_pairs(),
                (('a', 5), ('e', 7), ('i', 1)))

        self.assertEqual(s1.drop_duplicated(exclude_first=True).to_pairs(),
                (('a', 5), ('b', 3), ('e', 7), ('f', 2), ('i', 1))
                )


    def test_series_reindex_add_level(self) -> None:
        s1 = Series(['a', 'b', 'c'])

        s2 = s1.relabel_add_level('I')
        self.assertEqual(s2.index.depth, 2)
        self.assertEqual(s2.to_pairs(),
                ((('I', 0), 'a'), (('I', 1), 'b'), (('I', 2), 'c')))

        s3 = s2.relabel_flat()
        self.assertEqual(s3.index.depth, 1)
        self.assertEqual(s3.to_pairs(),
                ((('I', 0), 'a'), (('I', 1), 'b'), (('I', 2), 'c')))


    def test_series_drop_level_a(self) -> None:
        s1 = Series(['a', 'b', 'c'],
                index=IndexHierarchy.from_labels([('A', 1), ('B', 1), ('C', 1)]))
        s2 = s1.relabel_drop_level(-1)
        self.assertEqual(s2.to_pairs(),
                (('A', 'a'), ('B', 'b'), ('C', 'c'))
                )


    def test_series_from_pandas_a(self) -> None:
        import pandas as pd

        pds = pd.Series([3,4,5], index=list('abc'))
        sfs = Series.from_pandas(pds)
        self.assertEqual(list(pds.items()), list(sfs.items()))

        # mutate Pandas
        pds['c'] = 50
        self.assertNotEqual(pds['c'], sfs['c'])

        # owning data
        pds = pd.Series([3,4,5], index=list('abc'))
        sfs = Series.from_pandas(pds, own_data=True)
        self.assertEqual(list(pds.items()), list(sfs.items()))

    def test_series_from_pandas_b(self) -> None:
        import pandas as pd

        pds = pd.Series([3,4,5], index=list('abc')).convert_dtypes()
        sfs = Series.from_pandas(pds)
        self.assertEqual(list(pds.items()), list(sfs.items()))

        # mutate Pandas
        pds['c'] = 50
        self.assertNotEqual(pds['c'], sfs['c'])

        # owning data
        pds = pd.Series([3,4,5], index=list('abc'))
        sfs = Series.from_pandas(pds, own_data=True)
        self.assertEqual(list(pds.items()), list(sfs.items()))

    def test_series_to_pandas_a(self) -> None:

        s1 = Series(range(4),
            index=IndexHierarchy.from_product(('a', 'b'), ('x', 'y')))
        df = s1.to_pandas()

        self.assertEqual(df.index.values.tolist(),
                [('a', 'x'), ('a', 'y'), ('b', 'x'), ('b', 'y')]
                )
        self.assertEqual(df.values.tolist(),
                [0, 1, 2, 3]
                )

    def test_series_to_pandas_b(self) -> None:

        from pandas import Timestamp

        s1 = Series(range(4),
            index=IndexDate(('2018-01-02', '2018-01-03', '2018-01-04', '2018-01-05')))
        df = s1.to_pandas()

        self.assertEqual(df.index.tolist(),
            [Timestamp('2018-01-02 00:00:00'), Timestamp('2018-01-03 00:00:00'), Timestamp('2018-01-04 00:00:00'), Timestamp('2018-01-05 00:00:00')]
            )
        self.assertEqual(df.values.tolist(),
            [0, 1, 2, 3]
            )



    def test_series_astype_a(self) -> None:

        s1 = Series(['a', 'b', 'c'])

        s2 = s1.astype(object)
        self.assertEqual(s2.to_pairs(),
                ((0, 'a'), (1, 'b'), (2, 'c')))
        self.assertTrue(s2.dtype == object)

        # we cannot convert to float
        with self.assertRaises(ValueError):
            s1.astype(float)

    def test_series_astype_b(self) -> None:

        s1 = Series([1, 3, 4, 0])

        s2 = s1.astype(bool)
        self.assertEqual(
                s2.to_pairs(),
                ((0, True), (1, True), (2, True), (3, False)))
        self.assertTrue(s2.dtype == bool)


    def test_series_min_max_a(self) -> None:

        s1 = Series([1, 3, 4, 0])
        self.assertEqual(s1.min(), 0)
        self.assertEqual(s1.max(), 4)


        s2 = sf.Series([-1, 4, None, np.nan])
        self.assertEqual(s2.min(), -1)
        with self.assertRaises(TypeError):
            s2.min(skipna=False)

        self.assertEqual(s2.max(), 4)
        with self.assertRaises(TypeError):
            s2.max(skipna=False)

        s3 = sf.Series([-1, 4, None])
        self.assertEqual(s3.min(), -1)
        with self.assertRaises(TypeError):
            s2.max(skipna=False)



    def test_series_min_max_b(self) -> None:
        # string objects work as expected; when fixed length strings, however, the do not

        s1 = Series(list('abc'), dtype=object)
        self.assertEqual(s1.min(), 'a')
        self.assertEqual(s1.max(), 'c')

        # get the same result from character arrays
        s2 = sf.Series(list('abc'))
        self.assertEqual(s2.min(), 'a')
        self.assertEqual(s2.max(), 'c')

    #---------------------------------------------------------------------------

    def test_series_clip_a(self) -> None:

        s1 = Series(range(6), index=list('abcdef'))

        self.assertEqual(s1.clip(lower=3).to_pairs(),
                (('a', 3), ('b', 3), ('c', 3), ('d', 3), ('e', 4), ('f', 5))
                )

        self.assertEqual(s1.clip(lower=-1).to_pairs(),
                (('a', 0), ('b', 1), ('c', 2), ('d', 3), ('e', 4), ('f', 5))
                )

        self.assertEqual(s1.clip(upper=-1).to_pairs(),
                (('a', -1), ('b', -1), ('c', -1), ('d', -1), ('e', -1), ('f', -1))
                )

        self.assertEqual(s1.clip(upper=3).to_pairs(),
                (('a', 0), ('b', 1), ('c', 2), ('d', 3), ('e', 3), ('f', 3))
                )


    def test_series_clip_b(self) -> None:
        s1 = Series(range(6), index=list('abcdef'))

        s2 = Series((2, 3, 0, -1, 8, 6), index=list('abcdef'))

        self.assertEqual(s1.clip(lower=s2).to_pairs(),
                (('a', 2), ('b', 3), ('c', 2), ('d', 3), ('e', 8), ('f', 6))
                )

        self.assertEqual(s1.clip(upper=s2).to_pairs(),
                (('a', 0), ('b', 1), ('c', 0), ('d', -1), ('e', 4), ('f', 5))
                )

        s3 = Series((2, 3, 0), index=list('abc'))

        self.assertEqual(s1.clip(lower=s3).to_pairs(),
                (('a', 2), ('b', 3), ('c', 2), ('d', 3), ('e', 4), ('f', 5))
                )

        self.assertEqual(s1.clip(upper=s3).to_pairs(),
                (('a', 0), ('b', 1), ('c', 0), ('d', 3), ('e', 4), ('f', 5))
                )


    def test_series_clip_c(self) -> None:
        s1 = Series(range(6), index=list('abcdef'))

        with self.assertRaises(RuntimeError):
            _ = s1.clip(lower=(2, 5))


    #---------------------------------------------------------------------------
    def test_series_pickle_a(self) -> None:
        s1 = Series(range(6), index=list('abcdef'))
        s2 = Series((2, 3, 0, -1, 8, 6), index=list('abcdef'))
        s3 = s2.astype(bool)


        for series in (s1, s2, s3):
            pbytes = pickle.dumps(series)
            series_new = pickle.loads(pbytes)
            for v in series: # iter labels
                # this compares series objects
                self.assertFalse(series_new.values.flags.writeable)
                self.assertEqual(series_new.loc[v], series.loc[v])


    #---------------------------------------------------------------------------

    def test_series_drop_loc_a(self) -> None:
        s1 = Series((2, 3, 0, -1, 8, 6), index=list('abcdef'))

        self.assertEqual(s1.drop.loc['d'].to_pairs(),
                (('a', 2), ('b', 3), ('c', 0), ('e', 8), ('f', 6)))

        self.assertEqual(s1.drop.loc['d':].to_pairs(),  # type: ignore  # https://github.com/python/typeshed/pull/3024
                (('a', 2), ('b', 3), ('c', 0)))

        self.assertEqual(s1.drop.loc['d':'e'].to_pairs(),  # type: ignore  # https://github.com/python/typeshed/pull/3024
                (('a', 2), ('b', 3), ('c', 0), ('f', 6)))

        self.assertEqual(s1.drop.loc[s1 > 0].to_pairs(),
                (('c', 0), ('d', -1)))


    def test_series_drop_loc_b(self) -> None:
        s1 = Series((2, 3, 0, -1), index=list('abcd'))
        s2 = s1._drop_iloc((s1 < 1).values)
        self.assertEqual(s2.to_pairs(), (('a', 2), ('b', 3)))



    def test_series_drop_iloc_a(self) -> None:
        s1 = Series((2, 3, 0, -1, 8, 6), index=list('abcdef'))

        self.assertEqual(s1.drop.iloc[-1].to_pairs(),
                (('a', 2), ('b', 3), ('c', 0), ('d', -1), ('e', 8))
                )
        self.assertEqual(s1.drop.iloc[2:].to_pairs(),
                (('a', 2), ('b', 3)))

        self.assertEqual(s1.drop.iloc[[0, 3]].to_pairs(),
                (('b', 3), ('c', 0), ('e', 8), ('f', 6)))



    #---------------------------------------------------------------------------

    def test_series_head_a(self) -> None:
        s1 = Series(range(100), index=reversed(range(100)))
        self.assertEqual(s1.head().to_pairs(),
                ((99, 0), (98, 1), (97, 2), (96, 3), (95, 4)))
        self.assertEqual(s1.head(2).to_pairs(),
                ((99, 0), (98, 1)))


    def test_series_tail_a(self) -> None:
        s1 = Series(range(100), index=reversed(range(100)))

        self.assertEqual(s1.tail().to_pairs(),
                ((4, 95), (3, 96), (2, 97), (1, 98), (0, 99)))

        self.assertEqual(s1.tail(2).to_pairs(),
                ((1, 98), (0, 99)))


    def test_series_roll_a(self) -> None:
        s1 = Series((2, 3, 0, -1, 8, 6), index=list('abcdef'))

        self.assertEqual(s1.roll(2).to_pairs(),
                (('a', 8), ('b', 6), ('c', 2), ('d', 3), ('e', 0), ('f', -1))
                )

        self.assertEqual(s1.roll(-2).to_pairs(),
                (('a', 0), ('b', -1), ('c', 8), ('d', 6), ('e', 2), ('f', 3))
                )

        # if the roll is a noop, we reuse the same array
        self.assertEqual(s1.mloc, s1.roll(len(s1)).mloc)


    def test_series_roll_b(self) -> None:
        s1 = Series((2, 3, 0, -1, 8, 6), index=list('abcdef'))

        self.assertEqual(s1.roll(2, include_index=True).to_pairs(),
            (('e', 8), ('f', 6), ('a', 2), ('b', 3), ('c', 0), ('d', -1))
            )

        self.assertEqual(s1.roll(-2, include_index=True).to_pairs(),
            (('c', 0), ('d', -1), ('e', 8), ('f', 6), ('a', 2), ('b', 3))
            )


    def test_series_shift_a(self) -> None:
        s1 = Series((2, 3, 0, -1, 8, 6), index=list('abcdef'))

        # if the shift is a noop, we reuse the same array
        self.assertEqual(s1.mloc, s1.shift(0).mloc)

        # default fill is NaN
        self.assertEqual(s1.shift(4).dtype,
                np.dtype('float64')
                )

        # import ipdb; ipdb.set_trace()
        self.assertEqual(s1.shift(4, fill_value=None).to_pairs(),
                (('a', None), ('b', None), ('c', None), ('d', None), ('e', 2), ('f', 3))
                )

        self.assertEqual(s1.shift(-4, fill_value=None).to_pairs(),
                (('a', 8), ('b', 6), ('c', None), ('d', None), ('e', None), ('f', None))
                )

        self.assertEqual(
                s1.shift(6, fill_value=None).to_pairs(),
                (('a', None), ('b', None), ('c', None), ('d', None), ('e', None), ('f', None))
                )

        self.assertEqual(
                s1.shift(-6, fill_value=None).to_pairs(),
                (('a', None), ('b', None), ('c', None), ('d', None), ('e', None), ('f', None))
                )

    #---------------------------------------------------------------------------
    def test_series_isin_a(self) -> None:

        s1 = Series((2, 3, 0, -1, 8, 6), index=list('abcdef'))

        self.assertEqual(s1.isin([]).to_pairs(),
            (('a', False), ('b', False), ('c', False), ('d', False), ('e', False), ('f', False))
            )

        self.assertEqual(s1.isin((-1, 8)).to_pairs(),
            (('a', False), ('b', False), ('c', False), ('d', True), ('e', True), ('f', False))
            )

        self.assertEqual(s1.isin(s1.values).to_pairs(),
            (('a', True), ('b', True), ('c', True), ('d', True), ('e', True), ('f', True))
            )


    def test_series_isin_b(self) -> None:

        s1 = Series(['a', 'b', 'c', 'd'])
        self.assertEqual(s1.isin(('b', 'c')).to_pairs(),
                ((0, False), (1, True), (2, True), (3, False)))

        self.assertEqual(s1.isin(('b', 'c', None)).to_pairs(),
                ((0, False), (1, True), (2, True), (3, False)))

        self.assertEqual(s1.isin(s1[[1, 2]].values).to_pairs(),
                ((0, False), (1, True), (2, True), (3, False)))

        self.assertEqual(s1.isin({'b', 'c'}).to_pairs(),
                ((0, False), (1, True), (2, True), (3, False)))


    def test_series_isin_c(self) -> None:

        s1 = Series(['a', 'b', 'c', 'd', 'a', 'b', 'c', 'd'])

        self.assertEqual(s1.isin(('a', 'd')).to_pairs(),
                ((0, True), (1, False), (2, False), (3, True), (4, True), (5, False), (6, False), (7, True)))


    def test_series_isin_d(self) -> None:
        s1 = Series((1, 1), index=list('ab'))
        lookup = {2,3,4,5,6,7,8,9,10,11,12,13}
        # Checks an edge case where if a numpy `assume_unique` flag is incorrectly passed, it returns the wrong result
        result = s1.isin(lookup)
        self.assertEqual(result.to_pairs(),
                (('a', False), ('b', False)))


    #---------------------------------------------------------------------------

    def test_series_to_html_a(self) -> None:

        s1 = Series((2, 3, 0, -1, 8, 6), index=list('abcdef'))

        post = s1.to_html(config=DisplayConfig(type_show=False, type_color=False))

        html = '<table border="1"><thead></thead><tbody><tr><th>a</th><td>2</td></tr><tr><th>b</th><td>3</td></tr><tr><th>c</th><td>0</td></tr><tr><th>d</th><td>-1</td></tr><tr><th>e</th><td>8</td></tr><tr><th>f</th><td>6</td></tr></tbody></table>'
        self.assertEqual(post.strip(), html.strip())


    def test_series_to_html_datatables_a(self) -> None:

        s1 = Series((2, 3, 0, -1, 8, 6), index=list('abcdef'))

        sio = StringIO()

        post = s1.to_html_datatables(sio, show=False)

        self.assertEqual(post, None)

        self.assertTrue(len(sio.read()) > 1400)


    def test_series_to_html_datatables_b(self) -> None:

        s1 = Series((2, 3, 0, -1, 8, 6), index=list('abcdef'))

        with temp_file('.html', path=True) as fp:
            s1.to_html_datatables(fp, show=False)
            with open(fp) as file:
                data = file.read()
                self.assertTrue('SFTable' in data)
                self.assertTrue(len(data) > 800)




    def test_series_disply_a(self) -> None:

        s1 = Series((2, 3), index=list('ab'), name='alt', dtype=np.int64)

        match = tuple(s1.display(DisplayConfig(type_color=False)))
        self.assertEqual(
            match,
            (['<Series: alt>'], ['<Index>', ''], ['a', '2'], ['b', '3'], ['<<U1>', '<int64>'])
            )

        s2 = Series(('a', 'b'), index=Index(('x', 'y'), name='bar'), name='foo')

        match = tuple(s2.display(DisplayConfig(type_color=False)))

        self.assertEqual(
            match,
            (['<Series: foo>'], ['<Index: bar>', ''], ['x', 'a'], ['y', 'b'], ['<<U1>', '<<U1>'])
            )


    def test_series_to_frame_a(self) -> None:

        s1 = Series((2, 3), index=list('ab'), name='alt')

        f1 = s1.to_frame()

        self.assertTrue(f1.__class__ is Frame)
        self.assertEqual(f1.columns.values.tolist(), ['alt'])
        self.assertEqual(f1.to_pairs(0),
            (('alt', (('a', 2), ('b', 3))),))

        self.assertTrue(s1.mloc == f1.mloc.tolist()[0])

    def test_series_to_frame_b(self) -> None:

        s1 = Series((2, 3), index=list('ab'), name='alt')

        f1 = s1.to_frame_go()

        self.assertTrue(f1.__class__ is FrameGO)
        self.assertEqual(f1.columns.values.tolist(), ['alt'])
        self.assertEqual(f1.to_pairs(0),
            (('alt', (('a', 2), ('b', 3))),))

        self.assertTrue(s1.mloc == f1.mloc.tolist()[0])

    def test_series_to_frame_c(self) -> None:

        s1 = Series((2, 3, 4), index=list('abc'), name='alt')

        f2 = s1.to_frame(axis=0)
        self.assertEqual(f2.to_pairs(0),
            (('a', (('alt', 2),)), ('b', (('alt', 3),)), ('c', (('alt', 4),))))

    def test_series_to_frame_d(self) -> None:

        s1 = Series((2, 3, 4), index=list('abc'), name='alt')
        with self.assertRaises(NotImplementedError):
            s1.to_frame(axis=None)  # type: ignore


    def test_series_to_frame_go_a(self) -> None:
        a = sf.Series((1, 2, 3), name='a')
        f = a.to_frame_go(axis=0)
        f['b'] = 'b'

        self.assertEqual(f.to_pairs(0),
                ((0, (('a', 1),)), (1, (('a', 2),)), (2, (('a', 3),)), ('b', (('a', 'b'),)))
                )


    def test_series_from_concat_a(self) -> None:
        s1 = Series((2, 3, 0,), index=list('abc'))
        s2 = Series((10, 20), index=list('de'))
        s3 = Series((8, 6), index=list('fg'))

        s = Series.from_concat((s1, s2, s3))

        self.assertEqual(s.to_pairs(),
                (('a', 2), ('b', 3), ('c', 0), ('d', 10), ('e', 20), ('f', 8), ('g', 6))
                )

    def test_series_from_concat_b(self) -> None:
        s1 = Series((2, 3, 0,), index=list('abc'))
        s2 = Series(('10', '20'), index=list('de'))
        s3 = Series((8, 6), index=list('fg'))

        s = Series.from_concat((s1, s2, s3))

        self.assertEqual(s.to_pairs(),
                (('a', 2), ('b', 3), ('c', 0), ('d', '10'), ('e', '20'), ('f', 8), ('g', 6))
                )


    def test_series_from_concat_c(self) -> None:
        s1 = Series((2, 3, 0,), index=list('abc'))
        s2 = Series(('10', '20'), index=list('de'))
        s3 = Series((8, 6), index=(1, 2))

        s = Series.from_concat((s1, s2, s3))

        self.assertEqual(s.to_pairs(),
                (('a', 2), ('b', 3), ('c', 0), ('d', '10'), ('e', '20'), (1, 8), (2, 6))
                )

    def test_series_from_concat_d(self) -> None:
        s1 = Series((2, 3, 0,), index=list('abc')).relabel_add_level('i')
        s2 = Series(('10', '20', '100'), index=list('abc')).relabel_add_level('ii')

        s3 = Series.from_concat((s1, s2))

        self.assertEqual(s3.to_pairs(),
                ((('i', 'a'), 2), (('i', 'b'), 3), (('i', 'c'), 0), (('ii', 'a'), '10'), (('ii', 'b'), '20'), (('ii', 'c'), '100'))
                )

    def test_series_from_concat_e(self) -> None:
        s1 = Series((2, 3, 0,), index=list('abc'))
        s2 = Series((10, 20), index=list('de'))
        s3 = Series((8, 6), index=list('fg'))


        s = Series.from_concat((s1, s2, s3), index=IndexAutoFactory)

        self.assertEqual(s.to_pairs(),
                ((0, 2), (1, 3), (2, 0), (3, 10), (4, 20), (5, 8), (6, 6))
                )

    def test_series_from_concat_f(self) -> None:
        s1 = Series((2, 3, 0,), index=list('abc'))
        s2 = Series((10, 20), index=list('de'))
        s3 = Series((8, 6), index=list('fg'))

        s = Series.from_concat((s1, s2, s3), index=list('pqrstuv'))

        self.assertEqual(s.to_pairs(),
                (('p', 2), ('q', 3), ('r', 0), ('s', 10), ('t', 20), ('u', 8), ('v', 6))
                )

    def test_series_from_concat_g(self) -> None:

        s1 = Series.from_concat([])
        self.assertEqual((0,), s1.shape)

        s2 = Series.from_concat([], index=[])
        self.assertEqual((0,), s2.shape)
        self.assertEqual((0,), s2.index.shape)

        s3 = Series.from_concat([], name='s3')
        self.assertEqual((0,), s3.shape)
        self.assertEqual('s3', s3.name)

        s4 = Series.from_concat([], index=[], name='s4')
        self.assertEqual((0,), s4.shape)
        self.assertEqual((0,), s4.index.shape)
        self.assertEqual('s4', s4.name)


    #---------------------------------------------------------------------------

    def test_series_iter_group_a(self) -> None:

        s1 = Series((10, 4, 10, 4, 10),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        group = tuple(s1.iter_group(axis=0))

        self.assertEqual(group[0].to_pairs(),
                (('a', 10), ('c', 10), ('e', 10)))

        self.assertEqual(group[1].to_pairs(),
                (('b', 4), ('d', 4)))

        with self.assertRaises(AxisInvalid):
            tuple(s1.iter_group(axis=1))

        with self.assertRaises(TypeError):
            tuple(s1.iter_group('sdf')) #type: ignore

        with self.assertRaises(TypeError):
            tuple(s1.iter_group(foo='sdf')) #type: ignore


    #---------------------------------------------------------------------------
    def test_series_iter_group_index_a(self) -> None:

        s1 = Series((10, 3, 15, 21, 28),
                index=('a', 'b', 'c', 'd', 'e'),
                dtype=object)

        post = tuple(s1.iter_group_labels_items())
        self.assertTrue(len(post), len(s1))
        self.assertTrue(all(isinstance(x[1], Series) for x in post))

    def test_series_iter_group_index_b(self) -> None:

        colors = ('red', 'green')
        shapes = ('square', 'circle', 'triangle')
        s1 = sf.Series(range(6), index=sf.IndexHierarchy.from_product(shapes, colors))

        post = tuple(s1.iter_group_labels(depth_level=0))
        self.assertTrue(len(post), 3)

        self.assertEqual(s1.iter_group_labels(depth_level=0).apply(np.sum).to_pairs(),
                (('circle', 5), ('square', 1), ('triangle', 9))
                )

        self.assertEqual(s1.iter_group_labels(depth_level=1).apply(np.sum).to_pairs(),
                (('green', 9), ('red', 6))
                )

    def test_series_iter_group_index_c(self) -> None:

        colors = ('red', 'green')
        shapes = ('square', 'circle', 'triangle')
        textures = ('smooth', 'rough')

        s1 = sf.Series(range(12),
                index=sf.IndexHierarchy.from_product(shapes, colors, textures)
                )

        post = tuple(s1.iter_group_labels(depth_level=[0, 2]))
        self.assertTrue(len(post), 6)

        self.assertEqual(s1.iter_group_labels(depth_level=[0, 2]).apply(np.sum).to_pairs(),
                ((('circle', 'rough'), 12), (('circle', 'smooth'), 10), (('square', 'rough'), 4), (('square', 'smooth'), 2), (('triangle', 'rough'), 20), (('triangle', 'smooth'), 18))
                )


    def test_series_locmin_a(self) -> None:
        s1 = Series((2, 3, 0,), index=list('abc'))
        self.assertEqual(s1.loc_min(), 'c')
        self.assertEqual(s1.iloc_min(), 2)
        self.assertEqual(s1.loc_max(), 'b')
        self.assertEqual(s1.iloc_max(), 1)

    def test_series_locmin_b(self) -> None:
        s1 = Series((2, np.nan, 0, -1), index=list('abcd'))
        self.assertEqual(s1.loc_min(), 'd')
        self.assertEqual(s1.iloc_min(), 3)
        self.assertEqual(s1.loc_max(), 'a')
        self.assertEqual(s1.iloc_max(), 0)


    def test_series_locmin_c(self) -> None:
        s1 = Series((2, np.nan, 0,), index=list('abc'))

        with self.assertRaises(RuntimeError):
            s1.loc_min(skipna=False)

        with self.assertRaises(RuntimeError):
            s1.loc_max(skipna=False)


    def test_series_from_concat_items_a(self) -> None:

        s1 = Series((2, 3, 0,), index=list('abc'))
        s2 = Series((2, np.nan, 0, -1), index=list('abcd'))

        s3 = Series.from_concat_items((('x', s1), ('y', s2)))

        self.assertAlmostEqualItems(s3.to_pairs(),
                ((('x', 'a'), 2.0), (('x', 'b'), 3.0), (('x', 'c'), 0.0), (('y', 'a'), 2.0), (('y', 'b'), np.nan), (('y', 'c'), 0.0), (('y', 'd'), -1.0))
                )

        self.assertAlmostEqualItems(s3[HLoc[:, 'b']].to_pairs(),
                ((('x', 'b'), 3.0), (('y', 'b'), np.nan)))


    def test_series_from_concat_items_b(self) -> None:
        s1 = Series.from_concat_items([])

        self.assertEqual((0,), s1.shape)


    #---------------------------------------------------------------------------

    def test_series_axis_window_items_a(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))

        post = tuple(s1._axis_window_items(as_array=True, size=2, step=1, label_shift=0))

        # first window has second label, and first two values
        self.assertEqual(post[0][1].tolist(), [1, 2])
        self.assertEqual(post[0][0], 'b')

        self.assertEqual(post[-1][1].tolist(), [19, 20])
        self.assertEqual(post[-1][0], 't')


    def test_series_axis_window_items_b(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))

        post = tuple(s1._axis_window_items(as_array=True, size=2, step=1, label_shift=-1))

        # first window has first label, and first two values
        self.assertEqual(post[0][1].tolist(), [1, 2])
        self.assertEqual(post[0][0], 'a')

        self.assertEqual(post[-1][1].tolist(), [19, 20])
        self.assertEqual(post[-1][0], 's')



    def test_series_axis_window_items_c(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))

        # this is an expanding window anchored at the first index
        post = tuple(s1._axis_window_items(as_array=True, size=1, step=0, size_increment=1))

        self.assertEqual(post[0][0], 'a')
        self.assertEqual(post[0][1].tolist(), [1])

        self.assertEqual(post[-1][0], 't')
        self.assertEqual(post[-1][1].tolist(), list(range(1, 21)))



    def test_series_axis_window_items_d(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))

        post = tuple(s1._axis_window_items(as_array=True, size=5, start_shift=-5, window_sized=False))

        self.assertEqual(post[0][0], 'a')
        self.assertEqual(post[0][1].tolist(), [1])

        self.assertEqual(post[1][0], 'b')
        self.assertEqual(post[1][1].tolist(), [1, 2])

        self.assertEqual(post[-1][0], 't')
        self.assertEqual(post[-1][1].tolist(), [16, 17, 18, 19, 20])



    def test_series_axis_window_items_e(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))

        # start shift needs to be 1 less than window to go to start of window
        post = tuple(s1._axis_window_items(as_array=True, size=5, label_shift=-4, window_sized=False))

        self.assertEqual(post[0][0], 'a')
        self.assertEqual(post[0][1].tolist(), [1, 2, 3, 4, 5])

        self.assertEqual(post[1][0], 'b')
        self.assertEqual(post[1][1].tolist(), [2, 3, 4, 5, 6])

        self.assertEqual(post[-1][0], 't')
        self.assertEqual(post[-1][1].tolist(), [20])



    def test_series_axis_window_items_f(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))

        # start shift needs to be 1 less than window to go to start of window
        post = tuple(s1._axis_window_items(as_array=True, size=5, label_shift=-4, window_sized=True))

        self.assertEqual(post[0][0], 'a')
        self.assertEqual(post[0][1].tolist(), [1, 2, 3, 4, 5])

        self.assertEqual(post[1][0], 'b')
        self.assertEqual(post[1][1].tolist(), [2, 3, 4, 5, 6])

        self.assertEqual(post[-1][0], 'p')
        self.assertEqual(post[-1][1].tolist(), [16, 17, 18, 19, 20])


    def test_series_axis_window_items_g(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))

        with self.assertRaises(RuntimeError):
            tuple(s1._axis_window_items(as_array=True, size=0))

        with self.assertRaises(RuntimeError):
            tuple(s1._axis_window_items(size=2, as_array=True, step=-1))


    def test_series_axis_window_items_h(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))

        post = tuple(s1._axis_window_items(as_array=True, size=1))
        self.assertEqual(post[0][0], 'a')
        self.assertEqual(post[0][1].tolist(), [1])

        self.assertEqual(post[-1][0], 't')
        self.assertEqual(post[-1][1].tolist(), [20])



    def test_series_axis_window_items_i(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))
        # step equal to window size produces adaject windows
        post = tuple(s1._axis_window_items(as_array=True, size=3, step=3))

        self.assertEqual(post[0][0], 'c')
        self.assertEqual(post[0][1].tolist(), [1, 2, 3])

        self.assertEqual(post[1][0], 'f')
        self.assertEqual(post[1][1].tolist(), [4, 5, 6])

        self.assertEqual(post[-1][0], 'r')
        self.assertEqual(post[-1][1].tolist(), [16, 17, 18])


    def test_series_axis_window_items_j(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))
        # adjacent windows with label on first value, keeping incomplete windows
        post = tuple(s1._axis_window_items(as_array=True, size=3, step=3, label_shift=-2, window_sized=False))

        self.assertEqual(post[0][0], 'a')
        self.assertEqual(post[0][1].tolist(), [1, 2, 3])

        self.assertEqual(post[1][0], 'd')
        self.assertEqual(post[1][1].tolist(), [4, 5, 6])

        self.assertEqual(post[-1][0], 's')
        self.assertEqual(post[-1][1].tolist(), [19, 20])



    def test_series_axis_window_items_k(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))
        # adjacent windows with label on first value, keeping incomplete windows
        post = tuple(s1._axis_window_items(as_array=True, size=3, window_valid=lambda w: np.sum(w) % 2 == 1))

        self.assertEqual(post[0][0], 'd')
        self.assertEqual(post[0][1].tolist(), [2, 3, 4])

        self.assertEqual(post[1][0], 'f')
        self.assertEqual(post[1][1].tolist(), [4, 5, 6])

        self.assertEqual(post[-1][0], 't')
        self.assertEqual(post[-1][1].tolist(), [18, 19, 20])



    def test_series_axis_window_items_m(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))
        # adjacent windows with label on first value, keeping incomplete windows
        weight = np.array([.25, .5, .5, .25])
        post = tuple(s1._axis_window_items(as_array=True, size=4, window_func=lambda a: a * weight))

        self.assertEqual(post[0][0], 'd')
        self.assertEqual(post[0][1].tolist(), [0.25, 1, 1.5, 1])

        self.assertEqual(post[-1][0], 't')
        self.assertEqual(post[-1][1].tolist(), [4.25, 9, 9.5, 5])

    #---------------------------------------------------------------------------

    def test_series_iter_window_array_a(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))

        self.assertEqual(
                tuple(tuple(a) for a in s1.iter_window_array(size=2)),
                ((1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 20))
                )

    def test_series_iter_window_array_b(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))
        s2 = s1.iter_window_array(size=2).apply(np.mean)
        self.assertEqual(s2.to_pairs(),
                (('b', 1.5), ('c', 2.5), ('d', 3.5), ('e', 4.5), ('f', 5.5), ('g', 6.5), ('h', 7.5), ('i', 8.5), ('j', 9.5), ('k', 10.5), ('l', 11.5), ('m', 12.5), ('n', 13.5), ('o', 14.5), ('p', 15.5), ('q', 16.5), ('r', 17.5), ('s', 18.5), ('t', 19.5))
        )


    #---------------------------------------------------------------------------
    def test_series_iter_window_a(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))

        self.assertEqual(
                tuple(s.index.values.tolist() for s in s1.iter_window(size=2)), # type: ignore
                (['a', 'b'], ['b', 'c'], ['c', 'd'], ['d', 'e'], ['e', 'f'], ['f', 'g'], ['g', 'h'], ['h', 'i'], ['i', 'j'], ['j', 'k'], ['k', 'l'], ['l', 'm'], ['m', 'n'], ['n', 'o'], ['o', 'p'], ['p', 'q'], ['q', 'r'], ['r', 's'], ['s', 't'])
                )

        self.assertEqual(
            s1.iter_window(size=5, label_shift=-4, step=6, window_sized=False
                    ).apply(lambda s: len(s.index)).to_pairs(),
            (('a', 5), ('g', 5), ('m', 5), ('s', 2))
        )


    def test_series_iter_window_b(self) -> None:

        s1 = Series(range(10), index=self.get_letters(10))

        with self.assertRaises(TypeError):
            s1.iter_window() #type: ignore

        with self.assertRaises(TypeError):
            s1.iter_window(3) #type: ignore

        with self.assertRaises(TypeError):
            s1.iter_window(foo=3) #type: ignore

        self.assertEqual(
                tuple(x.to_pairs() for x in s1.iter_window(size=2, step=2)), #type: ignore
                ((('a', 0), ('b', 1)), (('c', 2), ('d', 3)), (('e', 4), ('f', 5)), (('g', 6), ('h', 7)), (('i', 8), ('j', 9)))
                )

    def test_series_iter_window_c(self) -> None:

        s1 = Series(range(1, 21), index=self.get_letters(20))

        self.assertEqual(
                tuple(w.tolist() for w in s1.iter_window_array( #type: ignore
                        size=7,
                        step=7,
                        window_sized=False,
                        label_shift=-6,
                        )),
                ([1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12, 13, 14], [15, 16, 17, 18, 19, 20])
                )


    def test_series_iter_window_d(self) -> None:
        post1 = sf.Series(range(12)).iter_window_array(
                size=5,
                start_shift=-10,
                window_sized=True).apply(np.mean)

        self.assertEqual(post1.to_pairs(),
                ((4, 2.0), (5, 3.0), (6, 4.0), (7, 5.0), (8, 6.0), (9, 7.0), (10, 8.0), (11, 9.0)))

        post2 = sf.Series(range(12)).iter_window_array(
                size=5,
                start_shift=0,
                window_sized=True).apply(np.mean)

        self.assertEqual(post2.to_pairs(),
                ((4, 2.0), (5, 3.0), (6, 4.0), (7, 5.0), (8, 6.0), (9, 7.0), (10, 8.0), (11, 9.0)))


    #---------------------------------------------------------------------------
    def test_series_bool_a(self) -> None:
        s1 = Series(range(1, 21), index=self.get_letters(20))
        self.assertTrue(bool(s1))

        s2 = Series(())
        self.assertFalse(bool(s2))


if __name__ == '__main__':
    unittest.main()
