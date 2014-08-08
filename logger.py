#!/usr/bin/env python

#imports
import time
import subprocess
import MySQLdb
import RPi.GPIO as GPIO
import os
from ConfigParser import SafeConfigParser

def main():

	#Set up gpio pins for leds and light sensor
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	#Green led
	GPIO.setup(25,GPIO.OUT)
	#Red led
	GPIO.setup(22,GPIO.OUT)
	#light sensor
	GPIO.setup(18,GPIO.OUT)
	
	#Initialize SafeConfigParser
	parser = SafeConfigParser()

	#Read config.ini
	parser.read('config.ini')

	dbHost = parser.get('mysql', 'dbHost')
	dbUser = parser.get('mysql', 'dbUser')
	dbPass = parser.get('mysql', 'dbpass')
	dbName = parser.get('mysql', 'dbname')

	#set up mysql connection string
	db = MySQLdb.connect(host=dbHost,user=dbUser,passwd=dbPass,db=dbName)

	#Load drivers for 1wire sensor
	try:
		w1_devices = os.listdir("/sys/bus/w1/devices/")
	except:
		output_mp1 = subprocess.Popen('sudo modprobe w1-gpio', shell=True, stdout=subprocess.PIPE)
		time.sleep(5)
		w1_devices = os.listdir("/sys/bus/w1/devices/")

	#Check to see if devices have been initialized 
	no_of_devices = len(w1_devices) -1

	if no_of_devices < 1:
		sys.exit()

	#define functions
	def read_temp(device):
		DS18b20 = open(device)
		text = DS18b20.read()
		DS18b20.close()

		# Split the text with new lines (\n) and select the second line.
		secondline = text.split("\n")[1]
		# Split the line into words, referring to the spaces, and select the 10th wo$
		temperaturedata = secondline.split(" ")[9]
		# The first two characters are "t=", so get rid of those and convert the tem$
		temperature = float(temperaturedata[2:])
		# Put the decimal point in the right place and display it.
		temperature = temperature / 1000
		return temperature

	#Set path to temp sensor
	tempSensor = "/sys/bus/w1/devices/28-0000052c98b1/w1_slave"

	#Get values here
	temperature = "%.2f" % (read_temp(tempSensor))

	#Temp value to float for logic below
	tmp = float(temperature)

	#Logic to control LEDs
	if tmp < 20:
		GPIO.output(22,1)
		GPIO.output(25,0)
	else:
		GPIO.output(22,0)
		GPIO.output(25,1)

	#DB stuff
	cursor = db.cursor()

	try:
		cursor.execute("""INSERT INTO L_Temp_Light (temperature)
	        	        VALUES(%s)""",(temperature))
		db.commit()
	except Exception,e:
	        #print("There was an error when attempting the insert: " + str(e))
	        db.rollback()

	#Cleanup GPIO
	#GPIO.cleanup()

if __name__ == "__main__":
    main()
