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
import traceback
import time
import adafruit_datetime

# Adafruit IO Account
IO_USER = secrets['aio_username']
IO_KEY = secrets['aio_key']
# Adafruit IO Feed
IO_FEED = 'ab-weather.winddirection'

cwd = ("/"+__file__).rsplit('/', 1)[0]
pyportal = PyPortal(
    json_path='data',
    status_neopixel=board.NEOPIXEL,
    default_bg=cwd+"pyp_spark_qr.bmp"
    )

# speed up projects with lots of text by preloading the font!pyportal.preload_font()
pyportal.get_local_time()
now = time.localtime()
print(now)
#print(datetime.datetime.now().isoformat())
ENDTIME  = "%04d-%02d-%02d%c" % (now.tm_year,now.tm_mon,now.tm_mday, "T") + "%04d:%02d:%02d%c" % (now.tm_hour, now.tm_min, now.tm_sec, "Z")
print(ENDTIME)
HOURS = 144  # how far back to go
RESOLUTION = 120  # in minutes
maxdatapoints = HOURS//(RESOLUTION//60)
print(maxdatapoints)

DATA_SOURCE = "https://io.adafruit.com/api/v2/{0}/feeds/{1}/data/chart?X-AIO-Key={2}&end_time={3}&hours={4}&resolution={5}".format(
    IO_USER, IO_FEED, IO_KEY, ENDTIME, HOURS, RESOLUTION)

print(DATA_SOURCE)
print("pyp_init")
#pyportal.splash
sparkline1 = Sparkline(
    width=335, height=85, max_items=maxdatapoints, x=80, y=188, color=0x000000
)
# add the sparkline into my_group
#pyportal.splash.append(my_group)
# add the sparkline into my_group
pyportal.splash.append(sparkline1)

my_group = Graphics()  # my_group = displayio.Group()
display = board.DISPLAY
# Add my_group (containing the sparkline) to the display
display.show(pyportal.splash)
#my_group.qrcode(
pyportal.show_QR(
    "https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true", qr_size=5, x=308, y=2)


while True:
    current_time = time.localtime()
    print(current_time.tm_hour,":",current_time.tm_min)
    try:
        print('Fetching Adafruit IO Feed Value..')
        gc.collect()
        print(gc.mem_free())
        value = pyportal.network.fetch_data(DATA_SOURCE, json_path=['data'])
        print("Response is", value[0][-1][0])
        print("number of rec's", len(value[0]))
        print(gc.mem_free())
        date_part, time_part = value[0][-1][0].split("T")
        # Split the time part at the ":" character to get the hours and minutes
        hours, minutes, seconds = time_part.split(":")
        print(f"Last data point:{hours}:{minutes}")
        print("____________________________________________")
        #value = requests.get(DATA_SOURCE)
        #jsondata = json.loads(value)
        #print(len(jsondata), "Filling sparkline")
        display.auto_refresh = False
        for item in value[0]:
            #print(item[1])
            sparkline1.add_value(float(item[1]))
            #print(gc.mem_free())
        display.auto_refresh = True
        #arkline1.update

    except MemoryError as e:
        traceback.print_exception(type(e), e, e.__traceback__)
        print("Some error occured, retrying! -", e)
        jsondata = None
        value = None
        gc.collect()

    print(gc.mem_free())

    gc.collect()
    #  pyportal.show_QR("https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true", qr_size=5, x=290, y=0)
    # my_group.display.show(my_group.splash)
    print(gc.mem_free())
    time.sleep(100)
