import pyautogui as ui 
import time

# 窗口放在桌面左下角
def get_data():
    ui.FAILSAFE = False
    ui.PAUSE = 1  # 设置键盘操作的时候停顿间隔时间为1秒

    ui.click(714, 947, button='left')
    #  ui.click(115, 732, button='left')  # 在屏幕200px，200px的位置点击鼠标左键
    #  ui.click(99, 757, button='left')  # 在屏幕200px，200px的位置点击鼠标右键
    time.sleep(3)
    ui.click(714, 947, button='left')
    
    # ui.click(1069, 889, button='right')
    #  ui.click(30, 734, button='left')  # 在屏幕200px，200px的位置点击鼠标中键
    #  ui.click(30, 755, button='left')  # 在屏幕200px，200px的位置点击鼠标中键
    #  ui.press('enter')
get_data()