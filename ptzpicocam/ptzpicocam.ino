#define JOYX_PIN A0
#define JOYY_PIN A1
#define ZOOM_PIN A2
#define ZOOM_LED_PIN 5

#define BTN_POS_0 3
#define SHORT_PRESS_TIME 1000
#define TIME_FOR_MEMORY_commande_memory 5 //10 --> 10 secondes

typedef enum PanDirection {
  PAN_LEFT = 1,
  PAN_RIGHT = 2,
  PAN_STOP = 3,
} PanDirection;

typedef enum TiltDirection {
  TILT_UP = 1,
  TILT_DOWN = 2,
  TILT_STOP = 3,
} TiltDirection;

typedef enum ZoomDirection {
  ZOOM_STOP = 0,
  ZOOM_TELE = 2,
  ZOOM_WIDE = 3,
} ZoomDirection;

struct Camera {
  PanDirection panDirection;
  uint16_t panSpeed;
  TiltDirection tiltDirection;
  uint16_t tiltSpeed;
  ZoomDirection zoomDirection;
  uint8_t zoomSpeed;
};

struct Bouton{
  uint8_t pin;
  unsigned int long timepressed;
  unsigned int long lastpressed;
  bool isPress;
};

typedef struct Joystick {
  int16_t x;
  int16_t y;
  int16_t zoom;
  uint16_t minVal;
  uint16_t maxVal;
  int16_t leftLimit;
  int16_t rightLimit;
  uint8_t deadzone;
} Joystick;

uint8_t drivePacket[] = {
  0x81, 0x01, 0x06, 0x01,
  0x0, 0x0, 0x00, 0x00, 0xff
};

uint8_t memoryPacket[] = {
  0x81, 0x01, 0x04, 0x3f,
  0x02, 0x0, 0xff
};

uint8_t zoomPacket[] = {
  0x81, 0x01, 0x04, 0x07, 0x00, 0xff
};

Camera camera;
Joystick joystick;
Bouton allbtn[1];

int8_t buttonToCheck = -1;
volatile int8_t commande_memory = 0;  //0 pas de commande, 1 memory commande, 2 drive commande
volatile unsigned long start_memory_commande_memory = 0;

void initJoystick() {
  joystick.minVal = 0;
  joystick.maxVal = 1023;
  joystick.deadzone = 5;

  uint16_t center = joystick.maxVal / 2;
  uint16_t threshold = center * joystick.deadzone / 100;
  joystick.leftLimit = center - threshold;
  joystick.rightLimit = center + threshold;
}

void isr_Btn1(){
  if(millis()-allbtn[0].lastpressed>70) {
    allbtn[0].lastpressed=millis();
    buttonToCheck = 0;
  }
}

void setup() {
  Serial.begin(9600);
  initJoystick();

  pinMode(JOYX_PIN, INPUT);
  pinMode(JOYY_PIN, INPUT);
  pinMode(ZOOM_PIN, INPUT);
  pinMode(ZOOM_LED_PIN, OUTPUT);

  pinMode(BTN_POS_0,INPUT);
  allbtn[0].pin=BTN_POS_0;
  allbtn[0].lastpressed=0;
  allbtn[0].timepressed=0;
  allbtn[0].isPress=false;
  attachInterrupt(digitalPinToInterrupt(BTN_POS_0),isr_Btn1,CHANGE);
}

void setZoomLed(uint8_t value) {
  digitalWrite(ZOOM_LED_PIN, value);
}

void loop() {
  
  if (buttonToCheck != -1) {
    if(allbtn[buttonToCheck].isPress == false) {
      allbtn[buttonToCheck].isPress = true;
      allbtn[buttonToCheck].timepressed = millis();   
    } else {
      if(millis()-allbtn[buttonToCheck].timepressed<SHORT_PRESS_TIME) {
        //Short press 
        memoryPacket[4] = 0x02;
        memoryPacket[5] = 0x00;
        commande_memory=2;
        start_memory_commande_memory = millis();
      } else {
        //Long press
        memoryPacket[4] = 0x01;
        memoryPacket[5] = 0x00;
        commande_memory=1;
      }
      allbtn[buttonToCheck].isPress=false;

    }
    buttonToCheck = -1;
  }
  joystick.x = analogRead(JOYX_PIN);
  joystick.y = analogRead(JOYY_PIN);
  joystick.zoom = analogRead(ZOOM_PIN);

  if (joystick.x < joystick.leftLimit) {
    camera.panSpeed = map(abs(joystick.x - joystick.leftLimit), joystick.minVal, joystick.leftLimit, 1, 0x18);
    camera.panDirection = PAN_RIGHT;
  }
  else if (joystick.x > joystick.rightLimit) {
    camera.panSpeed = map(joystick.x, joystick.rightLimit, joystick.maxVal, 1, 0x18);
    camera.panDirection = PAN_LEFT;
  }
  else {
    camera.panSpeed = 1;
    camera.panDirection = PAN_STOP;
  }

  if (joystick.y < joystick.leftLimit) {
    camera.tiltSpeed = map(abs(joystick.y - joystick.leftLimit), joystick.minVal, joystick.leftLimit, 1, 0x17);
    camera.tiltDirection = TILT_UP;
  }
  else if (joystick.y > joystick.rightLimit) {
    camera.tiltSpeed = map(joystick.y, joystick.rightLimit, joystick.maxVal, 1, 0x18);
    camera.tiltDirection = TILT_DOWN;
  }
  else {
    camera.tiltSpeed = 1;
    camera.tiltDirection = TILT_STOP;
  }

  if (joystick.zoom < joystick.leftLimit) {
    camera.zoomDirection = ZOOM_WIDE;
    camera.zoomSpeed = map(abs(joystick.zoom - joystick.leftLimit), joystick.minVal, joystick.leftLimit, 1, 7);
    setZoomLed(LOW);
  }
  else if (joystick.zoom > joystick.rightLimit) {
    camera.zoomDirection = ZOOM_TELE;
    camera.zoomSpeed = map(joystick.zoom, joystick.rightLimit, joystick.maxVal, 1, 7);
    setZoomLed(LOW);
  }
  else {
    camera.zoomDirection = ZOOM_STOP;
    camera.zoomSpeed = 1;
    setZoomLed(HIGH);
  }

  drivePacket[4] = camera.panSpeed;
  drivePacket[5] = camera.tiltSpeed;
  drivePacket[6] = camera.panDirection;
  drivePacket[7] = camera.tiltDirection;

  zoomPacket[4] = (camera.zoomDirection << 4) | camera.zoomSpeed;
  if((commande_memory > 0)) {
    Serial.write(memoryPacket, 7);  
    if(commande_memory==1) {
      commande_memory=0; 
    } else if((millis()-start_memory_commande_memory) >TIME_FOR_MEMORY_commande_memory*1000) {
      commande_memory=0;  
    }
  } else {
    Serial.write(drivePacket, 9);
    Serial.write(zoomPacket, 6);
  }
  /*Serial.print(camera.panSpeed);
  Serial.print(' ');
  Serial.print(camera.tiltSpeed);
  Serial.println();*/

  delay(33);
}
