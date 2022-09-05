riverwar: Download and graph hydrological data from USGS and USBR
=============================================

What is riverwar?
-----------------------

riverwar is a Python app and library to download and graph hydrological data from:
- USGS gages
- USBR RISE service

```python
python3 riverwar.py
```
Services available from USGS include:
- daily values (dv)

Services available from USBR RISE include:
- catalog for Upper and Lower Colorado River Basin, other basins should work with work
- get record id's for datases of interest
- download the data of interest as JSON

Quick start
-----------
dataretrieval can be installed using pip:

    $ pip3 install -r requirements.txt

If you want to run the latest version of the code, you can install from git:

    $ python3 riverwar.py

Issue tracker
-------------

Please report any bugs and enhancement ideas using the dataretrieval issue
tracker:

  https://github.com/edmillard/riverwar/issues

Feel free to also ask questions on the tracker.


Help wanted
-----------

Any help in testing, development, documentation and other tasks is
highly appreciated and useful to the project. 


[![Coverage Status]()
