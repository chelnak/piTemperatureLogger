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
	
	#Initialize SafeConfigParser
	parser = SafeConfigParser()

	#Read config.ini
	parser.read('config.ini')

	tempSensor0 = parser.get('hardware', 'tempSensor0')	
	tempSensor0_loc = parser.get('location', 'tempSensor0_loc')	

	dbON = parser.get('mysql', 'dbON')
	dbHost = parser.get('mysql', 'dbHost')
	dbUser = parser.get('mysql', 'dbUser')
	dbPass = parser.get('mysql', 'dbpass')
	dbName = parser.get('mysql', 'dbname')


	#Load drivers for 1wire sensor
	try:
		w1_devices = os.listdir("/sys/bus/w1/devices/")
	except:
		subprocess.Popen('modprobe w1-gpio', shell=True, stdout=subprocess.PIPE)
		time.sleep(5)
		w1_devices = os.listdir("/sys/bus/w1/devices/")

	#Check to see if devices have been initialized 
	no_of_devices = len(w1_devices) -1

	if no_of_devices < 1:
		sys.exit()

	#Get values here
	temperature = read_temp(tempSensor0)

	#Logic to control LEDs
	if temperature < 20:
		GPIO.output(22,1)
		GPIO.output(25,0)
	else:
		GPIO.output(22,0)
		GPIO.output(25,1)
			
	if dbON == "true":
		#set up mysql connection string
		db = MySQLdb.connect(host=dbHost,user=dbUser,passwd=dbPass,db=dbName)
		cursor = db.cursor()

		try:
			cursor.execute("""INSERT INTO tempData
	        	        VALUES(CURRENT_DATE(), NOW(), %s, %s)""",(tempSensor0_loc,temperature))
			db.commit()
		except Exception,e:
		        #print("There was an error when attempting the insert: " + str(e))
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
