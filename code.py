#XL pyportal fetch feeds, show QR

import time
import board
import busio
from adafruit_pyportal import PyPortal

from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import neopixel
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT
from secrets import secrets

# the current working directory (where this file is)
cwd = ("/"+__file__).rsplit('/', 1)[0]

# a function that returns whatever is passed in
def identity(x):
    return x

pyportal = PyPortal(status_neopixel=board.NEOPIXEL,
                    default_bg=cwd + "/on_this_day_bg.bmp",
                    text_font=cwd+"fonts/Arial-ItalicMT-17.bdf",
                    # we do this so the date doesnt get commas
                    text_transform=[identity]*6,
                    text_position=((10, 70), (10, 100), (10, 130),
                                   (60, 160), (105, 190), (10, 220)),
                    text_color=(0xFFFFFF, 0xFFFFFF, 0xFFFFFF,
                                0xFFFFFF, 0xFFFFFF, 0xFFFFFF),
                    text_maxlen=(50, 50, 50, 50, 50, 50),  # cut off characters
                    )

# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

status_light = neopixel.NeoPixel(
    board.NEOPIXEL, 1, brightness=0.2
)  # Uncomment for Most Boards
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(
    esp, secrets, status_light)

# Define callback functions which will be called when certain events happen.
# pylint: disable=unused-argument

def connected(client):
    # Connected function will be called when the client is connected to Adafruit IO.
    # This is a good place to subscribe to feed changes.  The client parameter
    # passed to this function is the Adafruit IO MQTT client so you can make
    # calls against it easily.
    print("Connected to Adafruit IO!  Listening for DemoFeed changes...")
    # Subscribe to changes on a feed named DemoFeed.
    io.subscribe_to_time("iso")

# pylint: disable=unused-argument

def message(client, feed_id, payload):
    # Message function will be called when a subscribed feed has a new value.
    # The feed_id parameter identifies the feed, and the payload parameter has
    # the new value.
    print("Feed {0} received new value: {1}".format(feed_id, payload))

print("Connecting to WiFi: ", secrets["ssid"])
wifi.connect()
print("Connected!")

# Initialize MQTT interface with the esp interface
MQTT.set_socket(socket, esp)

# Initialize a new MQTT Client object
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    port=8883,
    username=secrets["aio_username"],
    password=secrets["aio_key"],
)

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client)

# Connect the callback methods defined above to Adafruit IO
io.on_connect = connected
io.on_message = message

# Connect to Adafruit IO
print("Connecting to Adafruit IO...")
io.connect()

# create pyportal object w no data source (we'll feed it text later) 
""" 
 pyportal = PyPortal(status_neopixel = board.NEOPIXEL,
                    default_bg = cwd + "/on_this_day_bg.bmp",
                    text_font = cwd+"fonts/Arial-ItalicMT-17.bdf",
                    text_transform = [identity]*6,  # we do this so the date doesnt get commas
                    text_position=((10, 70), (10, 100), (10, 130),(60, 160), (105, 190), (10, 220)),
                    text_color=(0xFFFFFF, 0xFFFFFF, 0xFFFFFF, 0xFFFFFF, 0xFFFFFF, 0xFFFFFF),
                    text_maxlen=(50, 50, 50, 50, 50, 50), # cut off characters 
                   )
 """
while True:
    
    # now = time.localtime()
    #print("Current time:", now.tm_hour)
 
    io.loop()

    # Make a QR code from web reference 
    # pyportal.show_QR(bytearray("https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true"), qr_size=5, x=300, y=10)

    # wait 10 minutes before running again
    time.sleep(10*60)
