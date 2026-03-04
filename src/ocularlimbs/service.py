"""
OcularLimbs 后台服务
提供 HTTP API 供客户端调用
"""

import os
import sys
import argparse
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vision.capture import ScreenCapture
from vision.ocr import OCR
from action.mouse import MouseController
from action.keyboard import KeyboardController
from action.window import WindowController

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)

# 初始化控制器
capture = ScreenCapture()
ocr = OCR()
mouse = MouseController()
keyboard = KeyboardController()
window = WindowController()


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'OcularLimbs',
        'version': '1.0.0'
    })


@app.route('/api/see', methods=['GET'])
def see():
    """查看屏幕"""
    try:
        # 捕获屏幕
        screenshot = capture.capture()

        # OCR 识别
        text_result = ocr.recognize(screenshot)

        return jsonify({
            'success': True,
            'screen_width': screenshot.width,
            'screen_height': screenshot.height,
            'text_count': len(text_result.get('texts', [])),
            'summary': text_result.get('summary', ''),
            'elements': []
        })
    except Exception as e:
        logger.error(f"查看屏幕失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/capture', methods=['GET'])
def capture_screen():
    """捕获屏幕"""
    try:
        filename = request.args.get('save')
        compression = request.args.get('compression', 'balanced')

        # 捕获屏幕
        screenshot = capture.capture()

        result = {
            'success': True,
            'width': screenshot.width,
            'height': screenshot.height
        }

        # 保存文件
        if filename:
            from pathlib import Path
            save_path = Path(filename)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            screenshot.save(str(save_path))
            result['saved_to'] = str(save_path)
            result['size'] = save_path.stat().st_size

        return jsonify(result)
    except Exception as e:
        logger.error(f"捕获屏幕失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/find', methods=['GET'])
def find_text():
    """查找文字"""
    try:
        text = request.args.get('text', '')
        if not text:
            return jsonify({'success': False, 'error': '缺少 text 参数'})

        # 捕获屏幕
        screenshot = capture.capture()

        # OCR 识别
        text_result = ocr.recognize(screenshot)

        # 查找匹配的文字
        for item in text_result.get('texts', []):
            if text in item.get('text', ''):
                bbox = item.get('bbox', {})
                return jsonify({
                    'success': True,
                    'found': True,
                    'text': item.get('text'),
                    'bbox': bbox
                })

        return jsonify({'success': True, 'found': False})
    except Exception as e:
        logger.error(f"查找文字失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/click', methods=['POST'])
def click():
    """点击屏幕"""
    try:
        data = request.get_json()
        x = data.get('x')
        y = data.get('y')

        if x is None or y is None:
            return jsonify({'success': False, 'error': '缺少 x 或 y 参数'})

        mouse.click(x, y)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"点击失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/type', methods=['POST'])
def type_text():
    """输入文本"""
    try:
        data = request.get_json()
        text = data.get('text', '')

        keyboard.type(text)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"输入文本失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/execute', methods=['POST'])
def execute():
    """执行任务（简单实现）"""
    try:
        data = request.get_json()
        goal = data.get('goal', '')

        # 简单的任务解析（未来可以用 LLM 增强）
        result = {
            'success': True,
            'goal': goal,
            'message': '任务执行完成'
        }

        return jsonify(result)
    except Exception as e:
        logger.error(f"执行任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


def main():
    """启动服务"""
    parser = argparse.ArgumentParser(description='OcularLimbs 后台服务')
    parser.add_argument('--host', default='localhost', help='监听地址')
    parser.add_argument('--port', type=int, default=8848, help='监听端口')
    parser.add_argument('--daemon', action='store_true', help='后台运行模式')
    parser.add_argument('--debug', action='store_true', help='调试模式')

    args = parser.parse_args()

    if args.daemon:
        # 后台模式（简单实现，生产环境建议用专业的 daemon 库）
        import subprocess
        log_path = os.path.expanduser('~/.ocularlimbs/service.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        with open(log_path, 'a') as f:
            subprocess.Popen(
                [sys.executable, '-m', 'ocularlimbs.service',
                 '--host', args.host, '--port', str(args.port)],
                stdout=f,
                stderr=f
            )
        print(f"服务已在后台启动，日志: {log_path}")
        return

    logger.info(f"启动 OcularLimbs 服务: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == '__main__':
    main()
