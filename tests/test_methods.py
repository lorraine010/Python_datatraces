import datetime
import nose
import traces
import unittest
from future.utils import listitems, iteritems

key_list = [
    datetime.datetime(2012, 1, 7),
    datetime.datetime(2012, 2, 13),
    datetime.datetime(2012, 3, 20),
    datetime.datetime(2012, 4, 10),
]
numeric_types = {
    int: [1, 2, 3, 0],
    float: [1.0, 2.0, 3.0, 0.0],
    bool: [True, False, True, False],
    # complex: [complex(1, 0), complex(1, 1), complex(0, 1)],
}
non_numeric_hashable_types = {
    str: ['a', 'b', 'c', ''],
    tuple: [('a', 1), ('b', 2), ('c', 3), ()],
}
unhashable_types = {
    list: [[1, 1], [2, 2], [3, 3], []],
    dict: [{'a': 1}, {'b': 2}, {'c': 3}, {}],
    set: [{1}, {1, 2}, {1, 2, 3}, set()],
}
all_types = dict(listitems(numeric_types) +
                 listitems(non_numeric_hashable_types) + listitems(unhashable_types))


def _make_ts(type_, key_list, value_list):
    ts = traces.TimeSeries(default_type=type_)
    for t, v in zip(key_list, value_list):
        ts[t] = v
    return ts


def frange(x, y, jump):
    while x < y:
        yield x
        x += jump


class TestTraces(unittest.TestCase):

    def test_mean(self):

        # numberic hashable types should work
        for type_, value_list in iteritems(numeric_types):
            ts = _make_ts(type_, key_list, value_list)
            ts.distribution(key_list[0], key_list[-1])
            ts.mean(key_list[0], key_list[-1])

        # non-numeric hashable types should raise type error on mean, but
        # distribution should work
        for type_, value_list in iteritems(non_numeric_hashable_types):
            ts = _make_ts(type_, key_list, value_list)
            ts.distribution(key_list[0], key_list[-1])
            nose.tools.assert_raises(TypeError, ts.mean, key_list[0], key_list[1])

        # non-numeric unhashable types should raise error on distribution
        # and mean
        for type_, value_list in iteritems(unhashable_types):
            ts = _make_ts(type_, key_list, value_list)
            nose.tools.assert_raises(TypeError, ts.distribution,
                                     key_list[0], key_list[1])
            nose.tools.assert_raises(TypeError, ts.mean,
                                     key_list[0], key_list[1])

    def test_regularize(self): # TODO: Need to fix regularize
        time_list = [
            datetime.datetime(2016, 1, 1, 1, 1, 2),
            datetime.datetime(2016, 1, 1, 1, 1, 3),
            datetime.datetime(2016, 1, 1, 1, 1, 8),
            datetime.datetime(2016, 1, 1, 1, 1, 10)
        ]
        ts = _make_ts(int, time_list, [1, 2, 3, 0])

        def curr_time(i):
            return datetime.datetime(2016, 1, 1, 1, 1, i)

        # Check first arguments
        assert ts.regularize(2, 1, time_list[0], time_list[-1]) == [
            (curr_time(i),
             ts.mean(curr_time(i)-datetime.timedelta(seconds=1),
                     curr_time(i)+datetime.timedelta(seconds=1))) for i in range(2,11)]

        assert ts.regularize(0.2, 1, time_list[0], time_list[-1]) == [
            (curr_time(i),
             ts.mean(curr_time(i) - datetime.timedelta(seconds=.1),
                     curr_time(i) + datetime.timedelta(seconds=.1))) for i in range(2,11)]

        nose.tools.assert_raises(ValueError, ts.regularize, -1, 1, time_list[0], time_list[-1])

        # Check second arguments
        assert ts.regularize(1, 2, time_list[0], time_list[-1]) == [
            (curr_time(i),
             ts.mean(curr_time(i) - datetime.timedelta(seconds=.5),
                     curr_time(i) + datetime.timedelta(seconds=.5))) for i in range(2, 11, 2)]

        nose.tools.assert_raises(TypeError, ts.regularize, 1, 1.4, time_list[0], time_list[-1])
        nose.tools.assert_raises(ValueError, ts.regularize, 1, -1, time_list[0], time_list[-1])
        nose.tools.assert_raises(ValueError, ts.regularize, 1, 20, time_list[0], time_list[-1])

        # Check third and fourth arguments
        nose.tools.assert_raises(ValueError, ts.regularize, 1, 1, time_list[3], time_list[0])

        assert ts.regularize(2, 1, curr_time(5), curr_time(10)) == [
            (curr_time(i),
             ts.mean(curr_time(i) - datetime.timedelta(seconds=1),
                     curr_time(i) + datetime.timedelta(seconds=1))) for i in range(5, 11)]

        assert ts.regularize(2, 1, curr_time(2), curr_time(5)) == [
            (curr_time(i),
             ts.mean(curr_time(i) - datetime.timedelta(seconds=1),
                     curr_time(i) + datetime.timedelta(seconds=1))) for i in range(2, 6)]

        assert ts.regularize(2, 1, curr_time(0), curr_time(13)) == [
            (curr_time(i),
             ts.mean(curr_time(i) - datetime.timedelta(seconds=1),
                     curr_time(i) + datetime.timedelta(seconds=1))) for i in range(0, 14)]

    def test_to_bool(self):

        answer = {}
        for type_, value_list in iteritems(all_types):
            answer[type_] = [True if i else False for i in value_list]

        # numberic hashable types should work
        for type_, value_list in iteritems(all_types):
            ts = _make_ts(type_, key_list, value_list)
            result = ts.to_bool()
            values = [v for (k, v) in result.items()]
            assert answer[type_] == values
