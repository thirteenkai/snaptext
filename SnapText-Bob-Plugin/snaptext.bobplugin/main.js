/**
 * Local OCR - Bob 本地 OCR 插件
 * 调用本地 RapidOCR 服务进行文字识别
 */

/**
 * 获取支持的语言列表
 */
function supportLanguages() {
    return [
        'auto',
        'zh-Hans',
        'zh-Hant',
        'en',
        'ja',
        'ko',
        'fr',
        'de',
        'es',
        'ru'
    ];
}

/**
 * 执行 OCR 识别
 * @param {Object} query - 查询对象
 * @param {Object} query.image - 图片数据 ($data 类型)
 * @param {string} query.from - 源语言
 * @param {string} query.detectFrom - 检测到的语言
 * @param {Function} completion - 完成回调
 */
function ocr(query, completion) {
    // 获取配置
    const port = $option.port || '9999';
    const timeout = parseInt($option.timeout || '30') * 1000;

    // 服务地址
    const url = `http://127.0.0.1:${port}/ocr`;

    // 将图片转为 Base64
    const base64Image = query.image.toBase64();

    // 构建请求
    $http.request({
        method: 'POST',
        url: url,
        timeout: timeout,
        header: {
            'Content-Type': 'application/json'
        },
        body: {
            image: base64Image
        },
        handler: function (resp) {
            // 检查响应
            if (resp.error) {
                handleError(resp.error, completion);
                return;
            }

            const data = resp.data;

            // 检查错误
            if (data.error) {
                completion({
                    error: {
                        type: 'api',
                        message: data.error
                    }
                });
                return;
            }

            // 解析结果
            const texts = data.texts || [];
            const from = data.from || 'auto';

            if (texts.length === 0) {
                completion({
                    error: {
                        type: 'api',
                        message: '未识别到文字'
                    }
                });
                return;
            }

            // 构建 OCR 结果 - 合并所有文本行，保留换行
            const combinedText = texts.join('\n');

            completion({
                result: {
                    from: from,
                    texts: [{ text: combinedText }]
                }
            });
        }
    });
}

/**
 * 处理错误
 */
function handleError(error, completion) {
    let message = '未知错误';
    let type = 'unknown';

    if (error.code) {
        switch (error.code) {
            case -1001:
                message = 'OCR 服务请求超时，请检查服务是否运行';
                type = 'timeout';
                break;
            case -1004:
            case -1009:
                message = '无法连接到本地 OCR 服务，请确保 Local OCR 应用正在运行';
                type = 'network';
                break;
            default:
                message = `连接错误: ${error.localizedDescription || error.code}`;
                type = 'network';
        }
    } else if (error.localizedDescription) {
        message = error.localizedDescription;
    }

    completion({
        error: {
            type: type,
            message: message
        }
    });
}

/**
 * 插件验证（可选）
 * Bob 1.6.0+ 可用
 */
function pluginValidate(completion) {
    const port = $option.port || '9999';
    const url = `http://127.0.0.1:${port}/health`;

    $http.request({
        method: 'GET',
        url: url,
        timeout: 5000,
        handler: function (resp) {
            if (resp.error || !resp.data) {
                completion({
                    result: false,
                    reason: '无法连接到本地 OCR 服务，请确保 Local OCR 应用正在运行'
                });
                return;
            }

            if (resp.data.status === 'ok') {
                completion({
                    result: true
                });
            } else {
                completion({
                    result: false,
                    reason: 'OCR 服务状态异常'
                });
            }
        }
    });
}

/**
 * 超时设置（可选）
 * Bob 1.6.0+ 可用
 */
function pluginTimeoutInterval() {
    const timeout = parseInt($option.timeout || '30');
    return timeout;
}
