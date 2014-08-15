#!/usr/bin/env python

#imports
import time
import subprocess
import MySQLdb
import RPi.GPIO as GPIO
import os
import logging
from ConfigParser import SafeConfigParser

def main():
	#Read config.ini
	parser = SafeConfigParser()
	
	#This must be the full path config.ini
	parser.read('/home/pi/projects/piTemperatureLogger/config.ini')
	
	logFile = parser.get('defaults', 'logFile')	
	tempSensor0 = parser.get('hardware', 'tempSensor0')	
	tempSensor0_loc = parser.get('location', 'tempSensor0_loc')	
	dbON = parser.get('mysql', 'dbON')
	dbHost = parser.get('mysql', 'dbHost')
	dbUser = parser.get('mysql', 'dbUser')
	dbPass = parser.get('mysql', 'dbPass')
	dbName = parser.get('mysql', 'dbName')
	dbTable = parser.get('mysql', 'dbTable')	
	
	#Configure logger
	logger = logging.getLogger("piTemperatureLogger")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(logFile)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

	logger.info("Initializing GPIO pins")

	#Set up gpio pins for leds and light sensor
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)

	#Green led
	GPIO.setup(25,GPIO.OUT)
	#Red led
	GPIO.setup(22,GPIO.OUT)
	
	#Initialize SafeConfigParser
	logger.info("Initializing SafeConfigParser")

	#Load drivers for 1wire sensor
	logger.info("Loading drivers for 1wire sensor")

	try:
		w1_devices = os.listdir("/sys/bus/w1/devices/")
	except:
		logger.warn("Driver not loaded.. executing modprobe w1-gpio")

		subprocess.Popen('modprobe w1-gpio', shell=True, stdout=subprocess.PIPE)
		time.sleep(5)
		w1_devices = os.listdir("/sys/bus/w1/devices/")

	#Check to see if devices have been initialized 
	no_of_devices = len(w1_devices) -1

	if no_of_devices < 1:
		logger.error("Could not load 1wire sensor")

		sys.exit()

	#Get values here
	temperature = read_temp(tempSensor0)

	#Logic to control LEDs
	if temperature < 20:
		logger.info("Red LED = TRUE")
		GPIO.output(22,1)
		GPIO.output(25,0)
	else:
		logger.info("Green LED = TRUE")
		GPIO.output(22,0)
		GPIO.output(25,1)
			
	if dbON == "true":
		logger.info("dbON = TRUE")

		#set up mysql connection string
		db = MySQLdb.connect(host=dbHost,user=dbUser,passwd=dbPass,db=dbName)
		cursor = db.cursor()

		try:
			logger.info("INSERT: " + str(tempSensor0_loc) + " " + str(temperature))
			
			cursor.execute("""INSERT INTO tempData
	        	        VALUES(CURRENT_DATE(), NOW(), %s, %s)""",(tempSensor0_loc,temperature))
			
			db.commit()
		except Exception,e:
			logger.error("There was an error when attempting the insert: " + str(e))		        
		        db.rollback()
	else:
		print(temperature)

	#Cleanup GPIO
	#GPIO.cleanup()

def read_temp(device):
	DS18b20 = open(device)
	text = DS18b20.read()
	DS18b20.close()

	crc = text.split("\n")[0][-3:]

	if crc=="YES":
		rawData = text.split("\n")[1][-5:]
		temperature = float(rawData) / 1000
		return temperature
	else:
		return None

if __name__ == "__main__":
    main()
