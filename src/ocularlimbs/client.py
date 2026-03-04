"""
OcularLimbs 客户端 - 极简 API
让 AI 可以直接使用
"""

import sys
import os
import subprocess
import atexit
import time
import socket

# 服务配置
_SERVICE_PORT = 8848
_SERVICE_HOST = 'localhost'
_service_process = None


def _ensure_service():
    """确保服务在运行（自动启动）"""
    global _service_process

    # 检查服务是否已运行
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((_SERVICE_HOST, _SERVICE_PORT))
        sock.close()

        if result == 0:
            return True
    except:
        pass

    # 服务未运行，尝试启动
    try:
        # 尝试通过模块启动服务
        _service_process = subprocess.Popen(
            [sys.executable, "-m", "ocularlimbs.service", "--daemon"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 等待服务就绪
        for _ in range(10):
            time.sleep(0.5)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((_SERVICE_HOST, _SERVICE_PORT))
                sock.close()
                if result == 0:
                    atexit.register(_cleanup)
                    return True
            except:
                pass
    except:
        pass

    return False


def _cleanup():
    """清理：停止服务"""
    global _service_process
    if _service_process:
        try:
            _service_process.terminate()
            _service_process.wait(timeout=2)
        except:
            pass
        _service_process = None


def _api_call(method, endpoint, data=None):
    """统一的 API 调用"""
    import requests

    # 确保服务运行
    if not _ensure_service():
        return {'success': False, 'error': '服务无法启动'}

    url = f"http://{_SERVICE_HOST}:{_SERVICE_PORT}/api{endpoint}"

    try:
        if method == 'GET':
            response = requests.get(url, params=data, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=30)
        else:
            return {'success': False, 'error': '不支持的 HTTP 方法'}

        return response.json()
    except Exception as e:
        return {'success': False, 'error': str(e)}


def see():
    """
    查看屏幕

    Returns:
        dict: 屏幕信息
        {
            'width': 屏幕宽度,
            'height': 屏幕高度,
            'texts': 识别到的文字数量,
            'summary': 简短描述
        }

    Example:
        >>> screen = see()
        >>> print(f"屏幕: {screen['width']}x{screen['height']}")
    """
    result = _api_call('GET', '/see')
    if result.get('success'):
        return {
            'width': result.get('screen_width', 0),
            'height': result.get('screen_height', 0),
            'texts': result.get('text_count', 0),
            'summary': result.get('summary', ''),
            'elements': result.get('elements', [])
        }
    return result


def capture(filename=None, compression='balanced'):
    """
    捕获屏幕并保存

    Args:
        filename: 保存的文件名（可选）
        compression: 压缩预设 (ultra_fast/fast/balanced/quality/archival)

    Returns:
        dict: 捕获结果

    Example:
        >>> capture()  # 只捕获
        >>> capture('test.png')  # 保存到文件
    """
    params = {}
    if filename:
        params['save'] = filename
    if compression:
        params['compression'] = compression

    return _api_call('GET', '/capture', params)


def find_text(text):
    """
    在屏幕上查找文字

    Args:
        text: 要查找的文字

    Returns:
        dict: 查找结果
        {
            'found': 是否找到,
            'text': 找到的文字,
            'x': 中心X坐标,
            'y': 中心Y坐标
        }

    Example:
        >>> result = find_text("确定")
        >>> if result['found']:
        >>>     click(result['x'], result['y'])
    """
    result = _api_call('GET', '/find', {'text': text})

    if result.get('success') and result.get('found'):
        bbox = result.get('bbox', {})
        return {
            'found': True,
            'text': text,
            'x': bbox.get('x', 0) + bbox.get('width', 0) // 2,
            'y': bbox.get('y', 0) + bbox.get('height', 0) // 2,
            'bbox': bbox
        }

    return {'found': False, 'error': result.get('error')}


def click(x, y):
    """
    点击屏幕坐标

    Args:
        x: X坐标
        y: Y坐标

    Returns:
        bool: 是否成功

    Example:
        >>> click(100, 200)
    """
    result = _api_call('POST', '/click', {'x': x, 'y': y})
    return result.get('success', False)


def click_text(text):
    """
    查找并点击文字

    Args:
        text: 要查找并点击的文字

    Returns:
        bool: 是否成功

    Example:
        >>> click_text("确定")
    """
    result = find_text(text)
    if result.get('found'):
        return click(result['x'], result['y'])
    return False


def type_text(text):
    """
    输入文本

    Args:
        text: 要输入的文本

    Returns:
        bool: 是否成功

    Example:
        >>> type_text("Hello World")
    """
    result = _api_call('POST', '/type', {'text': text})
    return result.get('success', False)


def press_key(key):
    """
    按键

    Args:
        key: 按键名称（如 'enter', 'escape', 'f1'）

    Returns:
        bool: 是否成功

    Example:
        >>> press_key('enter')
    """
    return type_text(key)


def execute(goal):
    """
    执行任务（自然语言描述）

    Args:
        goal: 任务描述

    Returns:
        dict: 执行结果

    Example:
        >>> execute("打开计算器")
    """
    return _api_call('POST', '/execute', {'goal': goal})
