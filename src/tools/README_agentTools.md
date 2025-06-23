# AI Agent Tools 说明文档

本文件系统性介绍 `src/tools/` 目录下已封装的所有流动控制与数据采集 AI Agent 工具，帮助用户快速了解、调用和扩展。

---

## 工具总览

- **流动控制类**：SyntheticJetController、WindFieldController、PneumaticFlowController、ShapeChangeWingController
- **数据采集类**：LaserDisplacementSensor、WindFieldVelocitySensor、PressureScanner、ForceBalanceSensor
- **DRL策略训练类**：DRLTrainer
- **环境定义**：flowEnv...、pneumatic_flow_controller_DRL_env、shape_change_wing_DRL_env（所有自定义Gym环境）

---

# 1. 流动控制类（flow_control）

## SyntheticJetController（合成射流信号发生器控制）

**简介**  
用于控制合成射流实验中的信号发生器，实现电压、调制频率等参数的设置与批量应用。

**主要功能**
- 初始化并连接信号发生器（支持pyvisa）
- 设置输出电压和调制频率
- 批量应用电压序列，自动间隔切换
- 关闭信号发生器

**特性亮点**
- 支持多品牌信号发生器（只需更换resource_name）
- 批量序列应用适合自动化实验
- 错误处理完善，连接失败有提示

**用法示例**
```python
from tools.flow_control.synthetic_jet import SyntheticJetController
controller = SyntheticJetController()
controller.set(voltage=10, modulation_frequency=3)
controller.apply_voltage_sequence([5, 10, 15], interval=5, modulation_frequency=3)
controller.close()
```

**注意事项**
- 需安装 `pyvisa` 库
- 需正确配置信号发生器的VISA地址
- 批量应用时请确保实验安全

---

## WindFieldController（风场发生器/可编程风扇阵列控制）

**简介**  
用于通过串口控制多块Arduino板，实现对风扇阵列的PWM调节，支持全场、单行、单列、单风扇独立控制及Excel批量风场设定。

**主要功能**
- 串口初始化与多板连接
- 全场/单行/单列/单风扇PWM控制
- Excel批量设定梯度风、展向风、时程风
- 支持风场自动切换与定时控制

**特性亮点**
- 支持大规模风扇阵列分组控制
- 兼容多种风场设定模式
- 适合风洞实验自动化

**用法示例**
```python
from tools.flow_control.wind_field_controller import WindFieldController
controller = WindFieldController('COM18', 'COM19', 'COM21')
controller.control_all(1000)
controller.control_row(5, 1200)
controller.control_column(10, 900)
controller.control_single_fan(8, 8, 1100)
controller.control_terrain('your_excel.xlsx')
controller.control_spanwise('your_excel.xlsx')
controller.control_timeserie('your_excel.xlsx', interval=1)
controller.close()
```

**注意事项**
- 需正确配置串口号和波特率
- Excel文件格式需与实验要求一致
- 控制大功率风扇时注意安全

---

## PneumaticFlowController（气管式吹吸气流量控制）

**简介**  
用于通过Modbus协议控制气管式吹吸气流量，适合风洞实验、主动流动控制等。

**主要功能**
- 通过串口和Modbus协议设置流量
- 支持设备地址、模式修改
- 读取当前流量、瞬时流量

**特性亮点**
- 兼容多种流量控制器
- 支持多设备并行管理
- 接口简洁，易于集成到自动化实验

**用法示例**
```python
from tools.flow_control.pneumatic_flow_controller import PneumaticFlowController
controller = PneumaticFlowController(port='COM3', baudrate=9600)
controller.set_flow_rate(device_id=1, value=2.5)
flow = controller.read_cvalue(device_id=1)
print(f"Current flow: {flow}")
controller.close()
```

**注意事项**
- 需安装modbus_tk、serial等依赖
- 需正确配置串口号、波特率和设备地址

---

## ShapeChangeWingController（可形变翼板控制）

**简介**  
用于多翼板的精确位置、角度控制，支持状态保存和串口通信，适合主动流动控制和气动实验。

**主要功能**
- 设置多翼板位置、角度
- 自动保存和读取状态
- 支持翼板复位

**特性亮点**
- 支持多翼板联动
- 状态差分控制，减少误差
- 兼容多种实验场景

**用法示例**
```python
from tools.flow_control.shape_change_wing_controller import ShapeChangeWingController
controller = ShapeChangeWingController(port='COM17', baudrate=115200)
controller.set_fin_position([0, 0, 0, 0])
controller.set_fin_angle([10, 0, 0, 0])
controller.reset_position()
controller.reset_angle()
```

**注意事项**
- 需安装serial、numpy、struct等依赖
- 需正确配置串口号和波特率
- 使用前请确保硬件连接安全

---

# 2. 数据采集类（data_acquisition）

## LaserDisplacementSensor（激光位移计数据采集与处理）

**简介**  
用于激光位移计的自动采集触发、RMS值与采样数据读取、正弦拟合等。

**主要功能**
- 通过UDP或自动点击触发LabVIEW采集
- 读取RMS值和时域采样数据
- 支持1秒/5秒采样窗口
- 对采集数据进行正弦拟合分析

**特性亮点**
- 支持与LabVIEW无缝联动
- 采集与分析一体化
- 适合振动、位移等实验场景

**用法示例**
```python
from tools.data_acquisition.displacement_sensor import LaserDisplacementSensor
sensor = LaserDisplacementSensor('C:/data/data.csv')
sensor.trigger_acquisition()
rms, samples = sensor.get_rms_and_samples()
params = sensor.fit_sine()
```

