#!/usr/bin/env python
import rospy
import time

import qwiic
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

from std_msgs.msg import String


def get_ip_address(interface):
    if get_network_interface_state(interface) == 'down':
        return None
    cmd = "ifconfig %s | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'" % interface
    return subprocess.check_output(cmd, shell=True).decode('ascii')[:-1]


def get_network_interface_state(interface):
    return subprocess.check_output('cat /sys/class/net/%s/operstate' % interface, shell=True).decode('ascii')[:-1]


user_text=None

def on_user_text(msg):
	global user_text	
	user_text=msg.data

	rospy.loginfo(rospy.get_caller_id() + ' user_text=%s', msg.data)


# initialization
if __name__ == '__main__':

	# Scan for devices on I2C bus
	addresses = qwiic.scan()

	# Initialize Display-----------------------------------------------------------
	# Try to connect to the OLED display module via I2C.

	# 128x32 display (default)---------------------------------------------
	if 60 in addresses:
		disp1 = Adafruit_SSD1306.SSD1306_128_32(rst=None, i2c_bus=1, gpio=1) # setting gpio to 1 is hack to avoid platform detection
		try:
			# Initiallize Display
			disp1.begin()

			# Clear display.
			disp1.clear()
			disp1.display()

			# Create blank image for drawing.
			# Make sure to create image with mode '1' for 1-bit color.
			width = disp1.width
			height = disp1.height
			image = Image.new('1', (width, height))

			# Get drawing object to draw on image.
			draw = ImageDraw.Draw(image)

			# Draw a black filled box to clear the image.
			draw.rectangle((0,0,width,height), outline=0, fill=0)

			# Draw some shapes.
			# First define some constants to allow easy resizing of shapes.
			padding = -2
			top = padding
			bottom = height-padding
			# Move left to right keeping track of the current x position for drawing shapes.
			x = 0

			# Load default font.
			font = ImageFont.load_default()

			# Draw a black filled box to clear the image.
			draw.rectangle((0,0,width,height), outline=0, fill=0)
		except OSError as err:
			print("OS error: {0}".format(err))
			
			# Update ROS
			rospy.rostime.wallsleep(1.0) # Pause 1 sec

	# 48 x 64 display------------------------------------------------------
	elif 61 in addresses:
		disp2 = qwiic.QwiicMicroOled()
		try:
			# Initiallize Display
			disp2.begin()

			# Display Flame (set to buffer in begin function)
			disp2.display()

			# Update ROS
			rospy.rostime.wallsleep(5.0) # Pause 5 sec

			# Clear Display
			disp2.clear(disp2.PAGE)
			disp2.clear(disp2.ALL)

			# Set Font
			disp2.set_font_type(0)
			# Could replace line spacing with disp2.getFontHeight, but doesn't scale properly

			# Screen Width
			import qwiic_micro_oled
			LCDWIDTH = qwiic_micro_oled._LCDWIDTH
		except OSError as err:
			print("OS error: {0}".format(err))
			
			# Update ROS
			rospy.rostime.wallsleep(1.0) # Pause 1 sec


	# setup ros node
	rospy.init_node('jetbot_oled')
	rospy.Subscriber('~user_text', String, on_user_text)

	# start running
	while not rospy.core.is_shutdown():

		# # Scan for devices on I2C bus
		# addresses = qwiic.scan()

		# Check Eth0, Wlan0, and Wlan1 Connections---------------------------------
		a = 0    # Indexing of Connections

		# Checks for Ethernet Connection
		try:
			eth = get_ip_address('eth0')
			if eth != None:
				a = a + 1
		except Exception as e:
			print(e)

		# Checks for WiFi Connection on wlan0
		try:
			wlan0 = get_ip_address('wlan0')
			if wlan0 != None:
				a = a + 2
		except Exception as e:
				print(e)

		# Checks for WiFi Connection on wlan1
		try:
			wlan1 = get_ip_address('wlan1')
			if wlan1 != None:
				a = a + 4
		except Exception as e:
			print(e)

		# Check Resource Usage-----------------------------------------------------
		# Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-$
			
		# CPU Load
		cmd = "top -bn1 | grep load | awk '{printf \"%.1f%%\", $(NF-2)}'"
		CPU = subprocess.check_output(cmd, shell = True )
		
		# Memory Use
		cmd = "free -m | awk 'NR==2{printf \"%.1f%%\", $3*100/$2}'"
		Mem_percent = subprocess.check_output(cmd, shell = True )
		cmd = "free -m | awk 'NR==2{printf \"%.2f/%.1f\", $3/1024,$2/1024}'"
		MemUsage = subprocess.check_output(cmd, shell = True )
		
		# Disk Storage
		cmd = "df -h | awk '$NF==\"/\"{printf \"%s\", $5}'"
		Disk_percent = subprocess.check_output(cmd, shell = True )
		cmd = "df -h | awk '$NF==\"/\"{printf \"%d/%d\", $3,$2}'"
		DiskUsage = subprocess.check_output(cmd, shell = True )


		try:
			# 128x32 display (default)-------------------------------------------------
			if 60 in addresses:
				
				# Draw a black filled box to clear the image.
				draw.rectangle((0,0,width,height), outline=0, fill=0)

				# Write two lines of text.
				if not user_text is None:
					draw.text((x, top), user_text,  font=font, fill=255)

					if len(user_text) > 21:
						print("Error: User text exceeds 21 character limitation")

				# Display IP address
				elif a == 1:
					draw.text((x, top),       "eth0: " + str(eth),  font=font, fill=255)
				elif a == 3:
					draw.text((x, top),       "eth0: " + str(eth),  font=font, fill=255)
				elif a == 5:
					draw.text((x, top),       "eth0: " + str(eth),  font=font, fill=255)
				elif a == 0:
					draw.text((x, top),       "No Connection!",  font=font, fill=255)

				if a == 2:
					draw.text((x, top+8),     "wlan0: " + str(wlan0), font=font, fill=255)
				elif a == 3:
					draw.text((x, top+8),     "wlan0: " + str(wlan0), font=font, fill=255)
				elif a == 4:
					draw.text((x, top+8),     "wlan1: " + str(wlan1), font=font, fill=255)
				elif a == 5:
					draw.text((x, top+8),     "wlan1: " + str(wlan1), font=font, fill=255)
				else:
					draw.text((x, top),       "No Connection!",  font=font, fill=255)

				# Resource Usage
				draw.text((x, top+16),    "Mem: " + str(MemUsage.decode('utf-8')) + "GB",  font=font, fill=255)
				draw.text((x, top+25),    "Disk: " + str(DiskUsage.decode('utf-8')) + "GB",  font=font, fill=255)

				# Display image.
				disp.image(image)
				disp.display()
				
				# Update ROS
				rospy.rostime.wallsleep(1.0)

			# 48 x 64 display----------------------------------------------------------
			elif 61 in addresses:
				# Text Spacing (places text on right edge of display)----------------------
				b = 0
				c = 0

				if eth != None:
					#Check String Length
					if len(eth) > 10:
						# Find '.' to loop numerals
						while b != -1:
							x1 = LCDWIDTH - disp2._font.width * (len(eth) - b)
							i = b + 1
							b = eth.find('.', i)

				if wlan0 != None:
					#Check String Length
					if len(wlan0) > 10:
						# Find '.' to loop numerals
						while c != -1:
							x2 = LCDWIDTH - disp2._font.width * (len(wlan0) - c)
							j = c + 1
							c = wlan0.find('.', j)

				if wlan1 != None:
					#Check String Length
					if len(wlan1) > 10:
						# Find '.' to loop numerals
						while c != -1:
							x2 = LCDWIDTH - disp2._font.width * (len(wlan1) - c)
							j = c + 1
							c = wlan1.find('.', j)

				x3 = LCDWIDTH - (disp2._font.width + 1) * (len(str(CPU.decode('utf-8'))))
				x4 = LCDWIDTH - (disp2._font.width + 1) * (len(str(Mem_percent.decode('utf-8'))))
				x5 = LCDWIDTH - (disp2._font.width + 1) * (len(str(Disk_percent.decode('utf-8'))))
				x6 = LCDWIDTH - (disp2._font.width + 1) * (len(str(MemUsage.decode('utf-8')) + "GB"))
				x7 = LCDWIDTH - (disp2._font.width + 1) * (len(str(DiskUsage.decode('utf-8')) + "GB"))

				# Displays IP Address (if available)---------------------------------------
				
				# Clear Display
				disp2.clear(disp2.PAGE)
				disp2.clear(disp2.ALL)
				
				#Set Cursor at Origin
				disp2.set_cursor(0,0)

				# Text Line----------------------------------------------------------------
				d = 0

				# Write user text.
				if not user_text is None and len(user_text) <= 10:
					d = 8

					disp2.print(user_text)
			
					#Set Cursor at Origin
					disp2.set_cursor(0, d)

				
				# Prints IP Address on OLED Display
				if a == 1:
					disp2.print("eth0:")
					disp2.set_cursor(0,8 + d)
					if b != 0:
						disp2.print(str(eth[0:i]))
						disp2.set_cursor(x1,16 + d)
						disp2.print(str(eth[i::]))
					else:
						disp2.print(str(eth))
					
				elif a == 2:
					disp2.print("wlan0: ")
					disp2.set_cursor(0,8 + d)
					if c != 0:
						disp2.print(str(wlan0[0:j]))
						disp2.set_cursor(x2,16 + d)
						disp2.print(str(wlan0[j::]))
					else:
						disp2.print(str(wlan0))
					
				elif a == 3:
					disp2.print("eth0:")
					disp2.set_cursor(0,8 + d)
					if b != 0:
						disp2.print(str(eth[0:i]))
						disp2.set_cursor(x1,16 + d)
						disp2.print(str(eth[i::]))
					else:
						disp2.print(str(eth))
					
					disp2.set_cursor(0,24 + d)
					disp2.print("wlan0: ")
					disp2.set_cursor(0,32 + d)
					if c != 0:
						disp2.print(str(wlan0[0:j]))
						disp2.set_cursor(x2,40 + d)
						disp2.print(str(wlan0[j::]))
					else:
						disp2.print(str(wlan0))

				elif a == 4:
					disp2.print("wlan1: ")
					disp2.set_cursor(0,8 + d)
					if c != 0:
						disp2.print(str(wlan1[0:j]))
						disp2.set_cursor(x2,16 + d)
						disp2.print(str(wlan1[j::]))
					else:
						disp2.print(str(wlan1))

				elif a == 5:
					disp2.print("eth0:")
					disp2.set_cursor(0,8 + d)
					if b != 0:
						disp2.print(str(eth[0:i]))
						disp2.set_cursor(x1,16 + d)
						disp2.print(str(eth[i::]))
					else:
						disp2.print(str(eth))
					
					disp2.set_cursor(0,24 + d)
					disp2.print("wlan1: ")
					disp2.set_cursor(0,32 + d)
					if c != 0:
						disp2.print(str(wlan1[0:j]))
						disp2.set_cursor(x2,40 + d)
						disp2.print(str(wlan1[j::]))
					else:
						disp2.print(str(wlan1))

				else:
					disp2.set_cursor(0,d)
					disp2.print("No Connection!")
				
				disp2.display()

				# Update ROS
				rospy.rostime.wallsleep(10.0) # Pause 10 sec

				# Displays Resource Usage-------------------------------------------
				# ------------------------------------------------------------------

				# Percentage--------------------------------------------------------
				# Clear Display
				disp2.clear(disp2.PAGE)
				disp2.clear(disp2.ALL)

				#Set Cursor at Origin
				disp2.set_cursor(0,0)

				# Write user text.
				if d == 8:
					disp2.print(user_text)
			
					#Set Cursor at Origin
					disp2.set_cursor(0, d)

				# Prints Percentage Use on OLED Display
				disp2.set_cursor(0,0 + d)	# Set Cursor at Origin
				disp2.print("CPU:")
				disp2.set_cursor(0,10 + d)
				disp2.print("Mem:")
				disp2.set_cursor(0,20 + d)	
				disp2.print("Disk:")

				disp2.set_cursor(x3,0 + d)
				disp2.print(str(CPU.decode('utf-8')))
				disp2.set_cursor(x4,10 + d)
				disp2.print(str(Mem_percent.decode('utf-8')))
				disp2.set_cursor(x5,20 + d)	
				disp2.print(str(Disk_percent.decode('utf-8')))
				
				disp2.display()

				# Update ROS
				rospy.rostime.wallsleep(7.5) # Pause 7.5 sec
				
				
				# Size--------------------------------------------------------------
				# Clear Display
				disp2.clear(disp2.PAGE)
				disp2.clear(disp2.ALL)

				#Set Cursor at Origin
				disp2.set_cursor(0,0)

				# Write user text.
				if d == 8:
					disp2.print(user_text)
			
					#Set Cursor at Origin
					disp2.set_cursor(0, d)
				
				# Prints Capacity Use on OLED Display
				disp2.set_cursor(0,0 + d)	# Set Cursor at Origin
				disp2.print("Mem:")
				disp2.set_cursor(x6,10 + d)
				disp2.print(str(MemUsage.decode('utf-8')) + "GB")
				disp2.set_cursor(0,20 + d)
				disp2.print("Disk:")
				disp2.set_cursor(x7,30 + d)
				disp2.print(str(DiskUsage.decode('utf-8')) + "GB")
				
				disp2.display()
				
				# Update ROS
				rospy.rostime.wallsleep(7.5) # Pause 7.5 sec


				# Clear Display
				disp2.clear(disp2.PAGE)
				disp2.clear(disp2.ALL)

				#Set Cursor at Origin
				disp2.set_cursor(0,0)

				# User Text---------------------------------------------------------
				if not user_text is None and 10 < len(user_text) <= 60:
					# Write user text.
					disp2.print(user_text)

					# Display image.
					disp2.display()
					
					# Update ROS
					rospy.rostime.wallsleep(10.0)

				elif not user_text is None and len(user_text) > 60:
					# Display Error Message
					disp2.print("Error:    User text exceeds 60character limitation")
					print("Error: User text exceeds 60 character limitation")

					# Display image.
					disp2.display()
					
					# Update ROS
					rospy.rostime.wallsleep(10.0)

			else:
				break
			
		except OSError as err:
			print("OS error: {0}".format(err))
			
			# Update ROS
			rospy.rostime.wallsleep(5.0) # Pause 5 sec
			break
		except:
			break