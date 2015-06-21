from humblematch import WrapObj, Any, OR, w
import collections
import pytest


def test_w_single_value():
    assert(w(5) == 5)
    assert(w(5.0) == 5)
    assert(w("hello") == "hello")
    assert(w(float("inf")) == float("inf"))
    assert(w(10.23) == 10.23)
    # assert(w("abhas") == u"abhas")

    assert(w(object()) != object())
    assert(w(5) != "asd")
    assert(w(10) != 5)
    assert(w(10) != [10])
    assert(w(10) != {"a": 10})
    assert(w("5") != 5)

    # check that true and false is implemented correctly, i.e. is opp
    # todo add to all test collections
    assert((w(5) != 5) != (w(5) == 5))
    assert((w(5) != "asd") != (w(5) == "asd"))


def test_w_single_type():
    assert(w(int) == 5)
    assert(w(float) == 5.0)
    assert(w(float) == float("inf"))

    assert(w(int) != int)
    assert(w(float) != float)
    assert(w(TypeError) != TypeError)

    assert(w(int) != 2.33)
    assert(w(int) != "abhas")
    assert(w(int) != [1, 2, 3])

    assert(w(Any) == 5)
    assert(w(Any) == "try")
    assert(w(Any) == [[1]])

    assert(w(Any) == type)
    assert(w(Any) == (lambda: None))
    assert(w(Any) == Any)


