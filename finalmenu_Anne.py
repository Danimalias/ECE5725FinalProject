#Libraries Needed
import board
import neopixel
from time import sleep
import RPi.GPIO as GPIO
import time
import subprocess
import pygame,pigame
from pygame.locals import *
import sys
import os
import serial



######################### PiTFT Screen Setup Below ###########################

#Color Setup
WHITE = (255,255,255)
BLACK = (0, 0, 0)

#PiTFT Screen Initialization
os.putenv('SDL_VIDEODRV','fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV','dummy')
os.putenv('SDL_MOUSEDEV','/dev/null')
os.putenv('DISPLAY','')

#intialize the pygame 
pygame.init()
#connect pygame with the piTFT 
pitft = pigame.PiTft()

#set the display to size of the piTFT 
lcd = pygame.display.set_mode((320, 240))
lcd.fill((0,0,0))
#always need to update display after a change to have it show up 
pygame.display.update()

size = width, height = 320, 240 #size of window
screen = pygame.display.set_mode(size) #display screen size



######################### PiTFT Screen Menu Setup Below ###########################

font_big = pygame.font.Font(None, 50) #set font size to be big
font_medium = pygame.font.Font(None, 35) #set font size to be medium
font_small = pygame.font.Font(None, 25) #set font size to be small   

# set coordinates of where each image will be stationed
labels = {'Please Choose An Image' : (160, 25), 'Earth' : (40, 110), 'Soccer': (120, 110), 'Tennis' : (200, 110), 'Laugh' : (280, 110), 'Potato' : (40,210) , 'Cornell': (120, 210), 'Rpi' : (200,210), 'Alien' : (280,210)}

#Earth
earth = pygame.image.load("/home/pi/finalproj/menuimages/Earth.jpg").convert_alpha() #load the image and change scale
earth = pygame.transform.scale(earth, (40,40)) #further change the scale before getting the rectangle 
earthrect = earth.get_rect()
#Soccer
soccer = pygame.image.load("/home/pi/finalproj/menuimages/Soccer.jpg").convert_alpha() #load the image and change scale
soccer = pygame.transform.scale(soccer, (40,40)) #further change the scale before getting the rectangle 
soccerrect = soccer.get_rect()
#TennisBall
tennis = pygame.image.load("/home/pi/finalproj/menuimages/TennisBall.jpg").convert_alpha() #load the image and change scale
tennis = pygame.transform.scale(tennis, (40,40)) #further change the scale before getting the rectangle 
tennisrect = tennis.get_rect()
#Laugh-Emoji
laugh = pygame.image.load("/home/pi/finalproj/menuimages/Laugh.jpg").convert_alpha() #load the image and change scale
laugh = pygame.transform.scale(laugh, (40,40)) #further change the scale before getting the rectangle 
laughrect = laugh.get_rect()
#Moon
potato = pygame.image.load("/home/pi/finalproj/menuimages/Potato.jpg").convert_alpha() #load the image and change scale
potato = pygame.transform.scale(potato, (40,40)) #further change the scale before getting the rectangle 
potatorect = potato.get_rect()
#Cornell
cornell = pygame.image.load("/home/pi/finalproj/menuimages/Cornell.jpg").convert_alpha() #load the image and change scale
cornell = pygame.transform.scale(cornell, (40,40)) #further change the scale before getting the rectangle 
cornellrect = cornell.get_rect()
#Rpi
rpi = pygame.image.load("/home/pi/finalproj/menuimages/Rpi.png").convert_alpha() #load the image and change scale
rpi = pygame.transform.scale(rpi, (40,40)) #further change the scale before getting the rectangle 
rpirect = rpi.get_rect()
#Toy
toy = pygame.image.load("/home/pi/finalproj/menuimages/Alien.jpg").convert_alpha() #load the image and change scale
toy = pygame.transform.scale(toy, (40,40)) #further change the scale before getting the rectangle 
toyrect = toy.get_rect()

#update the screen 
pygame.display.update()



######################### GPIO Pin/Button and Boolean Variables Setup Below ###########################

#bailout button 
def GPIO27_callback(channel):
    global code_run
    code_run = False

GPIO.setwarnings(False) #disables warnings
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set quit button as an GPIO input
GPIO.add_event_detect(27, GPIO.FALLING, callback=GPIO27_callback, bouncetime = 300)
time_limit = 600 #timer limit
fps= 24 #frame rate of the screen
my_clock = pygame.time.Clock()
starttime = time.time()
code_run = True

#image boolean values
earthrun = False
soccerrun = False
tennisrun = False
laughrun = False
potatorun = False
cornellrun = False
rpirun = False
toyrun = False


################################### Main Loop Below ###################################

