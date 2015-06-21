from __future__ import print_function
from enum import Enum
from collections import Mapping, Iterable
from warnings import warn
import logging
import types
import numbers

# logging.debug = print

__all__ = ["Any", "OR", "WrapObj", "w", "WrapMultiObj", "inf", "StringTypes", "NumberType", "FunctionType", "ClassType"]


class MetaAny(type):

    def __instancecheck__(self, instance):
        return True

    def times(self, range_low, range_high=None):
        return WrapObj([self]).times(range_low, range_high)

    def save_as(self, save_key):
        return WrapObj(self).save_as(save_key)


class Any(object):

    '''
    Checker class which allows everything.
    Usually, you would use it as a catch-all or placeholder.
    >>> w(Any) == "asd"
    True
    >>> w(Any) == 2
    True
    >>> w(Any) == 2.35
    True
    >>> w(Any) == (lambda x:None)
    True
     '''
    __metaclass__ = MetaAny


def makeMultiInstanceMatcher(*list_type):
    '''
    Create checker class which allows some types or values.
    For combining two or more possible types of a variable

    >>> w(OR(int,float)) == 2.25 and w(OR(int,float)) == 2
    True
    >>> w(OR([int,float])) == 2.25 and w(OR([int,float])) == 2
    True
    '''

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

        def save_as(self, save_key):
            return WrapObj(self).save_as(save_key)

    class MultiInstanceMatcher(type):
        __metaclass__ = MetaMultiInstanceMatcher

    return MultiInstanceMatcher

OR = makeMultiInstanceMatcher

CHECK_DIR = Enum("Iterable check direction", ["FORWARDS", "BACKWARDS"])


