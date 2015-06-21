

## Run doctest -

python -m doctest .\wrap_obj.py

## Run tests-
cd humblematch
py.test

## To build - 

python setup.py sdist bdist_wheel
python setup.py build --plat-name=win-amd64 bdist_wininst
python setup.py build --plat-name=win32 bdist_wininst

To upload -
twine upload dist/*
