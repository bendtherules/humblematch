Title: HumbleMatch - Go sanitize your type-checking
Date: 2015-06-19 16:56
Authors: bendtherules
Category: Projects
Tags: HumbleMatch, Launch stuff, Projects
Slug: HumbleMatch_Launch

## Intro

Hi, I am [Abhas](blog.codesp.in) and personally, I love Python mostly for its intuitive, flexible and beautiful API. But some things, I really hate doing. HumbleMatch is my attempt at solving that pain.


## The Pain Point #1

For eg, lets say I have a Point class with two function signatures - `Point(x,y)` and `Point([x,y])`. Lets see a typical implementation of this -


    class Point(object):

    def __init__(self, x, y=None):
        if isinstance(x, int) and isinstance(y, int): # check for Point(x,y)
            self.x = x
            self.y = y
        elif isinstance(x, list) and (y is None): # check for Point([x,y])
            assert(len(x) == 2)
            assert(isinstance(x[0], int) and isinstance(x[1], int))
            x, y = x
            self.x = x
            self.y = y
        else:
            raise TypeError("Pass proper arguments")

Now, definitely there are some shortcuts you could take there, but the point is this process is quite error-prone and repetitive. For eg, one might easily miss the `(y is None)` or `isinstance` check in the 2nd case.

Again, this is a pretty basic requirement I imposed upon the `__init__` method. Wouldnt it be awesome if you could do all this easily and also support dicts like `{x:20,y:50}` or hell, even objects with `obj.x = 20, obj.y =50` directly as arguments?

Lets visit the better side


## Using HumbleMatch #1


    from humblematch import w


    class Point(object):

        def __init__(self, x, y=None):
            if w([int, int]) == [x, y]: # check for Point(x,y)
                self.x = x
                self.y = y            
            elif w([[int, int], None]) == [x, y]: # check for Point([x,y])
                x, y = x
                self.x = x
                self.y = y
            else:
                raise TypeError("Pass proper arguments")

Look at the difference on line 6 and line 10 - you can put all those isinstance and length checks in one line, and hopefully, it now becomes easier to grasp what the code does at one look. That `w` or `WrapObj` class is the most important among a very few classes that humblematch provides.

So, lets go through this and see how it works.

### humblematch.w(object)
--------------------------
Same as humblematch.WrapObj. It acts as a wrapper, and takes as input any object, be it a class like int or float or list or a value like 5.23.

It is in itself useless, but has a specialized \__eq__ operator which helps in matching. Object passed to it is considered as the reference against which any other object can be checked.

#### Methods
-------------
##### \__eq__(other)
Same as  `w(obj) == other`

If *obj* is a *class*, then it returns True if *other* is instance of *obj*. So,can match against types like int.

If not *class* and not the ones mentioned below, then returns True if `obj == other`. So, can match against values like 5 or "abcd"

If *obj* is a list-ish iterable (i.e. not string or dict), then each element is checked against that of *other*. Returns True if `other[index] == obj[index]` for every index in *obj* and they both have same number of elements

If *obj* is a Mapping (eg dict), returns true if for each key in *obj*,  `other[key] == obj[key]`. But it is ok for *other* to have extra keys

If *obj* is a Mapping and you use `w(obj).as_obj() == other`, then *other* is considered as a Object and all the keys in *obj* are looked up on *other* using \__getattribute__ i.e. it returns True if `other.key == obj[key]` for all the keys in *obj*.

#### Example

    w(int) == 5 is True
    w(int) == 5.23 is False

    w(int) == int is False # Wont match class itself
    
    w(5) == 5 is True
    w(5) == 5.0 is True # as 5 == 5.0 in Python

    w([int, 5]) == [2, 5] is True # Using list
    w([int, 5]) == [2.23, 5] is False
    w([list, 50]) == [[200], 50] is True

    w({"a":int}) == {"a":1, "b":99} is True # Using dict

    class object2(object):
        pass

    q = object2()
    q.a, q.b = 1, 99
    w({"b": int}).as_obj() == q is True  # Using object

    w({"a":[int,float]}) == {"a":[36,1.26]} # ** OK to nest expressions **


Also, I promised you that you can just as easily use dicts and objects - but from the previous examples, you probably can guess how to do that. So, if you are willing, just go forward and implement that first. Hopefully, you will love the simplicity.

Now because this is currently the only documentation on it, I'll go ahead with few more examples and provide the remaining doc alongside.



## The Pain Point #2

Lets say, we have a function called `diff_list`, which given *two lists as argument*, returns a *list of two lists, each of them containing the unique/exclusive elements* from the corresponding list passed as argument . (Unique in the sense its not present in the other list). But if any of those return lists dont have any unique argument, the function simply *returns `None` instead of that list*.

For simplicity, we also assume that the argument lists themselves dont have repeating elements. So, for eg. `diff_list([2,3,4,9],[1,3,9]) == [[2,4],[1]]` and `diff_list([2,3,4,9],[3,9]) == [[2,4],None]`



Heres a sample implementation we are going to use -
    

    from humblematch import w


    def diff_list(list_1, list_2):
        try:
            assert(w([list, list]) == [list_1, list_2])
        except AssertionError:
            raise TypeError("Both arguments must be list or a list-ish iterable")

        exclusive_list_1 = []

        for ele in list_1:
            if ele not in list_2:
                exclusive_list_1.append(ele)

        exclusive_list_2 = []
        for ele in list_2:
            if ele not in list_1:
                exclusive_list_2.append(ele)

        return [exclusive_list_1 or None, exclusive_list_2 or None]

