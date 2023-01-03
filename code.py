import time
import board
from adafruit_pyportal import PyPortal, Graphics
"""
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests
"""
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
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
import vectorio

# Adafruit IO Account
IO_USER = secrets['aio_username']
IO_KEY = secrets['aio_key']
# Adafruit IO Feed
feed_group = 'esp32s2tft'
feed_info=(('temp',1, "C"),('percent',1, "%"),('voltage', 2, "V"),('hum', 1, "%")) #name number of decimals, unit
IO_FEEDS=()
for feed in feed_info:
    IO_FEEDS+=feed_group+"."+feed[0],
#print(feed_info[0][1])
#print("%s %.*f %s" % (feed_info[0][0], feed_info[0][1], 3.18, feed_info[0][2]))

cwd = ("/"+__file__).rsplit('/', 1)[0]
pyportal = PyPortal(
    json_path='data',
    status_neopixel=board.NEOPIXEL,
    default_bg=cwd+"pyp_spark_qr.bmp"
    )

# speed up projects with lots of text by preloading the font!pyportal.preload_font()
pyportal.get_local_time()
now = time.localtime()
#print(now)
#print(datetime.datetime.now().isoformat())
ENDTIME  = "%04d-%02d-%02d%c" % (now.tm_year,now.tm_mon,now.tm_mday, "T") + "%04d:%02d:%02d%c" % (now.tm_hour, now.tm_min, now.tm_sec, "Z")
#print(ENDTIME)
HOURS = 144  # how far back to go
RESOLUTION = 120  # in minutes
maxdatapoints = HOURS//(RESOLUTION//60)
#print(maxdatapoints)

DATA_SOURCE = "https://io.adafruit.com/api/v2/{0}/feeds/{1}/data/chart?X-AIO-Key={2}&end_time={3}&hours={4}&resolution={5}".format(
    IO_USER, "ab-weather.winddirection", IO_KEY, ENDTIME, HOURS, RESOLUTION)

#print(DATA_SOURCE)
#pyportal.splash
sparkline1 = Sparkline(
    width=335, height=85, max_items=maxdatapoints, x=80, y=188, color=0x000000
)
# add the sparkline into my_group
#pyportal.splash.append(my_group)
# add the sparkline into my_group
pyportal.splash.append(sparkline1)

text_font = bitmap_font.load_font("/fonts/Helvetica-Oblique-17.bdf")
text_font.load_glyphs(b'M1234567890o.%')
DATACOLOR = 0x117766
DATE_COLOR=0x334455
DATA_LABELS = [
    Label(text_font, text="{:.{}f} {}".format(feed_info[0][1], 0, feed_info[0][2]), color=DATACOLOR, x=85, y=40, scale=2, background_tight=True),
    Label(text_font, text="{:.{}f}{}".format(
        feed_info[1][1], 44, feed_info[1][2]), color=DATACOLOR, x=200, y=40, scale=2),
    Label(text_font, text="{:.{}f} {}".format(
        feed_info[2][1], 3, feed_info[2][2]), color=DATACOLOR, x=85, y=80, scale=2),
    Label(text_font, text="{:.{}f}{}".format(
        feed_info[3][1], 0, feed_info[3][2]), color=DATACOLOR, x=200, y=80, scale=2)
]
DATE_LABEL = [
    Label(text_font, text="0000-00-00 00:00",color=DATE_COLOR,x=90, y=107),
    Label(text_font, text="00-00-00 00:00", color=DATE_COLOR, x=88, y=130, scale=2)
]
for label in DATA_LABELS + DATE_LABEL:
    pyportal.splash.append(label)
my_group = Graphics()  # my_group = displayio.Group()
display = board.DISPLAY
# Add my_group (containing the sparkline) to the display
display.show(pyportal.splash)
#my_group.qrcode(
pyportal.show_QR(
    "https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true", qr_size=5, x=308, y=2)


while True:
    now = time.localtime()
    s = "%02d%02d%02d %02d:%02d" % (now.tm_year-2000, now.tm_mon, now.tm_mday,now.tm_hour, now.tm_min)
    #print(current_time.tm_hour,":",current_time.tm_min)
    DATE_LABEL[1].text=s ##time now
    try:
        print('Fetching Adafruit IO Feed Value..')
        gc.collect()
        print(gc.mem_free())
        for i, feed in enumerate(IO_FEEDS):
            liveurl = "https://io.adafruit.com/api/v2/{0}/feeds/{1}/data?X-AIO-Key={2}&limit=1".format(IO_USER, feed, IO_KEY)
            print(liveurl)
            value = pyportal.network.fetch_data(liveurl, json_path=([0,'value'],[0,'created_at']))

            print("%.*f %s" % (feed_info[i][1], float(value[0]), feed_info[i][2]))
            DATA_LABELS[i].text = "%.*f %s" % (
                feed_info[i][1], float(value[0]), feed_info[i][2])
        DATE_LABEL[0].text=value[1] ##time for last fecthed  value
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

    print(int(sparkline1.y_bottom))
    print(sparkline1.y_min)
    palette = displayio.Palette(1)
    palette[0] = 0x125690
    points = [(25, int(sparkline1.y_bottom)), (300, int(sparkline1.y_bottom)),
              (380, int(sparkline1.y_bottom))]
    polygon = vectorio.Polygon(pixel_shader=palette, points=points, x=0, y=0)
    pyportal.splash.append(polygon)
    display.show(pyportal.splash)
    gc.collect()
    #  pyportal.show_QR("https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true", qr_size=5, x=290, y=0)
    # my_group.display.show(my_group.splash)
    print(gc.mem_free())
    time.sleep(60)
