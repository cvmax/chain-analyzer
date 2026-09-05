"""
HTTP 工具模块 - 代理感知的请求会话
"""
import os
import requests

# Python requests 默认读取 HTTP_PROXY/HTTPS_PROXY 环境变量
# 不强制设置代理，让 requests 自动处理


def http_get(url, params=None, headers=None, timeout=10):
    """带超时的 GET 请求"""
    return requests.get(url, params=params, headers=headers, timeout=timeout)