**注意事项**
- 需配置LabVIEW采集端口和数据文件路径
- 依赖pandas、numpy、scipy等库

---

## WindFieldVelocitySensor（风场风速测量/皮托管）

**简介**  
通过皮托管原理测量风场风速，适合风洞实验。

**主要功能**
- 触发采集（UDP）
- 读取最新风速数据

**特性亮点**
- 与压力扫描阀底层复用，接口简洁
- 适合实时风速监测

**用法示例**
```python
from tools.data_acquisition.wind_field_velocity_sensor import WindFieldVelocitySensor
sensor = WindFieldVelocitySensor('191.30.90.241', './test_data')
sensor.trigger()
wind = sensor.get_wind_velocity()
```

**注意事项**
- 需配置设备IP和数据保存路径
- 依赖底层WindAndPressureScanner实现

---

## PressureScanner（压力扫描阀多通道压力分布采集）

**简介**  
用于采集多通道压力扫描阀的压力分布数据。

**主要功能**
- 触发采集（UDP）
- 读取最新23通道压力分布

**特性亮点**
- 与风速测量底层复用，接口独立
- 适合风洞壁面压力分布实验

**用法示例**
```python
from tools.data_acquisition.pressure_scanner import PressureScanner
scanner = PressureScanner('191.30.90.241', './test_data')
scanner.trigger()
pressures = scanner.get_pressure_distribution()
```

**注意事项**
- 需配置设备IP和数据保存路径
- 依赖底层WindAndPressureScanner实现

---

## ForceBalanceSensor（三分力天平数据采集）

**简介**  
用于三分力天平的自动采集触发与三分力（Fx, Fy, Fz）数据读取。

**主要功能**
- 通过UDP触发LabVIEW采集
- 读取最新三分力数据

**特性亮点**
- 支持自动化实验流程
- 适合气动力测量

**用法示例**
```python
from tools.data_acquisition.force_balance_sensor import ForceBalanceSensor
sensor = ForceBalanceSensor('C:/data/force_data.csv')
sensor.trigger_acquisition()
force = sensor.get_latest_force()
```

**注意事项**
- 需配置LabVIEW采集端口和数据文件路径
- 依赖pandas等库

---

# 3. DRL策略训练类（Control_strategy_training）

## DRLTrainer（深度强化学习流动控制策略训练）

**简介**  
基于stable-baselines3的SAC算法，支持流动控制策略的训练、断点续训与评估。

**主要功能**
- 支持SAC算法的训练、断点续训、评估
- 环境通过env_fn参数灵活注入，适配多种流动控制环境
- 训练参数、日志目录、模型保存等均可配置

**特性亮点**
- 兼容所有标准Gym环境
- 支持自定义网络结构和超参数
- 训练流程自动化，断点续训方便

**用法示例**
```python
from tools.Control_strategy_training.DRL_trainer import DRLTrainer
from tools.environments.flowEnvTransient1ActionVoltage_Predictive import myEnv_flow
trainer = DRLTrainer(env_fn=myEnv_flow)
trainer.train(total_timesteps=10000)
# trainer.load_and_continue_train('logs_norm/rl_model_norm_12400_steps.zip', total_timesteps=50000, replay_buffer_path='logs_norm/rl_model_norm_replay_buffer_12400_steps.pkl')
# trainer.evaluate('logs_norm/rl_model_norm_12400_steps.zip')
```

**注意事项**
- 需安装stable-baselines3、torch、numpy、gym等依赖
- 环境文件需实现标准Gym接口，建议放在tools/environments/

---

# 4. 环境定义（environments）

## pneumatic_flow_controller_DRL_env（气管式吹吸气流量控制DRL环境）

**简介**  
基于PneumaticFlowController的标准Gym环境，适合SAC等DRL算法训练气管流量控制策略。

**主要功能**
- 标准Gym接口（reset/step/close）
- 动作空间为流量控制指令
- 状态空间、奖励函数可自定义

**特性亮点**
- 便于与DRLTrainer无缝集成
- 支持真实硬件实验与仿真

**用法示例**
```python
from tools.environments.pneumatic_flow_controller_DRL_env import WindTunnelEnv
env = WindTunnelEnv(port='COM3', baudrate=9600)
obs = env.reset()
obs, reward, done, info = env.step([0.5])
```

**注意事项**
- 需配合PneumaticFlowController使用
- 状态、奖励函数需根据实验需求完善

---

## shape_change_wing_DRL_env（可形变翼板控制DRL环境）

**简介**  
基于ShapeChangeWingController的标准Gym环境，适合DRL算法训练多翼板协同控制策略。

**主要功能**
- 标准Gym接口（reset/step/close）
- 动作空间为多翼板目标位置
- 状态空间、奖励函数可自定义

**特性亮点**
- 便于与DRLTrainer无缝集成
- 支持多翼板联动实验

**用法示例**
```python
from tools.environments.shape_change_wing_DRL_env import ShapeChangeWingEnv
env = ShapeChangeWingEnv(port='COM17', baudrate=115200)
obs = env.reset()
obs, reward, done, info = env.step([0.1, 0.2, 0.3, 0.4])
```

**注意事项**
- 需配合ShapeChangeWingController使用
- 状态、奖励函数需根据实验需求完善

---

# 归档与维护说明

- 原始实验与开发代码已归档在 `tools/archive/SyntheticJetDRL/`，仅供查阅和参考，不建议直接修改。
- 所有主流程和新开发请统一在tools及environments目录下进行。

---

如有疑问或需扩展新功能，请联系开发者或查阅各工具类源码注释。 