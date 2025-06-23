#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm1 = Adafruit_PWMServoDriver(0x41);

String x;
float duty[15];
String xx;
int index;
int length;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.setTimeout(1);

  pwm1.begin();  
  
  pwm1.setOscillatorFrequency(27000000);
  pwm1.setPWMFreq(1600);  // This is the maximum PWM frequency
  Wire.setClock(40000);
     
}

void loop() {

  if (Serial.available() > 0)
  {
    x="";

    while(Serial.available() > 0) x = x + Serial.readString(); //read all data
    
    for (uint8_t i=0; i < 15; i++)
    {
      index = x.indexOf('/');
      length = x.length();
      duty[i] = x.substring(0, index).toFloat();
      x = x.substring(index+1,length);
      Serial.print(duty[i]);
    }
  //pwm1
  for (uint8_t i=0; i < 15; i++) {
      pwm1.setPWM(i, 0, duty[0]*4096 );
    }
    
    Serial.flush();
  }
          
#ifdef ESP8266
    yield();  // take a breather, required for ESP8266
#endif
}
