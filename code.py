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
    default_bg=cwd+"pyp_spark_qr.bmp",
    debug=True
)

# Adafruit IO Account
IO_USER = secrets['aio_username']
IO_KEY = secrets['aio_key']
REFRESH_TIME = 600  # seconds between refresh. should match sensors updatetime
HOURS = 144  # how far back to go
RESOLUTION = 120  # in minutes 1,2 30, 60, 120
#maxdatapoints = HOURS//(RESOLUTION//60)# is it used?

soundBeep = "/sounds/beep.wav"

# Adafruit IO Feeds
feed_group = 'esp32s2tft'
# feedname, number of decimals, unit, pretty name
feed_info = (('temp', 1, "C", 'Temp'), ('hum', 0, "  %", 'Humidity'), ('voltage', 2, "V",'Battery'), ('percent', 1, "%", 'Batt life'))  
IO_FEEDS = ()
for feed in feed_info:
    #print(feed[0])
    IO_FEEDS += feed_group+"."+feed[0],
sparkfeed_index = 0  # which to show on the graph

# speed up projects with lots of text by preloading the font!pyportal.preload_font()

text_font = bitmap_font.load_font("/fonts/Helvetica-Oblique-17.bdf")
text_font.load_glyphs(b'M1234567890o.%')
DATACOLOR = 0x117766
DATE_COLOR = 0x334455
DATA_LABELS = [
    Label(text_font, text="{:.{}f} {}".format(
        0, feed_info[0][1],  feed_info[0][2]), color=DATACOLOR, x=85, y=40, scale=2, background_tight=True),
    Label(text_font, text="{:.{}f}{}".format(
        0, feed_info[1][1],  feed_info[1][2]), color=DATACOLOR, x=190, y=40, scale=2),
    Label(text_font, text="{:.{}f} {}".format(
        0, feed_info[2][1],  feed_info[2][2]), color=DATACOLOR, x=85, y=80, scale=2),
    Label(text_font, text="{:.{}f}{}".format(
        0, feed_info[3][1],  feed_info[3][2]), color=DATACOLOR, x=190, y=80, scale=2)
]
DATE_LABEL = Label(text_font, text="000000 00:00",
                   color=DATE_COLOR, x=88, y=130, scale=2)
STATUS_LABEL = Label(text_font, text=f"SSID: {secrets['ssid']}",
                     color=0x000000, x=90, y=108)
GRAPH_LABEL = Label(text_font, text="Temp: 144 h",
                    color=0x000000, x=82, y=168)
GRAPH_HI_LABEL = Label(text_font, text="---", color=0x000000, x=430, y=190)
GRAPH_LO_LABEL = Label(text_font, text="---", color=0x000000, x=430, y=263)

for label in DATA_LABELS:
    pyportal.splash.append(label)
pyportal.splash.append(DATE_LABEL)
pyportal.splash.append(STATUS_LABEL)
pyportal.splash.append(GRAPH_LABEL)
pyportal.splash.append(GRAPH_HI_LABEL)
pyportal.splash.append(GRAPH_LO_LABEL)
display = board.DISPLAY

buttons = []
TAB_BUTTON_HEIGHT = 73
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
    label_color=0xFF00FF,
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
    fill_color=0x5C5B5C, #None,  # 0x5C5B5C,
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
    label="1 week",
    label_font=text_font,
    label_color=0xFFF499,
    fill_color=0x00BB33,  # 0x5C5B5C,
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
    fill_color=0xBB0033,  # 0x5C5B5C,
    outline_color=0xFF7676,
    selected_fill=0x1A1A1A,
    selected_outline=0xFF2200,
    selected_label=0x005252,
)
buttons.append(button_48h)
button_reload = Button(
    x=430,  # Start at furthest left
    y=display.height-TAB_BUTTON_HEIGHT,  # Start at top
    width=60,  # Calculated width
    height=TAB_BUTTON_HEIGHT,  # Static height
    label="Update",
    label_font=text_font,
    label_color=0xFFF499,
    fill_color=None,  # 0x5C5B5C,
    outline_color=0xFF7676,
    selected_fill=0x1A1A1A,
    selected_outline=0xFF2200,
    selected_label=0x005252,
)
buttons.append(button_reload)
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
    "https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true", qr_size=3, x=308, y=2)

