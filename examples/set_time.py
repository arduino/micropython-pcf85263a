"""
This script connects to a Wi-Fi network, synchronizes the system time 
using NTP, and then sets the PCF85263A RTC module to the current time.

Initial author: Sebastian Romero (s.romero@arduino.cc)
Copyright (C) Arduino s.r.l. and/or its affiliated companies
"""

from time import sleep, localtime
from ntptime import settime
import network
from machine import I2C
from pcf85263a import PCF85263A

WIFI_SSID = "" # Adjust for your network
WIFI_PASSWORD = "" # Adjust for your network

def connect_wifi(wifi, ssid, password):
	"""
	Connect to Wi-Fi network using provided SSID and password.

	Parameters:
		wifi (network.WLAN): The WLAN interface to use for the connection.
		ssid (str): The SSID of the Wi-Fi network to connect to.
		password (str): The password for the Wi-Fi network.
	"""		
	if not wifi.isconnected():
		print('Connecting to network...')
		wifi.active(True)
		wifi.connect(ssid, password)
		while not wifi.isconnected():			
			sleep(1)		
	print('Network config:', wifi.ifconfig()) 

wifi = network.WLAN(network.STA_IF)

if not wifi.isconnected():	
	# Ask user to enter Wi-Fi credentials if not set
	if not WIFI_SSID:
		WIFI_SSID = input("Enter Wi-Fi SSID: ")
	if not WIFI_PASSWORD:
		WIFI_PASSWORD = input("Enter Wi-Fi Password: ")
	connect_wifi(wifi, WIFI_SSID, WIFI_PASSWORD)

settime() # Update RTC from NTP server (requires Internet connection)

bus = I2C(0) # Initialize I2C bus (adjust parameters if needed for your hardware)
rtc = PCF85263A(bus)

rtc.datetime = localtime() # Set RTC to current time (UTC)
t = rtc.datetime # Read back time from RTC
print(f"RTC set to: {t[0]:04d}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}")