def test_w_list_value():
    assert(w([5]) == [5])
    assert(w([1, 2]) == [1, 2])
    assert(w([1, 2]) == (1, 2))
    assert(w([1, 2]) == list([1, 2]))

    assert(w([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5])
    assert(w([5, 25.25]) == [5, 25.25])

    assert(w([5]) != 5)


def test_w_list_mixed():
    assert(w([int, 50]) == [200, 50])
    assert(w([int, 50, int]) == [200, 50, 201])
    assert(w([list, 50]) == [[200], 50])
    assert(w([list, 50]) == [[200, None, "whatever"], 50])

    assert(w([list, 50]) != [200, 50])
    assert(w([int, 50]) != [200, 500])

    assert((w([list, 50]) != [[200], 50]) != (w([list, 50]) == [[200], 50]))


def test_w_times():
    # write many more

    with pytest.raises(TypeError):
        # data in wrapmultiobj must be iterable
        assert(w({"a": int}).times(3) == [1, 2, 3])


def test_OR():
    assert(isinstance(5, OR(int)) is True)
    assert(isinstance(5, OR(int, int)) is True)
    assert(isinstance(5, OR([int, int])) is True)
    assert(isinstance(5, OR(int, 5)) is True)
    assert(isinstance(5, OR(float, 5)) is True)

    # float(5.0)=5.0
    # float.__eq__(int) is true if they are value equivalent
    assert(isinstance(5, OR(float, 5.000)) is True)
    assert(isinstance(5, OR(float, float(5.000))) is True)

    assert(isinstance(5, OR([float, int])) is True)
    assert(isinstance(5.36, OR([float, int])) is True)
    assert(isinstance("5.36", OR([str, int])) is True)
    assert(isinstance("5.36", OR(collections.Iterable)) is True)
    assert(isinstance([2], OR(collections.Iterable)) is True)
    assert(isinstance(2.35, OR(float, collections.Iterable)) is True)
    assert(isinstance([2], OR(float, collections.Iterable)) is True)

    assert(isinstance(5, OR(float)) is False)
    assert(isinstance(5, OR(float, 6)) is False)
    assert(isinstance(5, OR(float, 5.0000000000001)) is False)
    assert(isinstance(5.36, OR(collections.Iterable)) is False)
    assert(isinstance((2, 3), tuple) is True)


def test_OR_internal():
    assert(OR(int).list_match_type == OR([int]).list_match_type)
    assert(OR(int, str).list_match_type == (int, str))


def test_OR_times():
    assert((w([OR(int, 2.35).times(2, 5)]) == [9, 2]) is True)
    assert((w([OR(int, 2.35).times(2, 5)]) == [9, 2.35]) is True)
    assert((w([OR(int, 2.35).times(2, 5)]) == [9, 2.35, 9, 9]) is True)

    assert((w([OR(int, 2.35).times(2, 5)]) == [9, 5.05]) is False)
    assert((w([OR(int, 2.35).times(2, 5)]) == [9]) is False)
    assert((w([OR(int, 2.35).times(2, 5)]) == [9, 2.35, 9, 9, 9]) is False)


def test_ANY_times():
    assert((w([Any.times(2, 5)]) == [9, 2]) is True)
    assert((w([Any.times(2, 5)]) == [9, 2.35]) is True)

    assert((w([Any.times(2, 5)]) == [9]) is False)
    assert((w([Any.times(2, 5)]) == [9, 2.35, 6, "io", "asd"]) is False)


def test_repeat_twice():
    with pytest.raises(TypeError):
        assert(w([1, OR(int).times(0, float("inf")), OR(int).times(0, float("inf")), 5]) == [1, 6, 6, 6, 6, 5])

    # should pass later
    with pytest.raises(TypeError):
        assert(w([1, OR(int).times(3), OR(int).times(1), 5]) == [1, 6, 6, 6, 6, 5])


def test_w_extra_wrap():
    assert(w([1, w(2)]) == [1, 2])
    assert(w([1, w(2)]) == (1, 2))
    assert(w([w(1), 2]) == list([1, 2]))
    assert(OR(int, str).list_match_type == OR([int, str]).list_match_type)


def test_dict():
    assert(w({"a": int}) == {"a": 20})
    assert(w({"a": int, "b": float}) == {"a": 20, "b": 25.25})
    assert(w({"a": int, "b": list}) == {"a": 20, "b": [25.25]})
    assert(w({"a": int, "b": [int]}) == {"a": 20, "b": [25]})
    assert(w({"a": int, "b": [w([int]).times(3)]}) == {"a": 20, "b": [25, 3, 67]})
    assert(w({"a": int, "b": {"f": float}}) == {"a": 20, "b": {"f": 25.25}})

    # shouldnt complain about extras
    assert(w({"a": int}) == {"a": 20, "b": 25.25})

    assert(w({"a": int, "b": list}) != {"a": 20, "b": 25.25})
    assert(w({"a": int, "q": list}) != {"a": 20, "b": [2]})
    assert(w({"a": int, "b": [int]}) != {"a": 20, "b": [25.25]})
    assert(w({"a": int, "b": [float]}) != {"a": 20, "b": ["25.25"]})
    assert(w({"a": int, "b": [w([int]).times(3)]}) != {"a": 20, "b": [25, 67]})

# write test-
# mul insted of times


def test_as_obj():
    class object2(object):
        pass

    test_obj = object2()
    test_obj.a = 20
    assert(w({"a": int}).as_obj() == test_obj)
    assert(w({"a": int}).as_obj() != {"a": 20})
    assert(w({"a": float}).as_obj() != test_obj)
    assert(w({"a": int, "b": Any}).as_obj() != test_obj)

    test_obj.b = "qwerty"
    assert(w({"a": int, "b": Any}).as_obj() == test_obj)


def test_w_wrapObj():
    assert(w is WrapObj)


def test_save_as():
    dict_match = (w(int).save_as("a") == 5)
    assert(dict_match["a"] == 5)

    dict_match = (w([int, w(float).save_as("a")]) == [5, 10.23])
    assert(dict_match["a"] == 10.23)

    dict_match = (w([w(int), w(float).save_as("a")]) == [5, 10.23])
    assert(dict_match["a"] == 10.23)

    dict_match = (w([{"what": w(int).save_as("b")}, w(float).save_as("a")]) == [{"what": 5}, 10.23])
    assert(dict_match["b"] == 5 and dict_match["a"] == 10.23)
    with pytest.raises(AssertionError):
        assert(dict_match["b"] == 15)
    with pytest.raises(AssertionError):
        assert(dict_match["a"] == 5)
    with pytest.raises(AssertionError):
        assert(dict_match["a"] == 10)

    dict_match = (w([{"what": w(int).save_as("a")}, w(float).save_as("a")]) == [{"what": 5}, 10.23])
    assert(dict_match["a"] == 10.23)

    dict_match = (w([[int, w(int).save_as("b")], float]) == [[5, 99], 10.23])
    assert(dict_match["b"] == 99)

    dict_match = (w([w(int).save_as("a")]).times(2) == [2, 3])
    assert(dict_match["a"] != 3)
    assert(dict_match["a"] == [2, 3])

    dict_match_1 = (w([w([int]).times(2).save_as("b")]) == [5, 12])
    dict_match_2 = (w([w([int]).save_as("b").times(2)]) == [5, 12])
    assert(dict_match_1["b"] == [5, 12])
    assert(dict_match_1 == dict_match_2)