Our goal is to test this function from certain directions -

1. Whether it returns a list of two elements, each of which might be another list or None.
2. Given two lists of any size conataining only float as argument (eg. `diff_list([1.12,2.64],[2.56])`), whether all the elements in the sub-lists of the returned list are of type float.

Obviously, there are some other checks we should do, but this module probably wont be of much help there.

## Test 1


    from humblematch import w, OR
    from random import random, randint
    list_1 = [randint(0, 25) for i in range(randint(5, 10))]
    list_2 = [randint(0, 25) for i in range(randint(5, 10))]

    assert(diff_list(list_1, list_2) == w([OR(list, None), OR(list, None)]))


We need to check that each element in the returned list is either a list or None. So, we need to have some way of checking one argument against a number of types and values, where the check returns True if any of them satisfies. That why we have `humblematch.OR(obj1, obj2, ...)`

### humblematch.OR(obj1, obj2, ...)
------------------------------------

Also has the signature `humblematch.OR([obj1, obj2, ...])`.

`OR(obj1,obj2, ...) == other` returns True if `other` matches (isinstance of or is equal to) any of the `obj` passed as argument.

`OR` also has all the facilities of `w`, so its not required to use `w(OR())` - it is functionally equivalent to just `OR()`.

#### Example

    OR(int) == 5 is True
    OR(int, float) == 2.26 is True
    w(OR([10, None])) == None is True
    w(OR(str, 5)) == 5 is True
    

### humblematch.ANY
--------------------

Similar to `OR`, there is `humblematch.ANY` which matches object of any type. It is usually used when we dont care about the type of the argument, but still want it to be there. Also, `ANY` has all facilities of `w` just like `OR`.

#### Example 

    w(Any) == 4 is True
    Any == [2,{"a":3}] is True

### OR, ANY and more

Both `ANY` and `OR` work like Abstract Base Class (ABC). Along with this, we could also use any ABC for eg. those defined in `types` and `number` module.
HumbleMatch makes some of the common ones available directly, with slight modifications in some of them (specifically StringTypes). The available ones are:

* `StringTypes` - Matches strings of both types, `str` and `unicode`
* `NumberType` - Matches any kind of number (like `int` or `float`)
* `FunctionType` - Matches any function (useful for checking methods in object)
* `ClassType` - Matches any class (Probably both new and old-style class)

`ANY` and `OR` are more important in nested expressions like
    

    w([2,int, OR(str,int), Any]) == [2, 99, "asd", [{"a":55}]] is True

## Test 2


    from humblematch import w, inf
    from random import random, randint
    list_1 = [random()*10 for i in range(randint(1, 5))] #eg [1.23,5.32]
    list_2 = [random()*10 for i in range(randint(1, 5))] #eg [3.3,5.32,6.7]
        
    assert(diff_list(list_1, list_2) == w([[w([float]).times(0, inf)],
                                           [w([float]).times(0, inf)]]))

Lets say `diff_list(list_1, list_2)` returns `[list_3, list_4]`. We need to check that both *list\_3* and *list\_4* are filled with only float elements. So. to check *list\_3* first, we use `[w([float]).times(0, inf)]`, which means the *list\_3* is a list and it consists of elements which can be eaten up by the pattern `float` when repeated for atleast 0 times and at max infinite times. 

### humblematch.w([pattern_1, pattern_2, ...]).times(min,max)
-----------------------------------------------------------------
Also has signature `w([pattern_1, pattern_2]).times(exact_times)`

It works like the `*args` used in functions, it matches a number of elements which follow the given pattern, but should atleast repeat `min` times and atmost `max-1` times (i.e. `max` times is exclusive, just like `range` in python), if both arguments are given. If only one is given, it must repeat exactly `exact_times`. 

But hey, what exactly is the pattern `[pattern_1, pattern_2, ...]`? It means that `pattern_1` must occur first, followed by `pattern_2`, followed by others) to be count as one full match and this type of full match can occur in the `(min,max)` range. If the full match doesnt complete, it is considered invalid and hence doesnt match.

It is used like this :

`w([w([pattern_1, pattern_2, ...]).times(min,max)]) == [ele_1, ele_2, ...]`

Also, `w([pattern_1, pattern_2, ...]).times(min,max)` has another alias `w([pattern_1, pattern_2, ...])*(min,max)`, so we can use `*(min,max)` instead of `.times(min,max)` for shorthand purpose.

Infact now that we know this, in Test 2 we can remove the repetion of `w([float]).times(0, inf)` twice using another `.times`. Try that if you have some time.

## Undocumented

I purposedly missed one method which is already there, called `w(obj).save_as(arg_name)`. How it works is that whatever it matches with is stored  as `"arg_name"` and returns a dict filled with all such values, when `==`d with `other`. For eg `w([2, w(int).save_as("a"), OR(str,dict)).save_as("b")]) == [2,5,{"q":1}]` returns `{"a":5,"b":{"q":1}}`. I didnt document it well beacuse I am not mentally ok with a `==` call returning anything other than a `boolean`. Maybe, I will change the API in some way to make it better and document it then. But feel free to also try this, I am proud of this feature :)

And thats all for now, have fun and write more code.