class WrapObj(object):

    '''
    Create WrapObj instance.
    data -> Reference Object to match with.
    DO_TYPECHECK -> Whether the refernece and checked object must
    have same type? Defaults to false.

    >>> WrapObj(int)  # doctest: +ELLIPSIS
    <wrap_obj.WrapObj object at ...>
    >>> WrapObj(float, True)  # doctest: +ELLIPSIS
    <wrap_obj.WrapObj object at ...>

    '''

    def __init__(self, data, DO_TYPECHECK=False):

        super(WrapObj, self).__init__()
        self.data = data

        self.DO_TYPECHECK = DO_TYPECHECK
        self.treat_as_object = False
        self.dict_saved_values = {}
        self.save_key = None

    def as_obj(self):
        '''
        Matches wrapped dict to object

        >>> class object2(object): pass
        >>> test_obj = object2(); test_obj.a = 20
        >>> w({"a": int}).as_obj() == test_obj
        True
        '''

        try:
            assert(isinstance(self.data, Mapping))
        except AssertionError:
            raise TypeError("data={data} should be of type Mapping "
                            "(e.g. dict)".format(data=self.data))

        self.treat_as_object = True
        return self

    def save_as(self, arg_name):
        '''
        Saves matched value as arg_name, which is
        used as key in the returned dict from __eq__

        >>> _ = w([int,w(float).save_as("a")]) == [2,2.5]
        >>> _["a"] == 2.5
        True
        '''
        self.save_key = arg_name
        return self

    def times(self, range_low, range_high=None):
        '''
        Makes all the items in wrapped iteratble (in given order) match
        at least range_low times and at max (range_high-1) in __eq__

        >>> w([int]).times(2,4) == [2,56,7]
        True
        >>> w([int]).times(2) == [2,56]
        True

        Wrapped object must be a iterator. If only range_low is passed,
        must match for exactly range_low times.

        Returns a WrapMultiObj.
        '''
        return_obj = WrapMultiObj(self.data, range_low, range_high)
        return_obj.save_key = self.save_key
        return return_obj

    def __mul__(self, range_tuple):
        '''
        Same as WrapObj.times

        >>> w([int])*(2,4) == [2,56,7]
        True
        >>> w([int])*(2) == [2,56]
        True
        '''
        return self.times(range_tuple, None)

    # def __pos__(self):
    #     if (isinstance(self.data, Iterable) and (not isinstance(self.data, Mapping))):
    #         return WrapMultiObj(self.data, [1, 2])
    #     else:
    #         TypeError("+WrapObj only works when WrapObj.data is list-ish")

    def __ne__(self, other):
        '''
        Handles != matching. Returns opposite of == value

        >>> w(int) != [2,56]
        True
        '''
        return not(self.__eq__(other))

    def match_list(self, other):
        '''
        Internal method. Handles self == other, when other is list
        '''
        match_dict_or_True = None
        check_dir = CHECK_DIR.FORWARDS
        multiobj_index_forwards = None
        multiobj_index_backwards = None

        self.dict_saved_values = {}

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
                        match_dict_or_True = (WrapObj(ele_data) == ele_other)
                        if match_dict_or_True and isinstance(match_dict_or_True, dict):
                            self.dict_saved_values.update(match_dict_or_True)
                        if not match_dict_or_True:
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
                        match_dict_or_True = (WrapObj(ele_data) == ele_other)
                        if match_dict_or_True and isinstance(match_dict_or_True, dict):
                            self.dict_saved_values.update(match_dict_or_True)
                        if not match_dict_or_True:
                            return False

        if (match_dict_or_True and (multiobj_index_forwards is None) and (multiobj_index_forwards == multiobj_index_backwards)):
            # all of data is in other
            # so, if they have same length, everything is perfect
            if len(self.data) == len(other):
                return (self.dict_saved_values or True)
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
            match_dict_or_True = (ele_wrapmultiobj == other[multiobj_index_forwards:multiobj_index_backwards])
            if match_dict_or_True:
                if isinstance(match_dict_or_True, dict):
                    self.dict_saved_values.update(match_dict_or_True)
                return (self.dict_saved_values or True)
            else:
                return False

    def match_dict_or_obj(self, other, dict_or_obj=dict):
        '''
        Internal method. Handles self == other, when other is dict or obj
        '''
        assert(dict_or_obj in (dict, object))
        match_dict_or_True = None  # as in not known yet

        self.dict_saved_values = {}

        for (data_key, data_value) in self.data.iteritems():
            if isinstance(data_key, type):
                # todo: stop printing this line, which is broken into parts
                warn(("{data_key} is a class used as a key, but it "
                      "wont match keys which are instances of this type"
                      "").format(data_key=data_key))
            try:
                if dict_or_obj is dict:
                    # if dict, try using that key
                    other_value = other[data_key]
                elif dict_or_obj is object:
                    # if obj, try using that attribute
                    other_value = other.__getattribute__(data_key)
                else:
                    raise TypeError("dict_or_obj must be dict or obj")
            except (KeyError if dict_or_obj == dict else AttributeError):
                # catch correct kind of error
                # so if fails, it doesnt have that key or attribute. so, they dont match
                match_dict_or_True = False
                return False
            else:
                match_dict_or_True = (WrapObj(data_value) == other_value)

                if match_dict_or_True and isinstance(match_dict_or_True, dict):
                    self.dict_saved_values.update(match_dict_or_True)

                if match_dict_or_True is False:
                    return match_dict_or_True
        else:
            # should be True
            assert(bool(match_dict_or_True) is True)
            return (self.dict_saved_values or True)

    def __eq__(self, other):
        '''
        Handles self == other correctly

        >>> w(float) == 2.23
        True
        >>> w(str) == "2.23"
        True
        '''
        if self.DO_TYPECHECK and (type(self.data) != type(other)):
            return False

        elif isinstance(self.data, WrapObj):
            return self.data == other

        elif isinstance(self.data, WrapMultiObj):
            return (self.data == [other])

        elif isinstance(self.data, types.StringTypes):
            # take care of strings in normal way unlike lists
            return self.data == other

        elif (isinstance(self.data, Iterable) and (not isinstance(self.data, Mapping))) and\
                (isinstance(other, Iterable) and (not isinstance(other, Mapping))):
            return self.match_list(other)

        elif not(self.treat_as_object) and (isinstance(self.data, Mapping) and isinstance(other, Mapping)):
            return self.match_dict_or_obj(other, dict)

        elif self.treat_as_object:
            try:
                assert(isinstance(self.data, Mapping))
            except AssertionError:
                raise TypeError("data={data} should be of type Mapping "
                                "(e.g. dict)".format(data=self.data))

            return self.match_dict_or_obj(other, object)

        elif check_as_value_and_type(other, self.data):

            if self.save_key is not None:
                self.dict_saved_values[self.save_key] = other
                return self.dict_saved_values
            else:
                return True
            # return True

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
            raise TypeError("range_low={range_low} and range_high={range_high} must be of appropiate type"
                            "".format(range_low=range_low, range_high=range_high))

        logging.debug("OK")

        self.repeat_allowed_range = [range_low, range_high]

        logging.debug("DO_TYPECHECK is off")
        self.DO_TYPECHECK = False

        self.dict_saved_values = {}
        self.save_key = None

        logging.debug("Create OK, returned")

    def save_as(self, arg_name):
        self.save_key = arg_name
        return self

    def __ne__(self, other):
        return not(self.__eq__(other))

    def __eq__(self, other):
        '''
        Similar to WrapObj.__eq__
        But expects other is iterable
        '''
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

        self.dict_saved_values = {}

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
                    # match_dict_or_True = check_as_value_and_type(ele_other, ele_data)
                    match_dict_or_True = (WrapObj(ele_data) == ele_other)
                    # take care of save_as of child elements
                    if match_dict_or_True and isinstance(match_dict_or_True, dict):
                        # update self.dict_saved_values with each value in its list form,
                        # so as to allow muliple matches
                        for match_key in match_dict_or_True:
                            match_val = match_dict_or_True[match_key]
                            prev_match_val = self.dict_saved_values.get(match_key)
                            if isinstance(prev_match_val, list):
                                self.dict_saved_values[match_key].append(match_val)
                            else:
                                self.dict_saved_values[match_key] = [match_val]

                    if not match_dict_or_True:
                        # Return False as the match doesnt work out
                        logging.debug("{ele_other} with {ele_data} Match retuned False")
                        return False

            repeat_count += 1

        logging.debug("Match works with {repeat_count} iterations".format(repeat_count=repeat_count))
        if self.repeat_allowed_range[0] <= repeat_count < self.repeat_allowed_range[1]:
            logging.debug("And it is in valid range")
            # take care of save_as of self
            if self.save_key is not None:
                self.dict_saved_values[self.save_key] = other

            return (self.dict_saved_values or True)
        else:
            logging.debug("And it is NOT in valid range")
            return False


def check_as_value_and_type(to_check, value_or_type):
    '''
    Checks whether to_check is either
    i) instance of value_or_type if value_or_type is a class
    ii) to_check == value_or_type if value_or_type is not a class

    >>> check_as_value_and_type( 5, int)
    True
    >>> check_as_value_and_type( 5, 5)
    True
    >>> check_as_value_and_type( int, int)
    False
    '''
    logging.debug("Checking {1} with {0}".format(value_or_type, to_check))

    # if its class, then check if instance of that
    if isinstance(value_or_type, type):
        return isinstance(to_check, value_or_type)
    # try as value, if true return
    elif to_check == value_or_type:
        return True
    else:
        return False

w = WrapObj

# some extra constants
inf = float("inf")
StringTypes = OR(types.StringTypes)
NumberType = numbers.Number
FunctionType = types.FunctionType
ClassType = types.ClassType


# to think and todo
# def fmatch():
#     pass
