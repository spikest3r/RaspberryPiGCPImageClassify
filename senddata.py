from picamera2 import Picamera2
import io
import base64
import time
import requests
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image,ImageDraw,ImageFont
import RPi.GPIO as GPIO

BUTTON_PIN=17
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN,pull_up_down=GPIO.PUD_UP)

serial=i2c(port=1,address=0x3C)
device=ssd1306(serial,width=128,height=64)

imagepil = None
draw = None

def screeninit():
	global imagepil, draw
	imagepil = Image.new('1',(device.width,device.height))
	draw = ImageDraw.Draw(imagepil)

screeninit()
draw.text((0,0),"Initializing...",fill=255)
device.display(imagepil)

url = 'https://esp-classify-294872898597.europe-west1.run.app/classify'

picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())

def click():
	screeninit()
	draw.text((0,0),"Capturing...",fill=255)
	device.display(imagepil)
	picam2.start()
	time.sleep(2)
	screeninit()
	draw.text((0,0),"Processing...",fill=255)
	device.display(imagepil)
	image = picam2.capture_array()
	
	image = Image.fromarray(image) # flip not required!
	image = image.convert("RGB")
	buffer = io.BytesIO()
	image.save(buffer,format="JPEG")
	jpg_bytes = buffer.getvalue()
	
	jpg_base64 = base64.b64encode(jpg_bytes).decode("utf-8")
	
	data = {
		"image": jpg_base64
	}
	
	response = requests.post(url, json=data)
	print(response.text)
	
	json_response = response.json()
	#first_label = data["labels"][0]["description"]
	screeninit()
	for x in range(len(json_response["labels"])):
		draw.text((0,16+x*8),json_response["labels"][x]["description"], fill=255)
	
	device.display(imagepil)


screeninit()
draw.text((0,0),"Awaiting key...",fill=255)
device.display(imagepil)

try:
	while True:
		if GPIO.input(BUTTON_PIN) == 0:
			click()
except KeyboardInterrupt:
	pass
finally:
	GPIO.cleanup()
	device.clear()

input() # wait
