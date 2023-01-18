import time
import board
from adafruit_pyportal import PyPortal, Graphics
#from digitalio import DigitalInOut
import busio
#import json
from adafruit_display_shapes.sparkline import Sparkline
import displayio
from secrets import secrets
import gc
import traceback
import microcontroller
from adafruit_datetime import datetime, timedelta, _MONTHNAMES, _DAYNAMES
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
import vectorio
import adafruit_touchscreen
from adafruit_button import Button
from adafruit_progressbar.progressbar import HorizontalProgressBar

cwd = ("/"+__file__).rsplit('/', 1)[0]
pyportal = PyPortal(
    json_path='data',
    status_neopixel=board.NEOPIXEL,
    default_bg=cwd+"pyp_spark_qr.bmp"
    #debug=True
)

# Adafruit IO Account
IO_USER = secrets['aio_username']
IO_KEY = secrets['aio_key']
REFRESH_TIME = 600  # seconds between refresh. should match sensors updatetime
HOURS = 48  # how far back to go
HOURS = 48  # how far back to go
RESOLUTION = 120  # in minutes 1,2 30, 60, 120
#maxdatapoints = HOURS//(RESOLUTION//60)# is it used?

soundBeep = "/sounds/beep.wav"

# Adafruit IO Feeds
feed_group = 'esp32s2tft'
# feedname, number of decimals, unit, pretty name
feed_info = (('temp', 1, "\u00b0C", 'Temp'), ('hum', 0, "%", 'Humidity'),
             ('voltage', 2, "V",'Battery'), ('percent', 1, "%", 'Batt life'))
IO_FEEDS = ()
for feed in feed_info:
    #print(feed[0])
    IO_FEEDS += feed_group+"."+feed[0],
sparkfeed_index = 0  # which to show on the graph

# speed up projects with lots of text by preloading the font!
# pyportal.preload_font()

# LeagueSpartan-Bold-16.bdf")  # "Orbitron_Bold_16.h")
text_font = bitmap_font.load_font("/fonts/Helvetica-Oblique-17.bdf")
#text_font.load_glyphs(b'M1234567890o.%')
DATACOLOR = 0x117766
DATE_COLOR = 0x334455
DATA_LABELS = [
    Label(text_font, text="{:.{}f} {}".format(
        0, feed_info[0][1],  feed_info[0][2]), color=DATACOLOR, x=85, y=40, scale=2, background_tight=True),
    Label(text_font, text="{:.{}f} {}".format(
        0, feed_info[1][1],  feed_info[1][2]), color=DATACOLOR, x=230, y=40, scale=2),
    Label(text_font, text="{:.{}f} {}".format(
        0, feed_info[2][1],  feed_info[2][2]), color=DATACOLOR, x=85, y=80, scale=2),
    Label(text_font, text="{:.{}f}{}".format(
        0, feed_info[3][1],  feed_info[3][2]), color=DATACOLOR, x=230, y=80, scale=2)
]
DATE_LABEL = Label(text_font, text="1 Jan 00:00:00",
                   color=DATE_COLOR, x=99, y=133, scale=2)
STATUS_LABEL = Label(text_font, text=f"SSID: {secrets['ssid']}",
                     color=0x000000, x=80, y=108)
GRAPH_LABEL = Label(text_font, text="Temp: 96 h",
                    color=0x000000, x=82, y=168)
GRAPH_HI_LABEL = Label(text_font, text="---", color=0x000000, x=425, y=190)
GRAPH_LO_LABEL = Label(text_font, text="---", color=0x000000, x=425, y=263)
for label in DATA_LABELS:
    pyportal.splash.append(label)
pyportal.splash.append(DATE_LABEL)
pyportal.splash.append(STATUS_LABEL)
pyportal.splash.append(GRAPH_LABEL)
pyportal.splash.append(GRAPH_HI_LABEL)
pyportal.splash.append(GRAPH_LO_LABEL)
display = board.DISPLAY

datalabels = True #keep track of which labels are in the data area; data or weather forecast