try:
    while code_run:
        #UART initialization
        #/dev/ttyUSB0 the USB(top right) serial connection 
        ser = serial.Serial('/dev/ttyUSB0', 9600, timeout =1) #9600 baud rate of ESP32
        ser.reset_input_buffer() #resets serial buffer, helps flushes out noise and previous messages
        
        now = time.time() #keeps track of time
        elapsed_time = now-starttime
        if (elapsed_time > time_limit):
            code_run = False
        time.sleep(0.2)
        pitft.update() #update the screen 

        for event in pygame.event.get(): #event polling
            if(event.type is MOUSEBUTTONDOWN):
                x,y = pygame.mouse.get_pos()
                #print(x,y)
            elif(event.type is MOUSEBUTTONUP):
                x,y = pygame.mouse.get_pos()
                if y > 50 and y < 90 and x > 20 and x < 60: #Earth image pressed
                    print("Earth")
                    earthrun = True
                    soccerrun = False
                    tennisrun = False
                    laughrun = False
                    potatorun = False
                    cornellrun = False
                    rpirun = False
                    toyrun = False
                    string = "earth" + "\n" #"\n" indicates line separation
                    string = string.encode('utf_8') #UART encoder, the default
                    ser.write(string) #sending to ESP32 via UART
                    line = ser.readline().decode('utf_8').rstrip() #strips recieved message
                    print("received: ", line)
                elif y > 50 and y < 90 and x > 100 and x < 140:#Soccer ball image pressed
                    print("Soccer") 
                    earthrun = False
                    soccerrun = True
                    tennisrun = False
                    laughrun = False
                    potatorun = False
                    cornellrun = False
                    rpirun = False
                    toyrun = False
                    string = "soccer" + "\n" #"\n" indicates line separation
                    string = string.encode('utf_8')#UART encoder, the default
                    ser.write(string) #sending to ESP32 via UART
                    line = ser.readline().decode('utf_8').rstrip() #strips recieved message
                    print("received: ", line)
                elif y > 50 and y < 90 and x > 180 and x < 220: #Tennis Ball image pressed
                    print("Tennis Ball")
                    earthrun = False
                    soccerrun = False
                    tennisrun = True
                    laughrun = False
                    potatorun = False
                    cornellrun = False
                    rpirun = False
                    toyrun = False
                    string = "tennis ball" + "\n" #"\n" indicates line separation
                    string = string.encode('utf_8')#UART encoder, the default
                    ser.write(string) #sending to ESP32 via UART
                    line = ser.readline().decode('utf_8').rstrip() #strips recieved message
                    print("received: ", line)
                elif y > 50 and y < 90 and x > 260 and x < 300: #Laughing emoji image pressed
                    print("Laughing") 
                    earthrun = False
                    soccerrun = False
                    tennisrun = False
                    laughrun = True
                    potatorun = False
                    cornellrun = False
                    rpirun = False
                    toyrun = False
                    string = "laughing" + "\n" #"\n" indicates line separation
                    string = string.encode('utf_8')#UART encoder, the default
                    ser.write(string) #sending to ESP32 via UART
                    line = ser.readline().decode('utf_8').rstrip() #strips recieved message
                    print("received: ", line)
                elif y > 150 and y < 190 and x > 20 and x < 60: #Mr.Potato Head image pressed
                    print("Potato")
                    earthrun = False
                    soccerrun = False
                    tennisrun = False
                    laughrun = False
                    potatorun = True
                    cornellrun = False
                    rpirun = False
                    toyrun = False
                    string = "potato" + "\n" #"\n" indicates line separation
                    string = string.encode('utf_8')#UART encoder, the default
                    ser.write(string) #sending to ESP32 via UART
                    line = ser.readline().decode('utf_8').rstrip() #strips recieved message
                    print("received: ", line)
                elif y > 150 and y < 190 and x > 100 and x < 140: #Cornell Logo image pressed
                    print("Cornell")
                    earthrun = False
                    soccerrun = False
                    tennisrun = False
                    laughrun = False
                    potatorun = False
                    cornellrun = True
                    rpirun = False
                    toyrun = False
                    string = "cornell" + "\n" #"\n" indicates line separation
                    string = string.encode('utf_8')#UART encoder, the default
                    ser.write(string) #sending to ESP32 via UART
                    line = ser.readline().decode('utf_8').rstrip() #strips recieved message
                    print("received: ", line)
                elif y > 150 and y < 190 and x > 180 and x < 220: #Rpi image pressed
                    print("Rpi")
                    earthrun = False
                    soccerrun = False
                    tennisrun = False
                    laughrun = False
                    potatorun = False
                    cornellrun = False
                    rpirun = True
                    toyrun = False
                    string = "rpi" + "\n" #"\n" indicates line separation
                    string = string.encode('utf_8')#UART encoder, the default
                    ser.write(string) #sending to ESP32 via UART
                    line = ser.readline().decode('utf_8').rstrip() #strips recieved message
                    print("received: ", line)
                elif y > 150 and y < 190 and x > 260 and x < 300: #Alien image pressed
                    print("Alien")
                    earthrun = False
                    soccerrun = False
                    tennisrun = False
                    laughrun = False
                    potatorun = False
                    cornellrun = False
                    rpirun = False
                    toyrun = True
                    string = "toy" + "\n" #"\n" indicates line separation
                    string = string.encode('utf_8')#UART encoder, the default
                    ser.write(string) #sending to ESP32 via UART
                    line = ser.readline().decode('utf_8').rstrip() #strips recieved message
                    print("received: ", line)

        #Combine picture surface with workspace surface
        screen.blit(earth, (20,50)) #Earth
        screen.blit(soccer,(100,50)) #soccer
        screen.blit(tennis, (180,50)) #Tennis Ball
        screen.blit(laugh, (260,50)) #Laughing Emoji
        screen.blit(potato, (20,150)) #potato
        screen.blit(cornell, (100,150)) #Death Star
        screen.blit(rpi, (180,150)) #rpi
        screen.blit(toy, (260,150)) #alien
        for k,v in labels.items():
            text_surface = font_small.render('%s'%k, True, WHITE)
            rect = text_surface.get_rect(center=v)
            lcd.blit(text_surface, rect) # need to combine the workspace
        pygame.display.flip()  #Display workspace on screen
    

except KeyboardInterrupt:
    pass
finally:
    del(pitft)
        
        
        

