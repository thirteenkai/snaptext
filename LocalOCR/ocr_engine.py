"""
OCR 引擎模块 - RapidOCR 封装
"""
import base64
import io
from typing import List, Tuple, Optional
from PIL import Image

# 延迟导入 RapidOCR 以加快启动速度
_ocr_engine = None


def get_ocr_engine():
    """获取 OCR 引擎实例（单例模式）"""
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        # 优化参数以提高精度
        _ocr_engine = RapidOCR(
            text_score=0.5,  # 文本置信度阈值（默认0.5）
            det_use_cuda=False,
            rec_use_cuda=False,
        )
    return _ocr_engine


def detect_language(text: str) -> str:
    """简单的语言检测"""
    if not text:
        return "auto"
    
    # 统计字符类型
    chinese_count = 0
    english_count = 0
    japanese_count = 0
    korean_count = 0
    
    for char in text:
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF:  # 中文
            chinese_count += 1
        elif 0x3040 <= code <= 0x30FF:  # 日文假名
            japanese_count += 1
        elif 0xAC00 <= code <= 0xD7AF:  # 韩文
            korean_count += 1
        elif 0x0041 <= code <= 0x007A:  # 英文字母
            english_count += 1
    
    # 确定主要语言
    counts = {
        "zh-Hans": chinese_count,
        "en": english_count,
        "ja": japanese_count,
        "ko": korean_count
    }
    
    max_lang = max(counts, key=counts.get)
    if counts[max_lang] > 0:
        return max_lang
    return "auto"


def process_image(image_data: bytes) -> Image.Image:
    """处理图片数据"""
    return Image.open(io.BytesIO(image_data))


def base64_to_image(base64_str: str) -> Image.Image:
    """Base64 转图片"""
    # 移除可能的 data URL 前缀
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    
    image_data = base64.b64decode(base64_str)
    return process_image(image_data)


def merge_lines_by_position(ocr_result: list) -> List[str]:
    """
    根据文本框的 Y 坐标位置智能合并同一行的文本
    
    同一行的文本用空格连接，不同行的文本分开
    """
    if not ocr_result:
        return []
    
    # 提取每个文本框的信息：(y_center, x_left, text)
    items = []
    for item in ocr_result:
        box = item[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        text = item[1]
        
        # 计算 Y 中心点（取四个点的平均值）
        y_center = sum(point[1] for point in box) / 4
        # 取左边缘的 X 坐标用于排序
        x_left = min(point[0] for point in box)
        # 计算文本框高度（用于判断行间距阈值）
        y_coords = [point[1] for point in box]
        height = max(y_coords) - min(y_coords)
        
        items.append({
            'y_center': y_center,
            'x_left': x_left,
            'text': text,
            'height': height
        })
    
    # 按 Y 坐标分组（Y 坐标接近的为同一行）
    # 阈值：文本框高度的一半
    items.sort(key=lambda x: (x['y_center'], x['x_left']))
    
    lines = []
    current_line = [items[0]]
    
    for item in items[1:]:
        # 判断是否为同一行：Y 坐标差小于当前行平均高度的一半
        avg_height = sum(i['height'] for i in current_line) / len(current_line)
        threshold = max(avg_height * 0.6, 10)  # 至少 10 像素
        
        if abs(item['y_center'] - current_line[0]['y_center']) < threshold:
            current_line.append(item)
        else:
            lines.append(current_line)
            current_line = [item]
    
    lines.append(current_line)
    
    # 每行内部按 X 坐标排序，然后用空格连接
    result = []
    for line in lines:
        line.sort(key=lambda x: x['x_left'])
        line_text = ' '.join(item['text'] for item in line)
        result.append(line_text)
    
    return result


def _ocr_image(image: Image.Image, mode: str = "accurate") -> Tuple[List[str], str]:
    """
    内部 OCR 处理函数
    """
    # 转换为 RGB 模式
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")
    
    # 执行 OCR
    ocr = get_ocr_engine()
    result, _ = ocr(image)
    
    if result is None:
        return [], "auto"
    
    # 智能合并同一行的文本
    texts = merge_lines_by_position(result)
    
    # 检测语言
    combined_text = " ".join(texts)
    language = detect_language(combined_text)
    
    return texts, language


def ocr_from_base64(base64_str: str, mode: str = "accurate") -> Tuple[List[str], str]:
    """
    从 Base64 图片进行 OCR
    """
    try:
        image = base64_to_image(base64_str)
        return _ocr_image(image, mode)
    except Exception as e:
        print(f"OCR 错误: {e}")
        raise


def ocr_from_file(file_path: str, mode: str = "accurate") -> Tuple[List[str], str]:
    """
    从文件进行 OCR
    """
    try:
        image = Image.open(file_path)
        return _ocr_image(image, mode)
    except Exception as e:
        print(f"OCR 错误: {e}")
        raise
