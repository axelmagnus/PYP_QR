
my_group = Graphics()  # my_group = displayio.Group()
display = board.DISPLAY
my_group.qrcode(
    "https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true", qr_size=5, x=308, y=2)
# add the sparkline into my_group
my_group.splash.append(sparkline1)

# Add my_group (containing the sparkline) to the display
my_group.display.show(my_group.splash)

my_group = Graphics()  # my_group = displayio.Group()
display = board.DISPLAY
my_group.qrcode(
    "https://io.adafruit.com/axelmagnus/dashboards/battlevel?kiosk=true", qr_size=5, x=308, y=2)
# add the sparkline into my_group
my_group.splash.append(sparkline1)

# Add my_group (containing the sparkline) to the display
my_group.display.show(my_group.splash)


""" text_font=cwd+"/fonts/Helvetica-Oblique-17.bdf",   
    text_position=(30, 65),
    text_color=0xFFFFFF,
    text_wrap=35,  # wrap feed after 35 chars
    text_maxlen=160  """

"https://io.adafruit.com/api/v2/axelmagnus/feeds/ab-weather.winddirection/data?X-AIO-Key=1a20315d078d4304bee799ce4b2af0e7&limit=1"
