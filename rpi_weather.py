#! /usr/bin/env python

import drivers
from time import sleep
from datetime import datetime
import RPi.GPIO as GPIO
from pyowm import OWM
from socket import timeout

GPIO.setmode(GPIO.BCM)

display = drivers.Lcd()

GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Down Button
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Up Button

owm = OWM('')
mgr = owm.weather_manager()

reg = owm.city_id_registry()
list_of_locations = reg.locations_for('warsaw', country='PL')
city = list_of_locations[0]

uvimgr = owm.uvindex_manager()
uvi = uvimgr.uvindex_around_coords(city.lat, city.lon)

customchar = drivers.CustomCharacters(display)

# Custom character definitions
customchar.char_1_data=[ #thermometer symbol
        "00100",
        "01010",
        "01010",
        "01110",
        "01110",
        "11111",
        "11111",
        "01110"]

customchar.char_2_data=[ #humidity symbol
        "00100",
        "00100",
        "01010",
        "01010",
        "10001",
        "10001",
        "10001",
        "01110"]

customchar.char_3_data=[ #flag symbol
        "11000",
        "10110",
        "10001",
        "10001",
        "11001",
        "10110",
        "10000",
        "10000"]

customchar.char_4_data=[ #cloud symbol
        "00000",
        "00000",
        "00110",
        "11001",
        "10001",
        "01110",
        "00000",
        "00000"]

customchar.load_custom_characters_data()

screen = [" ",
	  " Weather Station ",
	  " Initializing ...",
	  " ",
	  " ",
	  " ",
	  " "]

def UpdateWeather():
	observation = mgr.weather_at_place('Warsaw, PL')
	w = observation.weather
	temperature = w.temperature('celsius')
	wind = observation.weather.wind()
	sunrise = w.sunrise_time(timeformat='date')
	sunset = w.sunset_time(timeformat='date')
	pressure = w.pressure
	now = datetime.now()
	#rain = observation.weather.rain()
	screen[0] = "Gliwice {:3.2f}".format(city.lat) + " {:3.2f}".format(city.lon)
	screen[1] = w.detailed_status
	screen[2] = "{0x00}" + "{:3.1f}".format(temperature['temp']) + "{0xDF}C " + "{0x01}" + "{}".format(w.humidity) + "% "  + "{0x03}" + "{}".format(w.clouds) + "%"
	screen[3] = "{0x02}" + "{:3.1f}".format(wind['speed']) + "m/s ^" + "{}".format(DegreeToDirection(wind['deg'])) + " {}".format(pressure['press']) + "hPa"
	screen[4] = "UV:{}".format(uvi.value) + " R:{}".format(uvi.get_exposure_risk())
	screen[5] = "{0xE0} " + sunrise.strftime("%H:%M") + "      {0xF4} " + sunset.strftime("%H:%M")
	screen[6] = now.strftime("%H:%M:%S  %d/%m/%Y")
	print("[INFO] Weather updated at {}".format(now.strftime("%H:%M:%S  %d/%m/%Y")))
	global DisplayedLine
	DisplayShift(screen, DisplayedLine)

def DegreeToDirection(degree):
	if(degree >= 0 and degree < 11.25):
		direction = "N"
	elif(degree > 11.25 and degree < 56.25):
		direction = "NE"
	elif(degree > 56.25 and degree < 101.25):
		direction = "E"
	elif(degree > 101.25 and degree < 146.25):
		direction = "SE"
	elif(degree > 146.25 and degree < 191.25):
		direction = "S"
	elif(degree > 191.25 and degree < 236.25):
		direction = "SW"
	elif(degree > 236.25 and degree < 281.25):
		direction = "W"
	elif(degree > 281.25 and degree < 326.25):
		direction = "NW"
	elif(degree > 326.25 and degree <= 360):
		direction = "N"
	return direction

def DisplayShift(screen, DisplayedLine):
	display.lcd_clear()
	display.lcd_display_extended_string(screen[DisplayedLine], 1)
	display.lcd_display_extended_string(screen[DisplayedLine + 1], 2)
	display.lcd_display_extended_string(screen[DisplayedLine + 2], 3)
	display.lcd_display_extended_string(screen[DisplayedLine + 3], 4)
	print("[DEBUG] Display has shifted!")

def DownButton(channel):
	global DisplayedLine
	if(DisplayedLine < len(screen) - 4):
		DisplayedLine += 1
		print("[DEBUG] Down button, displayed line: {}".format(DisplayedLine))
		DisplayShift(screen, DisplayedLine)

def UpButton(channel):
	global DisplayedLine
	if(DisplayedLine > 0):
		DisplayedLine -= 1
		print("[DEBUG] Up button, displayed line: {}".format(DisplayedLine))
		DisplayShift(screen, DisplayedLine)

GPIO.add_event_detect(20, GPIO.FALLING, callback=DownButton, bouncetime=400)
GPIO.add_event_detect(21, GPIO.FALLING, callback=UpButton, bouncetime=400)

counter = 0
DisplayedLine = 0

try:
	DisplayShift(screen , DisplayedLine)
	print("[INFO] Writing to display")
	while True:
		UpdateWeather()
		sleep(300)
except KeyboardInterrupt:
	# If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
	print("[INFO] Cleaning up!")
	display.lcd_clear()

except timeout:
	print("[DEBUG] API Timeout!")
	display.lcd_clear()
	display.lcd_display_string("Connection Error!" ,1)
	display.lcd_display_string("API Timeout!", 2)
	display.lcd_display_string("Retrying in 5s...", 3)
	sleep(5)

	print("[DEBUG] Retrying...")
	UpdateWeather()