WEATHER_LABELS = [
    Label(text_font, text="Curr", color=DATACOLOR, x=85, y=30, scale=2, background_tight=True),
    Label(text_font, text="Forecast", color=DATACOLOR, x=85, y=60, scale=2),
    Label(text_font, text="Sunrise:      Sunset:",
          color=DATACOLOR, x=85, y=90, scale=1),
    Label(text_font, text="Min, Max", color=DATACOLOR,
          x=200, y=30, scale=1, background_tight=True),
]
def show_weather():  # show forecast,
    #mintemp,maxtemp,act_temp=0
    #sunrise, sunset, description=None

    print(gc.mem_free())
    weather_data = pyportal.network.fetch_data(
        "http://api.openweathermap.org/data/2.5/forecast?q=Malmo, SE&appid=4acdd2457856e1ef6c064f1e928ea71e&cnt=8", json_path=[]) #3 hour forecasts this is cnt*3=24 h
    #print(weather_data[0])

    hi = max([item['main']['temp'] for item in weather_data[0]['list']])-273.15
    lo = min([item['main']['temp'] for item in weather_data[0]['list']])-273.15

    WEATHER_LABELS[0].text = "%.1f\u00b0C" % (float(weather_data[0]['list'][0]['main']['temp'])-273.15)
    WEATHER_LABELS[3].text="24h H: %.1f\u00b0 L: %.1f\u00b0" % (hi,lo)

    desc = weather_data[0]['list'][0]['weather'][0]['description']
    desc=desc[0].upper() + desc[1:]
    WEATHER_LABELS[1].text = desc

    sunrise = time.localtime(
        weather_data[0]['city']['sunrise']+weather_data[0]['city']['timezone'])
    sunset = time.localtime(
        weather_data[0]['city']['sunset']+weather_data[0]['city']['timezone'])
    forecast_time = time.localtime(weather_data[0]['list'][0]['dt'])

    try:
        rainml = weather_data[0]['list'][0]['rain']['3h']
    except:  #theres no  rain entry in the json
        print("except")
        rainml=0
    WEATHER_LABELS[2].text = "R: {:.0f} mm PoP: {:.0f}% Sunrise: {:d}:{:02d}".format(rainml, float(weather_data[0]['list'][0]['pop'])*100.0,  sunrise.tm_hour, sunrise.tm_min)
    del weather_data
    gc.collect()
    print(gc.mem_free())
    STATUS_LABEL.text = "Forecast:{:d} {:s} {:d}:{:02d} Sunset: {:d}:{:02d}".format(forecast_time.tm_mday, _MONTHNAMES[forecast_time.tm_mon],forecast_time.tm_hour,forecast_time.tm_min, sunset.tm_hour, sunset.tm_min)
    buttons[6].label = "Data"  # keep track of what is shown
