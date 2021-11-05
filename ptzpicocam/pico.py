import camera
from machine import Pin, Timer, ADC
import time
from enum import IntEnum

global flag_read_pos_JoyStick

global posX
global posY
global posZ

ana_potar = 28
ana_vert = 27
ana_hor = 26

joyX_pin = ADC(Pin(ana_hor))
joyY_pin = ADC(Pin(ana_vert))
poten_pin = ADC(Pin(ana_potar))

timer_ana = Timer()

flag_read_pos_JoyStick = False

global nPalierX
global nPalierY
global nPalierZ

posX = 0
posY = 0
posZ = 0

minX = 0
maxX = 65535
minY = 0
maxY = 65535
minZ = 0
maxZ = 65535

nPalierX = 47
nPalierY = 45
nPalierZ = 15

# Build threshold list
# Threshold list for Z
global thres_Z
thres_Z = []
thres_Z.append(minZ)
for i in range(1, nPalierZ):
    thres_Z.append(int(i / nPalierZ * (maxZ - minZ) + minZ))
thres_Z.append(maxZ)

# Threshold list for Y
global thres_Y
thres_Y = []  # Thres Tilt
thres_Y.append(minY)
for i in range(1, nPalierY):
    thres_Y.append(int(i / nPalierY * (maxY - minY) + minY))
thres_Y.append(maxY)

# Threshold list for X
global thres_X
thres_X = []  # Thres Pan
thres_X.append(minX)
for i in range(1, nPalierX):
    thres_X.append(int(i / nPalierX * (maxX - minX) + minX))
thres_X.append(maxX)


def timer_read_ana(timer_ana):
    global posY
    global posX
    global posZ
    global flag_read_pos_JoyStick

    posX = joyX_pin.read_u16()
    posY = joyY_pin.read_u16()
    posZ = poten_pin.read_u16()
    flag_read_pos_JoyStick = True

timer_ana.init(freq=5, mode=Timer.PERIODIC, callback=timer_read_ana)

def calc_Pan_Com(positionX):
    if thres_X[int(nPalierX / 2)] <= positionX and positionX <= thres_X[int(nPalierX / 2) + 1]:
        # No move X
        dirX = camera.CameraAPI.PanDirection(1)
        speedX = 0
    else:
        # Set Speed X
        if positionX <= thres_X[int(nPalierX / 2)]:
            # Right Mvt
            dirX = camera.CameraAPI.PanDirection(2)
            r = 0
            for i in range(0, int(nPalierX / 2) + 1):
                if positionX <= thres_X[i]:
                    r = i
                    break
            speedX = int(nPalierX / 2) + 1 - r
        else:
            # Left Mvt
            dirX = camera.CameraAPI.PanDirection(1)
            r = nPalierX + 1
            for i in range(int(nPalierX / 2) + 2, nPalierX + 1):
                if positionX < thres_X[i]:
                    print("break")
                    r = i
                    break
            speedX = r - int(nPalierX / 2) - 1
    # print("Dir X ",dirX,"  Speed X ",speedX)
    return dirX, speedX

def calc_Tilt_Com(positionY):
    if thres_Y[int(nPalierY / 2)] <= positionY and positionY <= thres_Y[int(nPalierY / 2) + 1]:
        # No move Y
        dirY = camera.CameraAPI.TiltDirection(1)
        speedY = 0
    else:
        # Set Speed Y
        if positionY <= thres_Y[int(nPalierY / 2)]:
            # Down Mvt
            dirY = camera.CameraAPI.TiltDirection(2)
            r = 0
            for i in range(0, int(nPalierY / 2) + 1):
                if positionY <= thres_Y[i]:
                    r = i
                    break
            speedY = int(nPalierY / 2) + 1 - r
        else:
            # Uo Mvt
            dirY = camera.CameraAPI.TiltDirection(1)
            r = nPalierY + 1
            for i in range(int(nPalierY / 2) + 2, nPalierY + 1):
                if positionY < thres_Y[i]:
                    r = i
                    break
            speedY = r - int(nPalierY / 2) - 1
    # print("Dir  Y ",dirY,"  Speed Y ",speedY)
    return dirY, speedY

def calc_Zoom_Com(positionVal):
    if thres_Z[int(nPalierZ / 2)] <= positionVal and positionVal <= thres_Z[int(nPalierZ / 2) + 1]:
        # Stop Zoom
        camera.cameraAPI.stopZoom()
    else:
        # Set Zoom
        if positionVal <= thres_Z[int(nPalierZ / 2)]:
            # Wide Mvt
            dirZ = camera.cameraAPI.ZoomDirection(3)
            r = 0
            for i in range(0, int(nPalierZ / 2) + 1):
                if positionVal <= thres_Z[i]:
                    r = i
                    break
            speedZ = int(nPalierZ / 2) - r
        else:
            # Tele Mvt
            dirZ = camera.cameraAPI.ZoomDirection(2)
            r = nPalierZ + 1
            for i in range(int(nPalierZ / 2), nPalierZ + 1):
                if positionVal < thres_Z[i]:
                    r = i
                    break
            speedZ = r - int(nPalierZ / 2 + 2)
        camera.cameraAPI.setZoom(speedZ,dirZ)

def convert_joystick_values(positionX, positionY, positionZ):
    calc_Zoom_Com(positionZ)
    panDir, panSpeed = calc_Pan_Com(positionX)  # x
    tiltDir, tiltSpeed = calc_Tilt_Com(positionY)  # y
    # setTiltPan(tiltDir,tiltSpeed,panDir,panSpeed)

def fct():
    while True:
        time.sleep(1)
        if flag_read_pos_JoyStick == True:
            convert_joystick_values(posX, posY, posZ)
