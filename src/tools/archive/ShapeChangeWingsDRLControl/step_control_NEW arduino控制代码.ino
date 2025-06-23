#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
// 定义电机控制用常量
// A4988连接Arduino引脚号，0号为旋转电机，1-4为翼板电机
const int dirPin_0 = 40;  // 方向引脚
const int stepPin_0 = 41; // 步进引脚
const int dirPin_1 = 31;  // 方向引脚
const int stepPin_1 = 32; // 步进引脚
const int dirPin_2 = 33;  // 方向引脚
const int stepPin_2 = 34; // 步进引脚
const int dirPin_3 = 35;  // 方向引脚
const int stepPin_3 = 36; // 步进引脚
const int dirPin_4 = 37;  // 方向引脚
const int stepPin_4 = 38; // 步进引脚
#define NUM_VALUES 5  // 5 个浮动数（4个差值 + 1个标识符）
float Dir_dis[NUM_VALUES];  // 用于存储接收到的 5 个浮动数
String x;
int index;
int length;
// 电机每圈步数
const int STEPS_PER_REV = 400;

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(1);
  // 设置控制电机的引脚为输出
  pinMode(stepPin_0, OUTPUT); 
  pinMode(dirPin_0, OUTPUT);
  pinMode(stepPin_1, OUTPUT); 
  pinMode(dirPin_1, OUTPUT);   
  pinMode(stepPin_2, OUTPUT); 
  pinMode(dirPin_2, OUTPUT); 
  pinMode(stepPin_3, OUTPUT); 
  pinMode(dirPin_3, OUTPUT); 
  pinMode(stepPin_4, OUTPUT); 
  pinMode(dirPin_4, OUTPUT); 
}

void loop() {
  if (Serial.available() >= 20) {  // 判断接收到的数据长度（5个浮动数，每个4字节，共20字节）
    byte byteData[20];  // 用于存储接收到的字节数据
    int bytesRead = Serial.readBytes(byteData, 20);  // 读取数据
    if (bytesRead == 20) {  // 确保接收到 20 字节数据
      // 将字节数据转换为 5 个浮动数
      float receivedData[NUM_VALUES];
      memcpy(receivedData, byteData, NUM_VALUES * sizeof(float));
      // 打印接收到的数据
      Serial.print("Received Data: ");
      for (int i = 0; i < NUM_VALUES; i++) {
        Dir_dis[i] = receivedData[i];
        Serial.print(Dir_dis[i]);
        Serial.print(" ");
      }
      Serial.println();

      // 根据 Dir_dis[0] 判断控制模式
      if (Dir_dis[0] == 1) {
        // 控制翼板电机的方向
        setMotorDirection(1, Dir_dis[1], dirPin_1);
        setMotorDirection(2, Dir_dis[2], dirPin_2);
        setMotorDirection(3, Dir_dis[3], dirPin_3);
        setMotorDirection(4, Dir_dis[4], dirPin_4);
        
        // 控制翼板电机旋转
        controlMotorStep(stepPin_1, Dir_dis[1]);
        controlMotorStep(stepPin_2, Dir_dis[2]);
        controlMotorStep(stepPin_3, Dir_dis[3]);
        controlMotorStep(stepPin_4, Dir_dis[4]);
      }

      if (Dir_dis[0] == 2) {
        // 控制旋转电机
        setMotorDirection(0, Dir_dis[1], dirPin_0);  
        // 旋转电机步进
        controlRotationMotor(stepPin_0, Dir_dis[1]);
      }
    } else {
      Serial.println("Error: Incomplete data received");
    }
  }
}

// 设置电机方向
void setMotorDirection(int motor, float distance, int dirPin) {
  if (distance < 0) {
    digitalWrite(dirPin, HIGH);  // 逆时针旋转
  } else {
    digitalWrite(dirPin, LOW);   // 顺时针旋转
  }
}

// 控制电机步进
void controlMotorStep(int stepPin, float steps) {
  int stepsToMove = STEPS_PER_REV * abs(steps) * 0.5; // 计算步数
  for (int i = 0; i < stepsToMove; i++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(200); // 延迟
    digitalWrite(stepPin, LOW);
    delayMicroseconds(200); // 延迟
  }
}

// 控制旋转电机步进
void controlRotationMotor(int stepPin, float steps) {
  int stepsToMove = 35 * 400 / 360 * abs(steps); // 旋转电机的步数计算
  for (int i = 0; i < stepsToMove; i++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(2000); // 延迟
    digitalWrite(stepPin, LOW);
    delayMicroseconds(2000); // 延迟
  }
}