"""
HTTP 服务器模块 - 提供 OCR API
"""
import logging
from flask import Flask, request, jsonify
from ocr_engine import ocr_from_base64
from config import config

# 配置日志
# 获取 logger (配置由主程序统一管理)
logger = logging.getLogger("ocr_server")

app = Flask(__name__)

# 禁用 Flask 默认日志 (verbose)
flask_log = logging.getLogger('werkzeug')
flask_log.setLevel(logging.ERROR)

# 回调函数，用于通知菜单栏应用状态变化
_status_callback = None
_processing = False


def set_status_callback(callback):
    """设置状态回调"""
    global _status_callback
    _status_callback = callback


def notify_status(is_processing: bool):
    """通知状态变化"""
    global _processing
    _processing = is_processing
    if _status_callback:
        _status_callback(is_processing)


@app.route('/ocr', methods=['POST', 'OPTIONS'])
def ocr_endpoint():
    """OCR API 端点"""
    # 处理 CORS 预检请求
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        notify_status(True)
        
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': '缺少图片数据'}), 400
        
        base64_image = data['image']
        mode = config.mode
        
        # 执行 OCR
        texts, language = ocr_from_base64(base64_image, mode)
        
        # 更新统计
        config.increment_count()
        
        logger.info(f"OCR 成功: {len(texts)} 行文本, 语言: {language}")
        
        response = jsonify({
            'texts': texts,
            'from': language
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"OCR 错误: {str(e)}")
        response = jsonify({'error': str(e)})
        response.status_code = 500
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    finally:
        notify_status(False)


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'ok', 'port': config.port})


@app.route('/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    stats = config.get_stats()
    return jsonify(stats)


def run_server(port: int = None):
    """运行服务器"""
    if port is None:
        port = config.port
    
    logger.info(f"启动 OCR 服务器，端口: {port}")
    app.run(host='0.0.0.0', port=port, threaded=True, use_reloader=False)


def run_server_threaded(port: int = None):
    """在线程中运行服务器"""
    import threading
    
    if port is None:
        port = config.port
    
    server_thread = threading.Thread(
        target=lambda: app.run(
            host='0.0.0.0',
            port=port,
            threaded=True,
            use_reloader=False
        ),
        daemon=True
    )
    server_thread.start()
    logger.info(f"OCR 服务器线程已启动，端口: {port}")
    return server_thread
