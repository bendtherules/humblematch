from __future__ import print_function
from enum import Enum
from collections import Mapping, Iterable
from warnings import warn
import logging

logging.debug = print


class MetaAny(type):

    def __instancecheck__(self, instance):
        return True

    def times(self, range_low, range_high=None):
        return WrapObj([self]).times(range_low, range_high)


class Any(object):
    __metaclass__ = MetaAny


def makeMultiInstanceMatcher(*list_type):
    if len(list_type) == 1 and isinstance(list_type[0], Iterable):
        list_type = tuple(list_type[0])

    class MetaMultiInstanceMatcher(type):
        # Use (both are same)
        # a = MetaMultiInstanceMatcher([int,float])
        # b = MetaMultiInstanceMatcher(int,float)
        list_match_type = list_type

        def __instancecheck__(self, instance):

            for each_type in self.list_match_type:
                if isinstance(each_type, type) and isinstance(instance, each_type):
                    # if type, use isinstance
                    return True
                elif each_type == instance:
                    # if value, check equality
                    return True
            else:
                return False

        def times(self, range_low, range_high=None):
            return WrapObj([self]).times(range_low, range_high)

    class MultiInstanceMatcher(type):
        __metaclass__ = MetaMultiInstanceMatcher

    return MultiInstanceMatcher

OR = makeMultiInstanceMatcher


CHECK_DIR = Enum("Iterable check direction", ["FORWARDS", "BACKWARDS"])


