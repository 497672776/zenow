"""
Token estimation utilities for chat messages
使用简单的字符计数方法估算 token 数量
"""
import re
from typing import List, Dict, Any


class TokenEstimator:
    """
    Token 估算器

    使用简化的规则估算 token 数量：
    - 中文字符：每个字符约 1.5-2 tokens
    - 英文单词：每个单词约 1-1.5 tokens
    - 标点符号：每个约 1 token

    这是一个近似估算，实际 token 数可能有 10-20% 的误差
    """

    def __init__(self):
        """初始化 token 估算器"""
        # 中文字符的 token 系数（每个中文字符约等于多少 token）
        self.chinese_char_ratio = 1.8

        # 英文单词的 token 系数（每个英文单词约等于多少 token）
        self.english_word_ratio = 1.3

        # 标点符号和特殊字符的 token 系数
        self.punctuation_ratio = 1.0

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 数量

        Args:
            text: 要估算的文本

        Returns:
            估算的 token 数量
        """
        if not text:
            return 0

        # 统计中文字符数量（包括中文标点）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', text))

        # 统计英文单词数量
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))

        # 统计数字
        numbers = len(re.findall(r'\d+', text))

        # 统计其他字符（标点、空格等）
        other_chars = len(text) - chinese_chars - len(re.findall(r'[a-zA-Z\d]', text))

        # 计算总 token 数
        total_tokens = (
            chinese_chars * self.chinese_char_ratio +
            english_words * self.english_word_ratio +
            numbers * 0.5 +  # 数字通常较短
            other_chars * self.punctuation_ratio
        )

        # 向上取整
        return int(total_tokens) + 1

    def estimate_message_tokens(self, role: str, content: str) -> int:
        """
        估算单条消息的 token 数量（包括角色标记的开销）

        Args:
            role: 角色 ('user', 'assistant', 'system')
            content: 消息内容

        Returns:
            估算的 token 数量
        """
        # 基础内容 token
        content_tokens = self.estimate_tokens(content)

        # 角色标记的开销（OpenAI 格式约 4 tokens per message）
        # {"role": "user", "content": "..."}
        role_overhead = 4

        return content_tokens + role_overhead

    def estimate_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        估算多条消息的总 token 数量

        Args:
            messages: 消息列表，每条消息包含 'role' 和 'content'

        Returns:
            估算的总 token 数量
        """
        total = 0
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            total += self.estimate_message_tokens(role, content)

        # 添加对话格式的额外开销（约 3 tokens）
        total += 3

        return total

    def estimate_with_system_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str
    ) -> int:
        """
        估算包含系统提示词的总 token 数量

        Args:
            messages: 消息列表
            system_prompt: 系统提示词

        Returns:
            估算的总 token 数量
        """
        # 系统提示词的 token
        system_tokens = self.estimate_message_tokens('system', system_prompt)

        # 消息的 token
        messages_tokens = self.estimate_messages_tokens(messages)

        return system_tokens + messages_tokens


# 全局单例
_estimator = TokenEstimator()


def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量（便捷函数）

    Args:
        text: 要估算的文本

    Returns:
        估算的 token 数量
    """
    return _estimator.estimate_tokens(text)


def estimate_message_tokens(role: str, content: str) -> int:
    """
    估算单条消息的 token 数量（便捷函数）

    Args:
        role: 角色 ('user', 'assistant', 'system')
        content: 消息内容

    Returns:
        估算的 token 数量
    """
    return _estimator.estimate_message_tokens(role, content)


def estimate_messages_tokens(messages: List[Dict[str, str]]) -> int:
    """
    估算多条消息的总 token 数量（便捷函数）

    Args:
        messages: 消息列表

    Returns:
        估算的总 token 数量
    """
    return _estimator.estimate_messages_tokens(messages)


def estimate_with_system_prompt(
    messages: List[Dict[str, str]],
    system_prompt: str
) -> int:
    """
    估算包含系统提示词的总 token 数量（便捷函数）

    Args:
        messages: 消息列表
        system_prompt: 系统提示词

    Returns:
        估算的总 token 数量
    """
    return _estimator.estimate_with_system_prompt(messages, system_prompt)
