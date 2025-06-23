import os
import pandas
import shutil
import time
import csv

from common_click_lab_view1 import clickAndCreateData


def is_csv_empty(file_path):
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return True
        else:
            return False
    else:
        return True


def get_merged():
    file_list = None
    merged_path = ''
    while True:
        while True:
            file_list = os.listdir(r'C:\qianghuafile\res')
            if len(file_list) <= 0:
                clickAndCreateData()
                continue
            break
        file_list.sort()
        merged_path = os.path.join(r'C:\qianghuafile\res', file_list[-1])

        if is_csv_empty(merged_path):
            print("CSV文件为空")
            shutil.move(merged_path, r'C:\qianghuafile\olddata')
            continue
        else:
            break

    return merged_path