value = None
pyportal.get_local_time()
lastupdated = datetime.now()
print("starting")
now = time.localtime()
firstrun=True
reload=False #for reload button

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
            pyportal.get_local_time()
            lastupdated = datetime.now()
            print("if...",lastupdated)
            STATUS_LABEL.text ='Fetching data...'
            progress_bar.value=0
            pyportal.splash.append(progress_bar)
            for i, feed in enumerate(IO_FEEDS):
                liveurl = "https://io.adafruit.com/api/v2/{0}/feeds/{1}/data?X-AIO-Key={2}&limit=1".format(
                    IO_USER, feed, IO_KEY)
                #print(liveurl)
                value = pyportal.network.fetch_data(
                    liveurl, json_path=([0, 'value'], [0, 'created_at']))
                if firstrun:#get last data points time and sync updates
                    pyportal.play_file(soundBeep)
                #print("%.*f %s" %
                #     (feed_info[i][1], float(value[0]), feed_info[i][2]))

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

            print("Last data: %2d/%d %02d:%2d:%01d" % (lastdata.day, lastdata.month, lastdata.hour, lastdata.minute,lastdata.second))
            # time for last fecthed  value
            print("last upd", lastupdated, "date now", datetime.now())#lastupdated = min(lastupdated, datetime.now())#either it has been updaated from feed, firstrun or its now
            reload=False
        #print("first:",firstrun)
        if firstrun:#Faake touch so it shows a graaph, default, temp button
            touch = (62, 122, 10514) #init with temp
        else:
            touch = ts.touch_point
 #           pyportal.splash.append(progress_bar)
        
        if touch:  # Only do this if the screen is touched, or fill buttons with names
            # loop with buttons using enumerate() to number each button group as i
            for i, b in enumerate(buttons):
                if i < 3:
                    b.label_color = 0xFFF499
                if b.contains(touch):  # Test each button to see if it was pressed, set data source aand label and fetch data for  graph
                    gc.collect()
                    print(gc.mem_free())
                    pyportal.play_file(soundBeep)
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
                    if i == 3:#144
                        print('1 week')
                        #GRAPH_LABEL.text = "Fetching data 1 week"
                        HOURS = 144
                        RESOLUTION = 120
                        buttons[3].fill_color = 0x00BB33
                        buttons[4].fill_color = 0xBB0033
                        while ts.touch_point:  # for debounce
                            pass
                    if i == 4:#48
                        print('48 h')
                        #GRAPH_LABEL.text = "Fetching data 48 h"
                        HOURS = 48
                        RESOLUTION = 60
                        buttons[4].fill_color = 0x00BB33
                        buttons[3].fill_color = 0xBB0033
                        while ts.touch_point:  # for debounce
                            pass
                    if i == 5: #Reload datalabels
                        reload=True
                    if 0<= i <=4:#Update sparkline
                        progress_bar.value = 0
                        pyportal.splash.append(progress_bar)
                        print(gc.mem_free())
                        sparkline1.clear_values()  # doesnt clear top and bottom"
                        #print(sparkline1.y_bottom)
                        print(gc.mem_free())
                        GRAPH_LABEL.text = "Fetching {} {} h".format(
                                    feed_info[sparkfeed_index][3], HOURS)
                        DATA_SOURCE = "https://io.adafruit.com/api/v2/{0}/feeds/{1}/data/chart?X-AIO-Key={2}&end_time={3}&hours={4}&resolution={5}".format(
                            IO_USER, IO_FEEDS[sparkfeed_index], IO_KEY, ENDTIME, HOURS, RESOLUTION)
                        print(
                            "_____________________Get sparkline data____________________")
                        #print(DATA_SOURCE)
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
                        """
                        
                        #sparkline1.__init__()

                        """
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
                        for i, item in enumerate(value[0]):#fill sparkline, progressbar
                            progress_bar.value = 100*(i+1)/len(value[0])
                            sparkline1.add_value(float(item[1]), update=False)

                        #display.show(pyportal.splash)
                        # print(sparkline1.values())
                        pyportal.splash.remove(progress_bar)
                        gc.collect()
                        GRAPH_LO_LABEL.text = f"%.*f %s" % (
                            feed_info[sparkfeed_index][1], min(sparkline1.values()), feed_info[sparkfeed_index][2])
                        GRAPH_HI_LABEL.text = f"%.*f %s" % (
                            feed_info[sparkfeed_index][1], max(sparkline1.values()), feed_info[sparkfeed_index][2])
                        """
                        #print("bottom top")
                        #print(sparkline1.y_bottom)
                        #sparkline1.y_top = max(sparkline1.values())

                        #sparkline1.y_bottom = min(sparkline1.values())
                        #print(sparkline1.y_top)
                        #sparkline1.y_bottom = min(sparkline1.values())
                        
                        sparkline1.y_max=15
                        sparkline1.min_value=3
                        sparkline1.max_value=20
                        """
                        GRAPH_LABEL.text = "{}: {} h R:{} h #:{:d}".format(
                            feed_info[sparkfeed_index][3], len(value[0])*RESOLUTION/60, RESOLUTION/60, len(value[0]))
                        value=None
                        gc.collect()
                        print("mem b4 sline", gc.mem_free())
                        display.auto_refresh =False
                        sparkline1.update()
                        display.auto_refresh = True       
               
        firstrun=False    
    except Exception as e:
        traceback.print_exception(type(e), e, e.__traceback__)
        print("Some error occured, retrying! -", e)
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
    """ print(int(sparkline1.y_bottom))
    print(sparkline1.y_min)
    palette = displayio.Palette(1)
    palette[0] = 0x125690
    points = [(25, int(sparkline1.y_bottom)), (300, int(sparkline1.y_bottom)),
              (380, int(sparkline1.y_bottom))]
    polygon = vectorio.Polygon(pixel_shader=palette, points=points, x=0, y=0)
    pyportal.splash.append(polygon)
    display.show(pyportal.splash) 
 """
