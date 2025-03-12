import requests
from flask import current_app
import json

class AIService:
    def __init__(self):
        self.api_key = current_app.config['SILICONFLOW_API_KEY']
        self.api_url = current_app.config['SILICONFLOW_API_URL']
        self.model = current_app.config['SILICONFLOW_MODEL']

    def get_chat_response(self, messages):
        
        # 添加调试日志
        current_app.logger.debug(f"当前系统提示词: {current_app.config.get('SYSTEM_PROMPT')}")
        
        # 确保 messages 是列表
        if not isinstance(messages, list):
            messages = [{"role": "user", "content": messages}]
        
        # 强制替换或添加系统提示
        system_message = {
            "role": "system",
            "content": current_app.config['SYSTEM_PROMPT']
        }
        
        # 移除任何现有的系统消息
        messages = [msg for msg in messages if msg.get('role') != 'system']
        # 在开头添加新的系统消息
        messages.insert(0, system_message)
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "stream": False,
            "max_tokens": current_app.config['MAX_TOKENS']
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "stream": False,
            "max_tokens": current_app.config['MAX_TOKENS']
        }
        
        try:
            current_app.logger.info(f"发送到硅基流动API的请求: {json.dumps(data, ensure_ascii=False)}")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=60  # 设置超时时间
            )
            
            current_app.logger.info(f"硅基流动API响应状态码: {response.status_code}")
            current_app.logger.info(f"硅基流动API响应内容: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                raise ValueError("API响应中没有choices字段")
                
            if 'message' not in result['choices'][0]:
                raise ValueError("API响应中没有message字段")
                
            if 'content' not in result['choices'][0]['message']:
                raise ValueError("API响应中没有content字段")
                
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"API请求错误: {str(e)}")
            if hasattr(e.response, 'text'):
                current_app.logger.error(f"API错误响应: {e.response.text}")
            return "抱歉，我现在无法回答。请稍后再试。"
            
        except (KeyError, json.JSONDecodeError, ValueError) as e:
            current_app.logger.error(f"API响应解析错误: {str(e)}")
            return "抱歉，处理响应时出现错误。"
            
        except Exception as e:
            current_app.logger.error(f"未预期的错误: {str(e)}")
            return "抱歉，发生了未知错误。"
    
    def get_chat_response_stream(self, messages):
        """流式获取聊天响应"""
        # 添加调试日志
        current_app.logger.debug(f"当前系统提示词: {current_app.config.get('SYSTEM_PROMPT')}")
        
        # 确保 messages 是列表
        if not isinstance(messages, list):
            messages = [{"role": "user", "content": messages}]
        
        # 强制替换或添加系统提示
        system_message = {
            "role": "system",
            "content": current_app.config['SYSTEM_PROMPT']
        }
        
        # 移除任何现有的系统消息
        messages = [msg for msg in messages if msg.get('role') != 'system']
        # 在开头添加新的系统消息
        messages.insert(0, system_message)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "stream": True,  # 启用流式输出
            "max_tokens": current_app.config['MAX_TOKENS']
        }
        
        try:
            current_app.logger.info(f"发送到硅基流动API的流式请求: {json.dumps(data, ensure_ascii=False)}")
            
            # 使用会话管理连接
            with requests.Session() as session:
                response = session.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=60,  # 设置超时时间
                    stream=True  # 启用流式响应
                )
                
                response.raise_for_status()
                
                # 逐行处理流式响应
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            try:
                                line_data = line[6:]  # 去掉 'data: ' 前缀
                                if line_data == "[DONE]":
                                    break
                                    
                                json_data = json.loads(line_data)
                                if 'choices' in json_data and json_data['choices']:
                                    delta = json_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        yield content  # 逐步返回内容
                            except json.JSONDecodeError:
                                continue
        
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"API请求错误: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                current_app.logger.error(f"API错误响应: {e.response.text}")
            yield "抱歉，我现在无法回答。请稍后再试。"
            
        except Exception as e:
            current_app.logger.error(f"未预期的错误: {str(e)}")
            yield "抱歉，发生了未知错误。"