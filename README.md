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
Services available for USGS gages include:
- download abd cache the data of interest as a
	daily values (dv)
- autoupdate the cache to the most recently available day

Services available for USBR RISE data include:
- download and cash catalogs for Upper and Lower Colorado River Basin
- download and cash other basins should work, you need the unified region id
- get record id's for datasets of interest in a unified region
- download and cache the data of interest as a JSON file

Services available to view data:
- plotting daily flows for a USGS gage or USBR structure
- bar graphs for annual water year flows for USGS gage or USBR structures

Quick start
-----------
riverwar can be installed using pip3:

    $ pip3 install -r requirements.txt

To run the very basin example:

    $ python3 riverwar.py

This will download and cache a bunch of Colorado River USGS gages and USBR RISE
data sets. It will then plot daily flows and water year annual bar graphs with a
10 year running average.  Press a button or key on the last figure to advanve to
the next.  This will create a LOT of graphs (more than a hundred) and may exhaust
memory if your memory is limited.  Ctrl-C in the shell to exit.

To download the catalogs uncomment this line in riverwar.py main:
    if __name__ == '__main__':
        # usbr_catalog()

To see all the items in a catalog uncomment these lines in riverwar.py in the function
usbr_catalog():

        # else:
            # print(record_title)

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
