"""
公共 AI 调用模块
统一封装 DeepSeek API 调用，提供超时和自动重试机制

所有需要调用大模型的服务（analyzer / matcher / detail_service）
都通过此模块的 call_deepseek() 函数发起请求，避免重复代码。
"""
import logging
from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 模块级单例客户端
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """获取或创建 OpenAI 客户端单例"""
    global _client
    if _client is None:
        settings = get_settings()
        _client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    return _client


def call_deepseek(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    label: str = "DeepSeek API",
) -> str:
    """
    调用 DeepSeek API，带 30 秒超时和 1 次自动重试。

    行为：
    - 单次调用超时时间 30 秒（连接 10 秒 + 读取 30 秒）
    - 超时 / 网络错误 / 服务端 5xx 自动重试 1 次（总共最多 2 次调用）
    - 重试时记录日志
    - 两次均失败则抛出 RuntimeError，附带友好提示

    Args:
        system_prompt: 系统 Prompt
        user_prompt: 用户 Prompt
        temperature: 温度参数（0~1，越低越确定）
        max_tokens: 最大输出 token 数
        label: 日志标签（用于区分调用来源）

    Returns:
        API 返回的文本内容（response.choices[0].message.content）

    Raises:
        RuntimeError: 两次调用均失败
    """
    client = _get_client()
    settings = get_settings()
    model = settings.deepseek_model

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_error: str = ""

    for attempt in range(2):  # 总共最多 2 次（初次 + 1 次重试）
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=30.0,  # 连接 + 读取总超时
            )
            content = response.choices[0].message.content or ""
            logger.info(f"[{label}] 调用成功, 长度={len(content)}")
            return content

        except Exception as e:
            last_error = str(e)
            if attempt == 0:
                logger.warning(
                    f"[{label}] DeepSeek API 调用失败，正在重试... "
                    f"错误: {e}"
                )
            else:
                logger.error(
                    f"[{label}] DeepSeek API 重试后仍然失败，"
                    f"已用尽 2 次尝试。错误: {e}"
                )

    # 两次均失败
    raise RuntimeError("AI 分析服务响应较慢，请稍后重试")