#TODO #4
buttons = []
TAB_BUTTON_HEIGHT = 79
TAB_BUTTON_WIDTH = 70
# Main User Interface Buttons
button_temp = Button(
    x=0,  # Start after width of a button
    y=display.height-3*TAB_BUTTON_HEIGHT,
    width=TAB_BUTTON_WIDTH,
    height=TAB_BUTTON_HEIGHT,
    style=Button.ROUNDRECT,
    label=feed_info[0][3],
    label_font=text_font,
    label_color=0xFFF499,
    fill_color=None,  # 0x5C5B5C,
    outline_color=None,
    selected_fill=0x1A1A1A,
    selected_outline=0x2E2E2E,
    selected_label=0x525252,
    # style = ROUNDRECT,
)
buttons.append(button_temp)
button_batt = Button(
    x=0,  # Start at furthest left
    y=display.height-2*TAB_BUTTON_HEIGHT,  # Start at top
    width=TAB_BUTTON_WIDTH,  # Calculated width
    height=TAB_BUTTON_HEIGHT,
    style=Button.ROUNDRECT,
    label=feed_info[2][3],
    label_font=text_font,
    label_color=0xFFF499,
    fill_color=None,  # 0x5C5B5C,
    outline_color=None,
    selected_fill=0x1A1A1A,
    selected_outline=0x2E2E2E,
    selected_label=0x525252,
    # style=ROUNDRECT,
)
buttons.append(button_batt)  # adding this button to the buttons group
button_charge = Button(
    x=0,  # Start at furthest left
    y=display.height-TAB_BUTTON_HEIGHT,  # Start at top
    width=TAB_BUTTON_WIDTH,  # Calculated width
    height=TAB_BUTTON_HEIGHT,  # Static height
    style=Button.ROUNDRECT,
    label=feed_info[3][3],
    label_font=text_font,
    label_color=0xFFF499,
    fill_color=None,  # 0x5C5B5C,
    outline_color=None,
    selected_fill=0x1A1A1A,
    selected_outline=0x2E2E2E,
    #selected_label=0x525252,
    # style=ROUNDRECT, 
)
buttons.append(button_charge)  # adding this button to the buttons group
TAB_BUTTON_HEIGHT = 44
TAB_BUTTON_WIDTH = 180
button_1w = Button(
    x=70,  # Start at furthest left
    y=display.height-TAB_BUTTON_HEIGHT,  # Start at top
    width=TAB_BUTTON_WIDTH,  # Calculated width
    height=TAB_BUTTON_HEIGHT,  # Static height
    style=Button.ROUNDRECT,
    label="96 h",
    label_font=text_font,
    label_color=0xFFF499,
    fill_color=0xBB0033,  # 0x5C5B5C,
    outline_color=0x00BBFF,
    selected_fill=0x1A1A1A,
    selected_outline=0xFF2200,
    selected_label=0x005252,
)
buttons.append(button_1w)
button_48h = Button(
    x=70+TAB_BUTTON_WIDTH,  # Start at furthest left
    y=display.height-TAB_BUTTON_HEIGHT,  # Start at top
    width=TAB_BUTTON_WIDTH,  # Calculated width
    height=TAB_BUTTON_HEIGHT,  # Static height
    style=Button.ROUNDRECT,
    label="48 h",
    label_font=text_font,
    label_color=0xFFF499,
    fill_color=0x00BB33,  # 0x5C5B5C,
    outline_color=0xFF7676,
    selected_fill=0x1A1A1A,
    selected_outline=0xFF2200,
    selected_label=0x005252,
)
buttons.append(button_48h)
button_reload = Button(
    x=377,  
    y=100, 
    width=100,  # Calculated width
    height=80,  # Static height
    label="Update",
    label_font=text_font,
    label_color=0xFFF499,
    style=Button.ROUNDRECT,
    fill_color=None,  # 0x5C5B5C,
    outline_color=0xFF7676,
    selected_fill=0x1A1A1A,
    selected_outline=0xFF2200,
    selected_label=0x005252,
)
buttons.append(button_reload)
button_weather = Button(
    x=0,  # Start after width of a button
    y=0,
    width=73,
    height=75,
    style=Button.ROUNDRECT,
    label="Weather",
    label_font=text_font,
    label_color=0xFFF499,
    fill_color=None,  # 0x5C5B5C,
    outline_color=None,
    selected_fill=0x1A1A1A,
    selected_outline=0x2E2E2E,
    selected_label=0x525252,
    # style = ROUNDRECT,
)
buttons.append(button_weather)
# Add all of the main buttons to the splash Group
for b in buttons:
    #b.style = Button.ROUNDRECT,
    pyportal.splash.append(b)

progress_bar = HorizontalProgressBar(
    (115, 215),
    (270, 25),
    bar_color=0x00BB33,
    outline_color=0xAAAAAA,
    fill_color=0x777777,
)

# Initializes the display touch screen area
ts = adafruit_touchscreen.Touchscreen(
    board.TOUCH_XL, board.TOUCH_XR,
    board.TOUCH_YD, board.TOUCH_YU,
    calibration=((5200, 59000), (5800, 57000)),
    size=(480, 320),
)

#my_group = Graphics()  # my_group = displayio.Group()
sparkline1 = Sparkline(width=335, height=85, max_items=200,
                       x=80, y=188, color=0x000000)
