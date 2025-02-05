import time
import jwt
import uuid
import requests
import urllib3
import random
import string

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TokenGenerator:
    def __init__(self):
        self.base_url = "http://xiaoyudecqg.cn/htl/mp/api"
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'http://xiaoyudecqg.cn',
            'Referer': 'http://xiaoyudecqg.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

    def generate_code(self):
            """按照JS逻辑生成code"""
            # 获取当前时间戳
            timestamp = int(time.time() * 1000)  # 毫秒级时间戳
            
            # 生成session信息
            session_info = {
                'timestamp': timestamp,
                'nonce': ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            }
            
            # 使用相同的加密算法
            message = f"{timestamp}_{session_info['nonce']}"
            code_hash = hashlib.sha256(message.encode()).hexdigest()
            
            # 构造最终的code
            code = f"{code_hash[:5]}{session_info['nonce']}{code_hash[13:18]}"
            
            # 确保总长度为32位
            if len(code) < 32:
                code += ''.join(random.choices(string.ascii_letters + string.digits, k=32-len(code)))
            
            return code[:32]
    def generate_token(self):
        """生成token"""
        now = int(time.time())
        device_id = str(uuid.uuid4())
        
        payload = {
            "id": device_id,
            "openId": f"mp_user_{device_id[:8]}",
            "subscribe": "1",
            "uuid": device_id,
            "iat": now,
            "exp": now + 86400  # 24小时过期
        }
        
        token = jwt.encode(
            payload,
            'xiaoyudecqg_secret_key_2024',
            algorithm='HS512',
            headers={
                "typ": "JWT",
                "alg": "HS512",
                "kid": "xiaoyu-2024"
            }
        )
        
        return token

    def login(self):
        """执行登录流程"""
        try:
            json_data = {
                'code': self.generate_code(),
                'token': self.generate_token()
            }
            
            print(f"生成的code: {json_data['code']}")  # 打印生成的code
            print(f"生成的token: {json_data['token'][:30]}...")  # 打印token的前30个字符
            
            response = requests.post(
                f'{self.base_url}/unAuth/login',
                headers=self.headers,
                json=json_data,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    new_token = data.get('data')
                    print(f"登录成功，获取新token: {new_token}")
                    return new_token
                else:
                    print(f"登录失败，错误信息: {data}")
            else:
                print(f"登录请求失败，状态码: {response.status_code}")
                
            return None
            
        except Exception as e:
            print(f"登录过程出错: {e}")
            return None

def main():
    """主函数"""
    generator = TokenGenerator()
    token = generator.login()
    if token:
        print(f"当前可用token: {token[:30]}...")
    else:
        print("获取token失败")

if __name__ == "__main__":
    main()