class WrapObj(object):

    def __init__(self, data, DO_TYPECHECK=False):
        super(WrapObj, self).__init__()
        self.data = data

        self.DO_TYPECHECK = DO_TYPECHECK
        self.treat_as_object = False

    def as_obj(self):
        try:
            assert(isinstance(self.data, Mapping))
        except AssertionError:
            raise TypeError("data={data} should be of type Mapping "
                            "(e.g. dict)".format(data=self.data))

        self.treat_as_object = True
        return self

    def times(self, range_low, range_high=None):
        return WrapMultiObj(self.data, range_low, range_high)

    def __mul__(self, range_tuple):
        return self.times(range_tuple, None)

    def __pos__(self):
        if (isinstance(self.data, Iterable) and (not isinstance(self.data, Mapping))):
            return WrapMultiObj(self.data, [1, 2])
        else:
            TypeError("+WrapObj only works when WrapObj.data is list-ish")

    def __ne__(self, other):
        return not(self.__eq__(other))

    def __eq__(self, other):
        if self.DO_TYPECHECK and (type(self.data) != type(other)):
            return False
        elif (self.data == other) or (check_as_value_and_type(other, self.data)):
            return True
        elif isinstance(self.data, WrapMultiObj):
            return (self.data == [other])
        elif (isinstance(self.data, Iterable) and (not isinstance(self.data, Mapping))) and\
                (isinstance(other, Iterable) and (not isinstance(other, Mapping))):
            does_match = None
            check_dir = CHECK_DIR.FORWARDS
            multiobj_index_forwards = None
            multiobj_index_backwards = None

            if (check_dir == CHECK_DIR.FORWARDS):

                for ele_index in range(0, len(self.data), 1):
                    ele_data = self.data[ele_index]
                    # as long as not multiobj, check in forwards
                    if isinstance(ele_data, WrapMultiObj):
                        multiobj_index_forwards = ele_index
                        check_dir = CHECK_DIR.BACKWARDS
                        break
                    else:
                        try:
                            ele_other = other[ele_index]
                        except IndexError:
                            # To_be_checked list has length less than matching list
                            return False
                        finally:
                            does_match = (WrapObj(ele_data) == ele_other)
                            if not does_match:
                                return False

            if (check_dir == CHECK_DIR.BACKWARDS):
                for ele_index in range(0 - 1, -(len(self.data) + 1), -1):
                    # ele_index is of negative value from -1 to -len (including)
                    ele_data = self.data[ele_index]
                    # as long as not multiobj, check in backwards
                    if isinstance(ele_data, WrapMultiObj):
                        multiobj_index_backwards = ele_index
                        check_dir = CHECK_DIR.FORWARDS
                        break
                    else:
                        try:
                            ele_other = other[ele_index]
                        except IndexError:
                            # To_be_checked list has length less than matching list
                            return False
                        finally:
                            does_match = does_match = (WrapObj(ele_data) == ele_other)
                            if not does_match:
                                return False

            if (does_match and (multiobj_index_forwards is None) and (multiobj_index_forwards == multiobj_index_backwards)):
                # all of data is in other
                # so, if they have same length, everything is perfect
                return len(self.data) == len(other)
            elif (multiobj_index_forwards + (-multiobj_index_backwards)) != len(self.data):
                # there is more than one length_ANY object
                raise TypeError("There must be only one object of arbitary range")
            else:
                # there is only one length ANY object

                # prepare back index for slicing operation
                # add 1 (as this one will give outer bound) and if results to 0, set to None (as 0 doesnt mean last index)
                multiobj_index_backwards += 1
                multiobj_index_backwards = multiobj_index_backwards or None
                ele_wrapmultiobj = self.data[multiobj_index_forwards]
                logging.debug("Comparing WrapMultiObj with part of list")
                does_match = (ele_wrapmultiobj == other[multiobj_index_forwards:multiobj_index_backwards])
                return does_match
        elif not(self.treat_as_object) and (isinstance(self.data, Mapping) and isinstance(other, Mapping)):
            does_match = None  # as in not known yet
            for (data_key, data_value) in self.data.iteritems():
                if isinstance(data_key, type):
                    # todo: stop printing this line, which is broken into parts
                    warn(("{data_key} is a class used as a key, but it "
                          "wont match keys which are instances of this type"
                          "").format(data_key=data_key))
                try:
                    # try using that key
                    other_value = other[data_key]
                except KeyError:
                    # if fails, it doesnt have that key. so, they dont match
                    does_match = False
                    return False
                else:
                    does_match = (WrapObj(data_value) == other_value)
                    if does_match is False:
                        return does_match
            else:
                # should be True
                assert(does_match is True)
                return True
        elif self.treat_as_object:
            try:
                assert(isinstance(self.data, Mapping))
            except AssertionError:
                raise TypeError("data={data} should be of type Mapping "
                                "(e.g. dict)".format(data=self.data))

            does_match = None  # as in not known yet
            for (data_key, data_value) in self.data.iteritems():
                if isinstance(data_key, type):
                    # todo: stop printing this line, which is broken into parts
                    warn(("{data_key} is a class used as a key, but it "
                          "wont match keys which are instances of this type"
                          "").format(data_key=data_key))
                try:
                    # try using that key
                    other_value = other.__getattribute__(data_key)
                except AttributeError:
                    # if fails, it doesnt have that attribute. so, they dont match
                    does_match = False
                    return False
                else:
                    does_match = (WrapObj(data_value) == other_value)
                    if does_match is False:
                        return does_match
            else:
                # should be True
                assert(does_match is True)
                return True

        else:
            return False