# add the sparkline into my_group
pyportal.splash.append(sparkline1)
# Add my_group (containing the sparkline) to the display
display.show(pyportal.splash)
#my_group.qrcode(
pyportal.show_QR(
    "https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true", qr_size=3, x=375, y=2)

value = None #for json data
print("getting time")
pyportal.get_local_time()
STATUS_LABEL.text=f"Connected: {secrets['ssid']}"
lastupdated = datetime.now()
now = time.localtime()
firstrun = True #set to true  for updating  data labels
reload = False  # for reload button

#http://api.openweathermap.org/data/2.5/weather?q=Malmo, SE&appid=4acdd2457856e1ef6c064f1e928ea71e

while True:
    oldnow = now
    now = time.localtime()
    s = "%d %s %d:%02d:%02d" % (
        now.tm_mday, _MONTHNAMES[now.tm_mon], now.tm_hour, now.tm_min, now.tm_sec)
    if oldnow.tm_sec != now.tm_sec or firstrun:#update time to fetch data from
        DATE_LABEL.text = s  # time now
        ENDTIME = "%04d-%02d-%02d%c%04d:%02d:%02d%c" % (
            now.tm_year, now.tm_mon, now.tm_mday, "T", now.tm_hour, now.tm_min, now.tm_sec, "Z")
    #nu = datetime.now()  # to use for latest publlished data
    try:
        gc.collect()
        #+ 5 so if thereis offset issues

        if (datetime.now() - lastupdated).total_seconds() > REFRESH_TIME  + 5 or firstrun or reload:
            print("updating..")
           # pyportal.get_local_time()
            lastupdated = datetime.now()
            print("if...", lastupdated)
            # keep track of what is shown: #change forecast to data labels
            #if buttons[6].label == "Weather" and 
            if b.label == "Data" :#when updating data, change to that view (must append labels)
                for label in WEATHER_LABELS:
                    pyportal.splash.remove(label)
                gc.collect()
                for label in DATA_LABELS:
                    pyportal.splash.append(label)
                b.label = "Weather"
            if b.label == "Weather": #show feed data (reload)
                STATUS_LABEL.text ='Fetching data...'
                print()
                progress_bar.value=0
                pyportal.splash.append(progress_bar)
                for i, feed in enumerate(IO_FEEDS):#fill datalabels
                    liveurl = "https://io.adafruit.com/api/v2/{0}/feeds/{1}/data?X-AIO-Key={2}&limit=1".format(
                        IO_USER, feed, IO_KEY)
                    #print(liveurl)
                    value = pyportal.network.fetch_data(
                        liveurl, json_path=([0, 'value'], [0, 'created_at']))
                    if firstrun:#get last data points time and sync updates
                        pyportal.play_file(soundBeep)
                    lastdata = datetime.fromisoformat(value[1][0:-1])
                    # feed  time is one hour behind
                    lastdata += timedelta(minutes=60)
                    # if feed is alive, use it for sync.
                    if lastdata > lastupdated - timedelta(seconds=REFRESH_TIME):
                        lastupdated = lastdata
                    print("ld", lastdata)
                    DATA_LABELS[i].text = "%.*f %s" % (
                    feed_info[i][1], float(value[0]), feed_info[i][2])
                    progress_bar.value = 100*(i+1)/len(IO_FEEDS)
                pyportal.splash.remove(progress_bar)

                date_part, time_part = value[1].split("T")
                year, month, day = date_part.split("-")
                hours, minutes, seconds = time_part[0:-1].split(":")
                #seconds = seconds[0:-1]
                adjhours = int(hours) + 1  # TZ or DST or something
                STATUS_LABEL.text = "Last data: %d %s %d:%02d:%02d" % (
                    lastdata.day,
                    _MONTHNAMES[lastdata.month],
                    lastdata.hour,
                    lastdata.minute,
                    lastdata.second,
                )

                print("Last data: %2d/%d %02d:%2d:%01d" % (lastdata.day,
                    lastdata.month, lastdata.hour, lastdata.minute,lastdata.second))
                # time for last fecthed  value
                #lastupdated = min(lastupdated, datetime.now())#either it has been updaated from feed, firstrun or its now
                print("last upd", lastupdated, "date now", datetime.now())
                buttons[6].label = "Weather"  # keep track of what is shown
            else:#update weather
                show_weather()
                buttons[6].label = "Data"  # keep track of what is shown
            reload=False
        
        touch = ts.touch_point

        if touch:  # Only do this if the screen is touched, or fill buttons with names
            # loop with buttons using enumerate() to number each button group as i
            for i, b in enumerate(buttons):
                if i < 3:
                    b.label_color = 0xFFF499
                # Test each button to see if it was pressed, set data source aand label and fetch data for  graph
                if b.contains(touch):
                    gc.collect()
                    print("if touch",gc.mem_free())
                    if 0 <= i <= 4:  # Update sparkline, clear to be able to play sound
                        sparkline1.clear_values()  # doesnt clear top and bottom"
                    #print(sparkline1.y_bottom)
                        gc.collect()
                        print("clear sline", gc.mem_free())
                        #pyportal.play_file(soundBeep)
                    if i < 3: #indicate what feed is pressed/shown
                        b.label_color = 0x000000
                    if i == 0:
                        print('Temp')
                        sparkfeed_index = 0
                        #b.label_color = 0x000000  # indicate what feed is pressed/shown
                        while ts.touch_point:  # for debounce
                            pass
                    if i == 1:
                        print('Battery')
                        sparkfeed_index = 2
                        while ts.touch_point:  # for debounce
                            pass
                    if i == 2:
                        print('Charge')
                        sparkfeed_index = 3
                        while ts.touch_point:  # for debounce
                            pass
                    if i == 3:#96
                        print('1 week')
                        #GRAPH_LABEL.text = "Fetching data 1 week"
                        HOURS = 96
                        RESOLUTION = 120
                        buttons[3].fill_color = 0x00BB33
                        buttons[4].fill_color = 0xBB0033
                        while ts.touch_point:  # for debounce
                            pass
                    if i == 4:#48
                        print('48 h')
                        #GRAPH_LABEL.text = "Fetching data 48 h"
                        HOURS = 48
                        RESOLUTION = 120
                        buttons[4].fill_color = 0x00BB33
                        buttons[3].fill_color = 0xBB0033
                        while ts.touch_point:  # for debounce
                            pass
                    if i == 5: #Reload datalabels
                        reload=True
                        STATUS_LABEL.text = "Updating data..."
                    if 0<= i <=4:#Update sparkline
                        progress_bar.value = 0
                        pyportal.splash.append(progress_bar)
                        print("update sline", gc.mem_free())
                        GRAPH_LABEL.text = "Fetching {} {} h".format(
                                    feed_info[sparkfeed_index][3], HOURS)
                        DATA_SOURCE = "https://io.adafruit.com/api/v2/{0}/feeds/{1}/data/chart?X-AIO-Key={2}&end_time={3}&hours={4}&resolution={5}".format(
                            IO_USER, IO_FEEDS[sparkfeed_index], IO_KEY, ENDTIME, HOURS, RESOLUTION)
                        print(
                            "_____________________Get sparkline data____________________")
                        print(DATA_SOURCE)
                        value = pyportal.network.fetch_data(
                            DATA_SOURCE, json_path=['data'])
                        GRAPH_LABEL.text = f"# of records: {len(value[0])}"
                        print(len(value[0]))
                        #display.auto_refresh = False
                        """
                        pyportal.splash.remove(sparkline1)
                        gc.collect()
                        sparkline1 = Sparkline(
                            width=335, height=85, max_items=len(value[0]), x=80, y=188, color=0x000000)
                        update()
                        init?
                        sparkline1.y_bottom = 100.0
                        sparkline1.y_top = 0.0
                        """

                        gc.collect()
                        max_value = max(value[0], key=lambda x: float(x[1]))
                        #print("max", max_value[1])
                        min_value = min(value[0], key=lambda x: float(x[1]))
                        #print("min", min_value[1])
                        """

                        sparkline1.y_top = float(max_value[1])

                        sparkline1.y_bottom = float(min_value[1])
                        """
                        display.auto_refresh = True
                        #progress_bar.maximum = len(value)
                        #fill sparkline, progressbar
                        print("before add", gc.mem_free())
                        for i, item in enumerate(value[0]):
                            progress_bar.value = 100*(i+1)/len(value[0])
                            sparkline1.add_value(float(item[1]), update=False)

                        #display.show(pyportal.splash)
                        # print(sparkline1.values())
                        pyportal.splash.remove(progress_bar)
                        gc.collect()
                        GRAPH_LO_LABEL.text = f"%.*f%s" % (
                            feed_info[sparkfeed_index][1], min(sparkline1.values()), feed_info[sparkfeed_index][2])
                        GRAPH_HI_LABEL.text = f"%.*f%s" % (
                            feed_info[sparkfeed_index][1], max(sparkline1.values()), feed_info[sparkfeed_index][2])
                        """
                        #print("bottom top")
                        #print(sparkline1.y_bottom)
                        #sparkline1.y_top = max(sparkline1.values())

                        #sparkline1.y_bottom = min(sparkline1.values())
                        #print(sparkline1.y_top)
                        #sparkline1.y_bottom = min(sparkline1.values())

                        sparkline1.y_max = 15
                        sparkline1.min_value = 3
                        sparkline1.max_value = 20
                        """
                        GRAPH_LABEL.text = "{}: {} h R:{} h #:{:d}".format(
                            feed_info[sparkfeed_index][3], len(value[0])*RESOLUTION/60, RESOLUTION/60, len(value[0]))
                        value = None
                        gc.collect()
                        print("mem b4 sline", gc.mem_free())
                        display.auto_refresh =False
                        sparkline1.update()
                        gc.collect()
                        display.auto_refresh = True
                    if i == 6:#fetch and show weather/data
                        if b.label == "Weather":
                            for label in DATA_LABELS:  # take out Data labels, in with weather labels
                                pyportal.splash.remove(label)
                            gc.collect()
                            for label in WEATHER_LABELS:
                                pyportal.splash.append(label)
                            show_weather()
                            # keep track of what is shown
                            buttons[6].label = "Data"
                            continue
                        if b.label == "Data":
                            for label in WEATHER_LABELS:
                                pyportal.splash.remove(label)
                            gc.collect()
                            for label in DATA_LABELS:
                                pyportal.splash.append(label)
                            b.label = "Weather"
                            STATUS_LABEL.text = "Last data: %d %s %d:%02d:%02d" % (lastdata.day,_MONTHNAMES[lastdata.month],lastdata.hour,lastdata.minute,lastdata.second,)
                            #reload=True dont reload automatically, wait for time or press Update button
        while ts.touch_point:  # for debounce
            pass
        firstrun=False
    except Exception as e:
        traceback.print_exception(type(e), e, e.__traceback__)
        print("Some error occured, retrying! -", e)
        print(sparkline1.values())
        try:
            GRAPH_LABEL.text = "Memory error"
        except:
            pass
        value = None
        gc.collect()
        print(gc.mem_free())
        import supervisor
        supervisor.reload()
        supervisor.runtime.usb_connected
        supervisor.runtime.serial_connected
        #import microcontroller cannot be connected to usb
        #microcontroller.reset()


    #gc.collect()
    #  pyportal.show_QR("https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true", qr_size=5, x=290, y=0)
    # my_group.display.show(my_group.splash)
"""
    print(int(sparkline1.y_bottom))
    print(sparkline1.y_min)
    palette = displayio.Palette(1)
    palette[0] = 0x125690
    points = [(25, int(sparkline1.y_bottom)), (300, int(sparkline1.y_bottom)),
              (380, int(sparkline1.y_bottom))]
    polygon = vectorio.Polygon(pixel_shader=palette, points=points, x=0, y=0)
    pyportal.splash.append(polygon)
    display.show(pyportal.splash) 
 """
