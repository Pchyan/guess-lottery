from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
from TaiwanLottery import TaiwanLotteryCrawler
import matplotlib.pyplot as plt
import re  # 引入正則表達式模組
import itertools
import random

app = Flask(__name__)

# 新增函數以爬取指定年份和月份的開獎紀錄
def fetch_lottery_results(start_year, end_year, start_month, end_month):
    lottery = TaiwanLotteryCrawler()
    
    results = []
    
    # 獲取指定範圍內的開獎紀錄
    for year in range(int(start_year), int(end_year) + 1):
        # 設定開始和結束月份
        if year == int(start_year):
            month_start = int(start_month)
        else:
            month_start = 1
        
        if year == int(end_year):
            month_end = int(end_month)
        else:
            month_end = 12
        
        for month in range(month_start, month_end + 1):
            month_str = str(month).zfill(2)  # 確保月份是兩位數
            result = lottery.lotto4d([year, month_str])
            if result and isinstance(result, list):
                results.extend(result)
    
    # 檢查返回的結果是否為空
    if not results:
        raise ValueError(f"無法獲取 {start_year}年{start_month}月到 {end_year}年{end_month}月的開獎紀錄，請檢查輸入的年份和月份。")
    
    return results

# 儲存資料到 CSV
def save_to_csv(data, filename="4d_results.csv"):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"資料已儲存到 {filename}")

# 讀取 CSV 資料
def load_data():
    filename = '4d_results.csv'  # 確保這裡的路徑是正確的
    if not os.path.exists(filename):
        raise FileNotFoundError(f"文件未找到: {filename}")
    
    if os.path.getsize(filename) == 0:
        raise ValueError(f"文件是空的: {filename}")

    try:
        df = pd.read_csv(filename)
        if df.empty:
            raise ValueError(f"讀取的文件是空的: {filename}")
        return df
    except pd.errors.EmptyDataError:
        raise ValueError(f"無法從文件中解析數據: {filename}")
    except pd.errors.ParserError:
        raise ValueError(f"文件格式錯誤: {filename}")

# 分析獎號落點
def analyze_numbers(df):
    # 將獎號轉換為數字列表
    all_numbers = []
    for numbers in df['獎號']:  # 使用 '獎號' 而不是 'numbers'
        # 使用正則表達式提取數字
        extracted_numbers = re.findall(r'\d+', str(numbers))  # 提取所有數字
        all_numbers.extend([int(num) for num in extracted_numbers])  # 將提取的數字轉換為整數並擴展列表
    
    # 統計每個數字的出現次數
    number_counts = pd.Series(all_numbers).value_counts().sort_index()
    print("各數字出現次數：")
    print(number_counts)
    
    # 可視化分析
    plt.figure(figsize=(12, 6))
    number_counts.plot(kind='bar', color='skyblue')
    plt.title("四星彩獎號落點分析")
    plt.xlabel("數字")
    plt.ylabel("出現次數")
    
    # 保存圖形為文件
    plt.savefig('static/lottery_analysis.png')  # 將圖形保存到 static 資料夾
    plt.close()  # 關閉圖形以釋放資源
    
    # 生成最有可能的四個數字組合
    most_common_numbers = number_counts.index[-4:]  # 獲取出現頻率最高的四個數字
    possible_combinations = list(itertools.combinations(most_common_numbers, 4))  # 生成所有可能的四個數字組合
    
    # 隨機選擇五組組合
    selected_combinations = random.sample(possible_combinations, min(5, len(possible_combinations)))
    
    print("最有可能出現的四個數字組合：")
    for combo in selected_combinations:
        print(combo)
    
    return number_counts, selected_combinations

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_year_month = request.form['start_year_month']
        end_year_month = request.form['end_year_month']
        
        # 解析年份和月份
        start_year, start_month = start_year_month.split('-')
        end_year, end_month = end_year_month.split('-')
        
        # 檢查年份和月份範圍
        if int(start_year) > int(end_year) or (int(start_year) == int(end_year) and int(start_month) > int(end_month)):
            raise ValueError("結束年份和月份必須大於或等於開始年份和月份。")
        
        lottery_results = fetch_lottery_results(start_year, end_year, start_month, end_month)
        save_to_csv(lottery_results)  # 儲存從爬蟲獲取的資料
        return redirect(url_for('results'))

    return render_template('index.html')

@app.route('/results')
def results():
    df = load_data()
    number_counts, selected_combinations = analyze_numbers(df)
    return render_template('results.html', number_counts=number_counts, selected_combinations=selected_combinations)

if __name__ == '__main__':
    app.run(debug=True)