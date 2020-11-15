This Project is currently in Alpha all requests are directed to https://master.apis.dev.openstreetmap.org


PY-OSMAPI
=========
A OSM-Edit API Interface written in Python

Description
============
This Project is forked from repository osmate_ I saw the need to write my own code to access the OSM-API for editing.
My second requirement was to be able to use OAuth which I haven't found In any other Python OSM-API yet.


.. _osmate: https://github.com/jonycoo/osmate

Installation
=============
the project is now on pip, so now it is just as easy as

.. code-block:: bash

    pip install py-osmapi

after that import osm.osm_api

.. code:: python

    import osm.osm_api
    import osm.osm_util
    osm = osm.osm_api.OsmApi()
    #currently only for accounts at the testserver (https://master.apis.dev.openstreetmap.org)
    osm.get_current_user((<osm-username>, <osm-password>))

I wrote some documentation to every public method.
I've Implemented all methods from the API v0.6, excluding reduction

Support
========
Please create an Issue in github for any Bugs and Feature requests.
For direct contact to me please write a PM via OSM `here <https://www.openstreetmap.org/user/jonycoo>`_.
If you want to support me, consider to `Donate <https://paypal.me/jonycoo>`_ any amount you like.