# todo allow custom class with __isinstance__ being called for composite type checking
# class int_or_infinite - use in WrapMultiObj __init__ check
class WrapMultiObj(object):

    def __init__(self, data, range_low, range_high):
        super(WrapMultiObj, self).__init__()

        logging.debug("Creating WrapMultiObj with data={data}".format(data=data))
        if (isinstance(data, Iterable) and (not isinstance(data, Mapping))):
            self.data = data
        else:
            raise TypeError("data={data} should be iterable".format(data=data))

        logging.debug("Checking {range_low}, {range_high} is of correct range..  ".format(range_low=range_low, range_high=range_high))
        INT_OR_INF = OR(int, float("inf"))
        if WrapObj([INT_OR_INF, INT_OR_INF]) == [range_low, range_high]:
            pass
        elif WrapObj([[INT_OR_INF, INT_OR_INF], None]) == [range_low, range_high]:
            range_low, range_high = range_low
        elif WrapObj([INT_OR_INF, None]) == [range_low, range_high]:
            range_high = range_low + 1
        else:
            raise TypeError("range_low and range_high must be of appropiate type")

        logging.debug("OK")

        self.repeat_allowed_range = [range_low, range_high]

        logging.debug("DO_TYPECHECK is off")
        self.DO_TYPECHECK = False

        logging.debug("Create OK, returned")

    def __ne__(self, other):
        return not(self.__eq__(other))

    def __eq__(self, other):
        logging.debug("Checking equality of {self_data} and {other}".format(self_data=self.data, other=other))
        if self.DO_TYPECHECK and (type(self.data) != type(other)):
            logging.debug("DO_TYPECHECK is on and yet types dont match. So returned False")
            return False

        logging.debug("Asserting matcher and matchee are both of list-ish type..  ")
        assert (isinstance(self.data, Iterable) and (not isinstance(self.data, Mapping)))
        try:
            # the one to be matched with should also be list, if its not, no chance of matching
            assert(isinstance(other, Iterable) and (not isinstance(other, Mapping)))
        except AssertionError:
            return False
        logging.debug("OK")

        # if len(other) is not integer multiple len(self.data), they will never match as a whole
        logging.debug("Checking length of matchee is multiple of length of matcher.. ")
        if (len(other) % len(self.data) != 0):
            logging.debug("NOT OK.. returned False")
            return False
        else:
            logging.debug("OK")

        repeat_count = 0
        while True:
            logging.debug("Running iteration {repeat_count}".format(repeat_count=repeat_count + 1))

            if (repeat_count > self.repeat_allowed_range[1]):
                logging.debug("Checking not yet complete, but max_allowed_repeated={max_repeat} crossed. "
                              "So, returning False.".format(max_repeat=self.repeat_allowed_range[1]))
                return False
            start_other_index = repeat_count * len(self.data)

            if start_other_index == len(other):
                # other_list is exhausted, their ends meet exactly
                break

            for ele_index in range(0, len(self.data)):
                ele_data = self.data[ele_index]
                # as long as not multiobj, move on
                if isinstance(ele_data, WrapMultiObj):
                    # raise TypeError(".times not allowed within .times")
                    raise TypeError("{self_class} not allowed within {self_class}, causes ambiguous condition".format(self_class=self.__class__))

                try:
                    ele_other = other[start_other_index + ele_index]
                except IndexError:
                    # To_be_checked list has length less than matching list in this iteration
                    # Return False as the whole data is not matchable this iteration
                    logging.debug("Checking for repeat matching at iteration = {repeat_count} failed".format(repeat_count=repeat_count))
                    return False
                finally:
                    does_match = check_as_value_and_type(ele_other, ele_data)
                    if not does_match:
                        # Return False as the match doesnt work out
                        logging.debug("{ele_other} with {ele_data} Match retuned False")
                        return False

            repeat_count += 1

        logging.debug("Match works with {repeat_count} iterations".format(repeat_count=repeat_count))
        if self.repeat_allowed_range[0] <= repeat_count < self.repeat_allowed_range[1]:
            logging.debug("And it is in valid range")
            return True
        else:
            logging.debug("And it is NOT in valid range")
            return False


def check_as_value_and_type(to_check, value_or_type):
    logging.debug("Checking {1} with {0}".format(value_or_type, to_check))
    # if cheking with Any, return True (let it through)

    # if value_or_type == Any:
    #     return True

    # if its class, then check if instance of that
    if isinstance(value_or_type, type):
        return isinstance(to_check, value_or_type)
    # try as value, if true return
    elif to_check == value_or_type:
        return True

w = WrapObj


def fmatch():
    pass
# print(WrapObj([int, int]) == [2, 2])
print(WrapObj([2, WrapObj([3]).times((1, 3))]) == [2, 3, 3])
OR(int).times(5)
