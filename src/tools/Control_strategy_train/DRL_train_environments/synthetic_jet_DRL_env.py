import gym
import numpy as np
from gym import spaces
import time
import pandas as pd
import os
import shutil
from datetime import datetime
from syntheticJetControl import set_signal_generator, clickAndCreateData, read_csv_get_RMS_TimeHisDisp_1s, measureAndComputeWindSpeed
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import joblib

class myEnv_flow(gym.Env):
    def __init__(self):
        self.training_num = 1
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(301,), dtype=np.float32)
        self.t = 0
        self.epoch = 0
        self.cumulative_reward = 0.0
        self.average_reward = 0.0
        self.rms_history = []
        self.wind_history = []
        self.step_time = 14.3  # 每个step的时间（秒）
        self.control_delay = 30  # 控制延迟时间（秒）
        self.delay_steps = int(np.ceil(self.control_delay / self.step_time))  # 需要提前的step数
        self.action_buffer = []  # 存储未来几个step的动作
        self.init_time = time.time()
        
        # 初始化预测模型
        self.wind_scaler = StandardScaler()
        self.vibration_scaler = StandardScaler()
        self.wind_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.vibration_model = self._build_lstm_model()
        
        # 模型训练数据
        self.wind_X = []
        self.wind_y = []
        self.vibration_X = []
        self.vibration_y = []

    def _build_lstm_model(self):
        """构建LSTM模型用于振动预测"""
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(10, 1), return_sequences=True),
            Dropout(0.2),
            LSTM(30, activation='relu'),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def _prepare_wind_data(self, history):
        """准备风速预测的训练数据"""
        if len(history) < 10:
            return None, None
        X = []
        y = []
        for i in range(len(history) - 10):
            X.append(history[i:i+10])
            y.append(history[i+10])
        return np.array(X), np.array(y)

    def _prepare_vibration_data(self, wind_history, rms_history):
        """准备振动预测的训练数据"""
        if len(wind_history) < 10 or len(rms_history) < 10:
            return None, None
        X = []
        y = []
        for i in range(len(wind_history) - 10):
            X.append(np.column_stack((wind_history[i:i+10], rms_history[i:i+10])))
            y.append(rms_history[i+10])
        return np.array(X), np.array(y)

    def calculate_predictive_reward(self, current_rms, predicted_wind):
        """计算预测性奖励"""
        # 基于预测风速计算预期振动
        expected_vibration = self.estimate_vibration(predicted_wind)
        
        # 计算预测振动与当前振动的差异
        vibration_diff = np.abs(expected_vibration - current_rms)
        
        # 如果预测到高振动，给予更高的奖励以鼓励提前控制
        if np.max(expected_vibration) > 0.4:  # 振动阈值
            # 预测越准确，奖励越高
            accuracy_reward = 1.0 - min(vibration_diff, 1.0)
            return 1.0 * accuracy_reward  # 增加预测性奖励的权重
        return 0.0

    def estimate_vibration(self, wind_speeds):
        """使用LSTM预测振动"""
        if len(self.rms_history) > 10 and len(self.wind_history) > 10:
            # 准备训练数据
            X, y = self._prepare_vibration_data(self.wind_history, self.rms_history)
            if X is not None and len(X) > 0:
                # 训练模型
                self.vibration_model.fit(X, y, epochs=10, batch_size=32, verbose=0)
                
                # 准备预测数据
                last_10_data = np.column_stack((
                    self.wind_history[-10:],
                    self.rms_history[-10:]
                )).reshape(1, 10, 2)
                
                # 预测振动
                prediction = self.vibration_model.predict(last_10_data)
                return prediction.flatten()
        return np.array([0.5 if w > 5.0 else 0.1 for w in wind_speeds])

    def step(self, action):
        now_time = time.time()
        self.init_time = now_time
        self.t += 1

        # 解析动作
        self.SJ_v = (action[0] + 1) / 2 * 20
        self.SJ_f = 6
        self.SJ_v = np.clip(self.SJ_v, 1, 20)
        self.SJ_f = np.clip(self.SJ_f, 2, 10)

        # 将当前动作添加到缓冲区
        self.action_buffer.append(action)
        
        # 如果缓冲区长度超过延迟步数，移除最旧的动作
        if len(self.action_buffer) > self.delay_steps:
            self.action_buffer.pop(0)

        # 应用延迟后的动作
        if len(self.action_buffer) > 0:
            delayed_action = self.action_buffer[0]
            delayed_SJ_v = (delayed_action[0] + 1) / 2 * 20
            delayed_SJ_v = np.clip(delayed_SJ_v, 1, 20)
            set_signal_generator(delayed_SJ_v, self.SJ_f)
        else:
            # 如果没有延迟动作，使用当前动作
            set_signal_generator(self.SJ_v, self.SJ_f)

        # 采集数据
        clickAndCreateData()
        
        # 获取数据
        source_file = 'c:/data/data.csv'
        destination_folder = 'c:/data/readdata/'
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        base_name = os.path.basename(source_file)
        filename, extension = os.path.splitext(base_name)
        new_filename = f'read_{filename}_{timestamp}{extension}'
        destination_file = os.path.join(destination_folder, new_filename)

        shutil.copyfile(source_file, destination_file)
        rms_value, TimHisdata = read_csv_get_RMS_TimeHisDisp_1s(destination_file)
        currentWindVelocity = measureAndComputeWindSpeed()

        # 更新历史数据
        self.rms_history.append(rms_value)
        self.wind_history.append(currentWindVelocity)

        # 预测30秒后的风速和振动
        predicted_wind = self.predict_future_wind(currentWindVelocity)
        predicted_vibration = self.estimate_vibration(predicted_wind)
        
        # 计算预测性奖励
        predictive_reward = self.calculate_predictive_reward(rms_value, predicted_wind)
        
        # 计算振动抑制奖励
        # 使用指数衰减函数，振动越小，奖励越高
        suppression_reward = 100 * np.exp(-5 * rms_value)  # 指数衰减函数
        
        # 如果振动低于阈值，给予额外奖励
        if rms_value < 0.4:  # 振动阈值
            suppression_reward += 50  # 额外奖励
        
        # 计算预测准确性奖励
        prediction_accuracy = 1.0 - min(np.abs(predicted_vibration - rms_value), 1.0)
        accuracy_reward = 20.0 * prediction_accuracy  # 增加预测准确性奖励的权重
        
        # 计算总奖励
        reward = suppression_reward + predictive_reward + accuracy_reward
        reward = round(reward, 3)

        # 更新累积奖励
        self.cumulative_reward += reward
        self.average_reward = self.cumulative_reward / self.t

        # 构建状态
        s_ = np.concatenate(([rms_value], TimHisdata))

        # 检查是否结束
        done = self.t >= 300

        # 记录数据
        print('step: ', self.t, ' ', 'SJ_v: ', self.SJ_v, ' ', 'SJ_f: ', self.SJ_f,
              'state: ', s_, ' ', 'reward: ', reward, ' ', 'WindVelocity: ', currentWindVelocity,
              'predicted_vibration: ', predicted_vibration,
              'suppression_reward: ', suppression_reward,
              'predictive_reward: ', predictive_reward,
              'accuracy_reward: ', accuracy_reward)

        with open('save/datalog/data.txt', 'a') as f:
            f.write(f'step: {self.t} voltage: {self.SJ_v} frequency: {self.SJ_f} VIVRMS: {rms_value} '
                   f'reward: {reward} WindVelocity: {currentWindVelocity} '
                   f'predicted_vibration: {predicted_vibration} '
                   f'suppression_reward: {suppression_reward} '
                   f'predictive_reward: {predictive_reward} '
                   f'accuracy_reward: {accuracy_reward}\n')

        return s_, float(reward), done, {}

    def predict_future_wind(self, current_wind):
        """使用随机森林预测未来风速"""
        if len(self.wind_history) > 10:
            # 准备训练数据
            X, y = self._prepare_wind_data(self.wind_history)
            if X is not None and len(X) > 0:
                # 训练模型
                self.wind_model.fit(X, y)
                
                # 准备预测数据
                last_10_wind = np.array(self.wind_history[-10:]).reshape(1, -1)
                # 预测30秒后的风速
                future_time = len(self.wind_history[-10:]) + 30/14.3
                prediction = self.wind_model.predict(last_10_wind)
                return prediction
        return np.array([current_wind])

    def reset(self):
        self.init_time = time.time()
        self.t = 0
        self.epoch += 1
        self.cumulative_reward = 0.0
        self.average_reward = 0.0
        self.rms_history = []
        self.wind_history = []
        self.action_buffer = []  # 清空动作缓冲区
        set_signal_generator(0.1, 0.1)
        self.reset_init()
        self.s = np.array([0.0], dtype=np.float32)
        return self.s

    def reset_init(self):
        set_signal_generator(0.1, 0.1)
        print('开始初始化')
        with open('save/datalog/data.txt', 'a') as f:
            f.write(f'step: {self.t} init\n')

    def save_models(self):
        """保存训练好的模型"""
        joblib.dump(self.wind_model, 'models/wind_model.joblib')
        self.vibration_model.save('models/vibration_model.h5')
        joblib.dump(self.wind_scaler, 'models/wind_scaler.joblib')
        joblib.dump(self.vibration_scaler, 'models/vibration_scaler.joblib')

    def load_models(self):
        """加载已训练的模型"""
        try:
            self.wind_model = joblib.load('models/wind_model.joblib')
            self.vibration_model = tf.keras.models.load_model('models/vibration_model.h5')
            self.wind_scaler = joblib.load('models/wind_scaler.joblib')
            self.vibration_scaler = joblib.load('models/vibration_scaler.joblib')
        except:
            print("No pre-trained models found. Using new models.")

if __name__ == '__main__':
    pass 