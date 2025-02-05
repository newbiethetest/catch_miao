from trader_tool.stock_data import stock_data
import pandas as pd
import numpy as np
import requests
import urllib.parse
from datetime import datetime, timedelta
import json
import os
import time
import urllib3
import platform

# 屏蔽 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ETFTracker:
    def load_token(self):
        """加载token"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    token = f.read().strip()
                    if token:
                        self.headers['Token'] = token
                        return True
        except Exception as e:
            print(f"Error loading token: {e}")
        return False

    def save_token(self, token):
        """保存token"""
        try:
            # 如果是Linux且目录不存在，创建目录
            if not self.is_windows:
                os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
                
            with open(self.token_file, 'w') as f:
                f.write(token)
                return True
        except Exception as e:
            print(f"Error saving token: {e}")
            return False

    def refresh_token(self):
        """刷新小鱼token"""
        try:
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Origin': 'http://xiaoyudecqg.cn',
                'Referer': 'http://xiaoyudecqg.cn/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            
            json_data = {
                'code': '061D2i1w38bEe437Fl3w3OMEip3D2i1X',
                'token': 'eyJhbGciOiJIUzUxMiJ9.eyJpZCI6IjE3Mzc2Mzk1OTQ1NzQyNDE3OTMiLCJvcGVuSWQiOiJvM1ZNNzVwRTBkRm5CZVh1QUdIelVtaEtsSG0wIiwic3Vic2NyaWJlIjoiMSIsInV1aWQiOiI3OGJkN2NhZC05Njg2LTQ3ZWYtOTYzZi03MWE5MjlmYTY2ZDUiLCJzdWIiOiIxNzM3NjM5NTk0NTc0MjQxNzkzIiwiaWF0IjoxNzM2OTg1MzY1LCJleHAiOjE3MzcwNzE3NjV9.8Tul4RxIUdmA1CeGxuJYKMV0q3JSGXAs9AiIMuo_rwaYb_PIeobSKxFgOfgKtNemIaHsDQLc6-8APO3Df-r-MA',
            }
            
            response = requests.post(
                'http://xiaoyudecqg.cn/htl/mp/api/unAuth/login',
                headers=headers,
                json=json_data,
                verify=False
            )
            response_data = response.json()
            print("刷新结果:",response_data)
            if response_data.get('code') == 200:
                new_token = response_data.get('data')
                if new_token:
                    self.headers['Token'] = new_token
                    if self.save_token(new_token):
                        print("Token refreshed and saved successfully")
                        return True
            else:
                error_url = "http://fwalert.com/2d0de187-389a-4be4-811b-332b2e244240?message=xiaoyu_cookie_failed"
                requests.get(error_url)
                print(f"刷新小鱼token失败: {response_data}")
                return False
            
        except Exception as e:
            print(f"刷新小鱼token时发生错误: {e}")
            return False

    def __init__(self):
        self.urgent_fwalert_url = "https://fwalert.com/2d0de187-389a-4be4-811b-332b2e244240"
        self.wxpusher_token = "YOUR_WXPUSHER_TOKEN"
        self.wxpusher_url = "http://wxpusher.zjiecode.com/api/send/message"
        self.stock_data = stock_data()
        
        # 设置文件路径
        self.is_windows = platform.system().lower() == 'windows'
        if self.is_windows:
            self.base_path = ''  # Windows下使用当前目录
        else:
            self.base_path = '/home/app/'  # Linux下使用自定义目录
        self.token_file = f'{self.base_path}token.txt'
        
        # 初始化 headers
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'http://xiaoyudecqg.cn',
            'Referer': 'http://xiaoyudecqg.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Token': ''  # 初始化为空，后续会通过load_token或refresh_token更新
        }
        
        # 初始化时加载token
        if not self.load_token():
            if not self.refresh_token():
                print("Warning: Failed to initialize token")

    def get_historical_discount(self, fund_code, fund_name, type_value):
        """获取基金历史溢价率数据"""
        try:
            params = {
                'fundCode': fund_code,
                'fundName': fund_name,
                'type': type_value,
                'current': '1',
            }
            
            response = requests.get(
                'http://xiaoyudecqg.cn/htl/mp/api/arbitrage/getHis',
                params=params,
                headers=self.headers,
                verify=False
            )
            data = response.json()
            
            if data.get('code') == 200:
                history_data = data.get('data', {}).get('mpEstimateHisVos', [])
                if history_data:
                    # 转换为DataFrame
                    df = pd.DataFrame(history_data)
                    # 重命名列
                    df = df.rename(columns={
                        'estimateDate': 'date',
                        'estimateDiscount': 'discount',
                        'estimateNetValue': 'net_value'
                    })
                    # 转换日期格式
                    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                    # 转换数值类型
                    df['discount'] = pd.to_numeric(df['discount'], errors='coerce')
                    return df
            
            print(f"获取{fund_code}历史溢价率失败")
            return pd.DataFrame()
            
        except Exception as e:
            print(f"获取{fund_code}历史溢价率时发生错误: {e}")
            return pd.DataFrame()

    def get_combined_data(self, code, fund_name, fund_type):
        """获取并合并基金数据"""
        try:
            # 获取历史溢价率数据
            df_discount = self.get_historical_discount(code, fund_name, fund_type)
            if df_discount.empty:
                print(f"未获取到{code}的溢价率数据")
                return None
                
            # 获取交易数据
            df_trade = self.stock_data.get_stock_hist_data_em(
                stock=code,
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),  # 只获取30天数据
                end_date=datetime.now().strftime('%Y%m%d'),
                data_type='D',
                count=30
            )
            
            # 选择需要的列并重命名
            df_trade = df_trade[['date', 'volume', '振幅', '换手率']].copy()
            df_trade = df_trade.rename(columns={
                '振幅': 'amplitude',
                '换手率': 'turnover'
            })
            
            # 合并数据
            df_combined = pd.merge(
                df_trade,
                df_discount[['date', 'discount']],
                on='date',
                how='inner'
            )
            
            # 计算滚动平均溢价率
            df_combined['discount_3d'] = df_combined['discount'].rolling(3).mean()
            df_combined['discount_30d'] = df_combined['discount'].rolling(30).mean()
            
            return df_combined
            
        except Exception as e:
            print(f"合并{code}数据时发生错误: {e}")
            return None

    def analyze_force(self, df):
        """分析主力资金状态"""
        # 计算基准（前5天平均）
        volume_base = df['volume'].rolling(5).mean().shift(1)
        amplitude_base = df['amplitude'].rolling(5).mean().shift(1)
        turnover_base = df['turnover'].rolling(5).mean().shift(1)
        
        # 计算比率
        df['volume_ratio'] = df['volume'] / volume_base
        df['amplitude_ratio'] = df['amplitude'] / amplitude_base
        df['turnover_ratio'] = df['turnover'] / turnover_base
        
        # 判断主力进场（指标放大但溢价率适中）
        force_in = (
            (df['volume_ratio'] > 2) & 
            (df['amplitude_ratio'] > 2) & 
            (df['turnover_ratio'] > 2) & 
            (abs(df['discount_3d']) < abs(df['discount_30d']) * 1.2)
        )
        
        # 判断主力离场（指标缩小且溢价率显著放大）
        force_out = (
            (df['volume_ratio'].rolling(3).mean() < 1) & 
            (df['amplitude_ratio'].rolling(3).mean() < 1) & 
            (df['turnover_ratio'].rolling(3).mean() < 1) & 
            (abs(df['discount_3d']) > abs(df['discount_30d']) * 1.5)
        )
        
        return force_in, force_out

    def generate_html_report(self, results):
        """生成HTML报告"""
        html = """
        <html>
        <head>
            <style>
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid black; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .force-in { background-color: #90EE90; }
                .force-out { background-color: #FFB6C1; }
            </style>
        </head>
        <body>
            <h2>ETF主力资金跟踪报告</h2>
            <table>
                <tr>
                    <th>代码</th>
                    <th>名称</th>
                    <th>状态</th>
                    <th>日期</th>
                    <th>成交量比</th>
                    <th>振幅比</th>
                    <th>换手率比</th>
                    <th>溢价率(3日)</th>
                    <th>溢价率(30日)</th>
                </tr>
        """
        
        for result in results:
            html += f"""
                <tr class="{result['status']}">
                    <td>{result['code']}</td>
                    <td>{result['name']}</td>
                    <td>{result['status_text']}</td>
                    <td>{result['date']}</td>
                    <td>{result['volume_ratio']:.2f}</td>
                    <td>{result['amplitude_ratio']:.2f}</td>
                    <td>{result['turnover_ratio']:.2f}</td>
                    <td>{result['discount_3d']:.2f}%</td>
                    <td>{result['discount_30d']:.2f}%</td>
                </tr>
            """
            
        html += """
            </table>
        </body>
        </html>
        """
        return html

    def send_alert(self, message):
        """发送紧急提醒"""
        try:
            encoded_msg = urllib.parse.quote(message)
            url = f"{self.urgent_fwalert_url}?message={encoded_msg}"
            response = requests.get(url, verify=False)
            response.raise_for_status()
            print(f"Alert sent: {message}")
        except Exception as e:
            print(f"Failed to send alert: {e}")

    def send_wxpusher(self, content, content_type=1):
        """发送WxPusher消息"""
        data = {
            "appToken": self.wxpusher_token,
            "content": content,
            "contentType": content_type,  # 1=文本, 2=HTML
            "topicIds": [123],  # 您的主题ID
            "url": ""  # 可选的跳转链接
        }
        
        try:
            response = requests.post(self.wxpusher_url, json=data)
            response.raise_for_status()
            print("WxPusher消息发送成功")
        except Exception as e:
            print(f"WxPusher消息发送失败: {e}")

    def xiaoyu_get_list(self):
        """获取ETF基金列表及溢价率"""
        try:
            response = requests.get(
                'http://xiaoyudecqg.cn/htl/mp/api/arbitrage/list?type=4',  # 修改为正确的API endpoint
                headers=self.headers,
                verify=False
            )
            data = response.json()
            
            if data.get('code') == 200:
                etf_list = data.get('data', [])
                if etf_list:
                    df = pd.DataFrame(etf_list)
                    # 确保必要的列存在
                    required_columns = ['fundCode', 'fundName', 'type']
                    if all(col in df.columns for col in required_columns):
                        return df
                    else:
                        print("Missing required columns in ETF list data")
                        return pd.DataFrame()
                        
            elif data.get('code') == -999:  # Token过期
                print("Token expired, attempting to refresh...")
                if self.refresh_token():
                    return self.xiaoyu_get_list()
                    
            print(f"获取ETF列表失败: {data}")
            print(pd.DataFrame())
            return pd.DataFrame()
            
        except Exception as e:
            print(f"获取ETF列表时发生错误: {e}")
            return pd.DataFrame()

    def run(self):
        """主运行函数"""
        # 获取ETF列表
        df_list = self.xiaoyu_get_list()
        if df_list.empty:
            print("获取ETF列表失败")
            return
            
        results = []
        for _, fund in df_list.iterrows():
            try:
                print(f"处理基金: {fund['fundCode']} - {fund['fundName']}")
                df = self.get_combined_data(
                    fund['fundCode'],
                    fund['fundName'],
                    fund['type']
                )
                
                if df is None:
                    continue
                    
                force_in, force_out = self.analyze_force(df)
                
                # 检查最近5天的状态
                recent_df = df.tail(5)
                recent_force_in = force_in.tail(5)
                recent_force_out = force_out.tail(5)
                
                if recent_force_in.any() or recent_force_out.any():
                    for idx, row in recent_df.iterrows():
                        if force_in.loc[idx] or force_out.loc[idx]:
                            status = 'force-in' if force_in.loc[idx] else 'force-out'
                            status_text = '主力进场' if force_in.loc[idx] else '主力离场'
                            
                            # 如果是最新一天的数据，发送紧急提醒
                            if idx == df.index[-1]:
                                urgent_msg = (
                                    f"ETF: {fund['fundCode']} - {fund['fundName']}\n"
                                    f"状态: {status_text}\n"
                                    f"日期: {row['date']}\n"
                                    f"成交量比: {row['volume_ratio']:.2f}\n"
                                    f"振幅比: {row['amplitude_ratio']:.2f}\n"
                                    f"换手率比: {row['turnover_ratio']:.2f}\n"
                                    f"溢价率(3日): {row['discount_3d']:.2f}%\n"
                                    f"溢价率(30日): {row['discount_30d']:.2f}%"
                                )
                                self.send_alert(urgent_msg)
                            
                            results.append({
                                'code': fund['fundCode'],
                                'name': fund['fundName'],
                                'status': status,
                                'status_text': status_text,
                                'date': row['date'],
                                'volume_ratio': row['volume_ratio'],
                                'amplitude_ratio': row['amplitude_ratio'],
                                'turnover_ratio': row['turnover_ratio'],
                                'discount_3d': row['discount_3d'],
                                'discount_30d': row['discount_30d']
                            })
                
                # 避免请求过于频繁
                time.sleep(1)
                
            except Exception as e:
                print(f"处理{fund['fundCode']}时发生错误: {e}")
                continue
                
        # 生成并发送HTML报告
        if results:
            html_report = self.generate_html_report(results)
            self.send_wxpusher(html_report, content_type=2)

if __name__ == "__main__":
    tracker = ETFTracker()
    tracker.run()
