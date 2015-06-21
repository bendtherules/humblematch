# HumbleMatch 
--------------
Will **Sanitize your type-checks and duck-checks** for you

![HumbleMatch logo](http://humblematch.readthedocs.org/en/latest/img/logo_medium.png "Yeah, I took that pic :)")

**Install using**
`pip install humblematch`

Available at [HumbleMatch@pypi](https://pypi.python.org/pypi/humblematch)

More Docs at [projects.codesp.in/humblematch](http://humblematch.readthedocs.org/en/latest/)

## What the heck is it?

HumbleMatch is made to *add a zing* to your mundane type-checking and duck-checking code.

* Check your function arguments reliably, add *more flexible signatures* and most of all, have a lovely API.
* Or just *sprinkle some assert* checks to ensure the data is what you expect it to be at any point.
* Provide helpful debugging errors, *dont just fail with cryptic errors*


## Get Running
--------------

### Run doctest -

python -m doctest .\humblematch\wrap_obj.py

### Run tests-
cd humblematch
py.test

### To build code - 

python setup.py sdist bdist_wheel
python setup.py build --plat-name=win-amd64 bdist_wininst
python setup.py build --plat-name=win32 bdist_wininst

### To upload to PYPI-

twine upload dist/* -R pypi

### To build or serve docs

mkdocs build

or

mkdocs serve

-----
