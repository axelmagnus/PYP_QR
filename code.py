import time
import board
from adafruit_pyportal import PyPortal, Graphics    
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests
from digitalio import DigitalInOut
import busio
import json
from adafruit_display_shapes.sparkline import Sparkline
import displayio
from secrets import secrets
import gc

# Adafruit IO Account
IO_USER = secrets['aio_username']
IO_KEY = secrets['aio_key']
# Adafruit IO Feed
IO_FEED = 'ab-weather.winddirection'

HOURS = 144  # how far back to go
RESOLUTION = 120 # in minutes
maxdatapoints = HOURS//(RESOLUTION//60)

DATA_SOURCE = "https://io.adafruit.com/api/v2/{0}/feeds/{1}/data/chart?X-AIO-Key={2}&hours={3}&resolution={4}".format(IO_USER, IO_FEED, IO_KEY, HOURS , RESOLUTION)

print(DATA_SOURCE)

""" FEED_VALUE_LOCATION = ['updated_at']
#FEED_VALUE_LOCATION = ['last_value']
# --------------- Adafruit io --------------- #
# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)

socket.set_interface(esp)
requests.set_socket(socket, esp) """

cwd = ("/"+__file__).rsplit('/', 1)[0]
pyportal = PyPortal(url=DATA_SOURCE,
                    json_path = 'data',
                    status_neopixel=board.NEOPIXEL,
                    #default_bg=cwd+"/pyportal_email.bmp",
                    text_font=cwd+"/fonts/Helvetica-Oblique-17.bdf",
                    text_position=(30, 65),
                    text_color=0xFFFFFF,
                    text_wrap=35,  # wrap feed after 35 chars
                    text_maxlen=160)

# speed up projects with lots of text by preloading the font!
pyportal.preload_font()


sparkline1 = Sparkline(
    width=460, height=100, max_items=maxdatapoints, x=20, y=210
)
my_group = Graphics()   #my_group = displayio.Group()
display = board.DISPLAY
my_group.qrcode("https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true", qr_size=5, x=308, y=2)
# add the sparkline into my_group
my_group.splash.append(sparkline1)

# Add my_group (containing the sparkline) to the display
my_group.display.show(my_group.splash)

while True:
    display.auto_refresh = False
    try:
        print('Fetching Adafruit IO Feed Value..')
        gc.collect()
        print(gc.mem_free())
        value = pyportal.fetch() 
        #print("Response is", value)
        print("____________________________________________")
        #value = requests.get(DATA_SOURCE)
        #jsondata = json.loads(value)
        #print(len(jsondata), "Filling sparkline")
        for item in value:
            #print(item[1])
            sparkline1.add_value(float(item[1]))
            #print(gc.mem_free())
        display.auto_refresh = True
        #arkline1.update    
        
    except MemoryError as e:
        print("Some error occured, retrying! -", e)
        jsondata = None
        value = None
        gc.collect()  

    print(gc.mem_free())

    gc.collect()
    pyportal.show_QR("https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true", qr_size=5, x=290, y=0)
    my_group.display.show(my_group.splash)
    print(gc.mem_free())
    time.sleep(10)
