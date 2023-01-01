# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# class of sparklines in CircuitPython
# created by Kevin Matocha - Copyright 2020 (C)

# See the bottom for a code example using the `sparkline` Class.

# # File: display_shapes_sparkline.py
# A sparkline is a scrolling line graph, where any values added to sparkline using
# `add_value` are plotted.
#
# The `sparkline` class creates an element suitable for adding to the display using
# `display.show(mySparkline)`
# or adding to a `displayio.Group` to be displayed.
#
# When creating the sparkline, identify the number of `max_items` that will be
# included in the graph.
# When additional elements are added to the sparkline and the number of items has
# exceeded max_items, any excess values are removed from the left of the graph,
# and new values are added to the right.


# The following is an example that shows the

# setup display
# instance sparklines
# add to the display
# Loop the following steps:
# 	add new values to sparkline `add_value`
# 	update the sparklines `update`

import time
import random
import board
import displayio

from adafruit_display_shapes.sparkline import Sparkline

import ssl
from random import randint
import adafruit_requests
import socketpool
import wifi
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError

display = board.DISPLAY

aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]

print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
# Initialize an Adafruit IO HTTP API object
io = IO_HTTP(aio_username, aio_key, requests)

try:
    # Get the 'temperature' feed from Adafruit IO
    temperature_feed = io.get_feed("temperature")
except AdafruitIO_RequestError:
    # If no 'temperature' feed exists, create one
    temperature_feed = io.create_new_feed("temperature")

# Send random integer values to the feed
random_value = randint(0, 50)
print("Sending {0} to temperature feed...".format(random_value))
io.send_data(temperature_feed["key"], random_value)
print("Data sent!")

# Retrieve data value from the feed
print("Retrieving data from temperature feed...")
received_data = io.receive_data(temperature_feed["key"])
print("Data from temperature feed: ", received_data["value"])
##########################################
# Create background bitmaps and sparklines
##########################################

# Baseline size of the sparkline chart, in pixels.
chart_width = display.width
chart_height = display.height

# sparkline1 uses a vertical y range between 0 to 10 and will contain a
# maximum of 40 items
sparkline1 = Sparkline(
    width=chart_width, height=chart_height, max_items=140, y_min=0, y_max=10, x=0, y=0
)

# Create a group to hold the sparkline and append the sparkline into the
# group (my_group)
#
# Note: In cases where display elements will overlap, then the order the elements
# are added to the group will set which is on top.  Latter elements are displayed
# on top of former elements.
my_group = displayio.Group()

# add the sparkline into my_group
my_group.append(sparkline1)


# Add my_group (containing the sparkline) to the display
display.show(my_group)

# Start the main loop
while True:

    # turn off the auto_refresh of the display while modifying the sparkline
    display.auto_refresh = False

    # add_value: add a new value to a sparkline
    # Note: The y-range for mySparkline1 is set to 0 to 10, so all these random
    # values (between 0 and 10) will fit within the visible range of this sparkline
    sparkline1.add_value(random.uniform(0, 10))

    # turn the display auto_refresh back on
    display.auto_refresh = True

    # The display seems to be less jittery if a small sleep time is provided
    # You can adjust this to see if it has any effect
    time.sleep(0.0001)
    print(sparkline1.update)
