"""LLM 大模型对话服务"""
from typing import AsyncGenerator
from openai import AsyncOpenAI
from config import settings

# 初始化 OpenAI 兼容客户端（DeepSeek / Qwen 等）
client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
)

# 系统角色提示词
SYSTEM_PROMPT_BASE = """You are a friendly, patient English teacher for a Chinese 3rd-grade primary school student.
Teaching rules:
1. Use very simple English words and short sentences suitable for a 9-year-old beginner.
2. Be encouraging and positive. Never criticize directly.
3. When the student makes a mistake, gently repeat the correct expression instead of pointing out the error.
4. If the student speaks in Chinese, reply in English first, then give a simple Chinese explanation.
5. Keep each response under 3 sentences for easy understanding.
6. Use emoji occasionally to make it fun and engaging. 😊"""


def build_system_prompt(memory_context: str) -> str:
    """根据用户记忆构建 System Prompt"""
    prompt = SYSTEM_PROMPT_BASE
    if memory_context:
        prompt += f"\n\nStudent profile (use this to personalize teaching):\n{memory_context}"
    return prompt


def build_memory_context(memory_records: list) -> str:
    """将记忆记录转为可注入的文本上下文"""
    parts = {
        "vocab_mastered": [],
        "vocab_weak": [],
        "grammar_weak": [],
        "pronunciation_issue": [],
        "learning_preference": [],
        "interest_topic": [],
    }

    for record in memory_records:
        key = record.memory_type
        if key in parts:
            parts[key].append(record.memory_key)

    lines = []
    if parts["vocab_mastered"]:
        lines.append(f"- Words student knows well: {', '.join(parts['vocab_mastered'][:20])}")
    if parts["vocab_weak"]:
        lines.append(f"- Words student needs practice: {', '.join(parts['vocab_weak'][:20])}")
    if parts["grammar_weak"]:
        lines.append(f"- Grammar points to reinforce: {', '.join(parts['grammar_weak'])}")
    if parts["pronunciation_issue"]:
        lines.append(f"- Pronunciation to watch: {', '.join(parts['pronunciation_issue'])}")
    if parts["interest_topic"]:
        lines.append(f"- Student's interests: {', '.join(parts['interest_topic'])}")

    return "\n".join(lines) if lines else ""


async def chat_stream(
    messages: list[dict],
    memory_context: str = "",
) -> AsyncGenerator[str, None]:
    """流式对话"""
    system_prompt = build_system_prompt(memory_context)
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    stream = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=full_messages,
        temperature=0.7,
        max_tokens=200,
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def chat(messages: list[dict], memory_context: str = "") -> str:
    """非流式对话"""
    system_prompt = build_system_prompt(memory_context)
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=full_messages,
        temperature=0.7,
        max_tokens=200,
    )

    return response.choices[0].message.content or ""


async def evaluate_pronunciation(
    target_sentence: str,
    user_transcript: str,
) -> dict:
    """评估发音（基于文本对比 + LLM辅助评分）"""
    prompt = f"""You are an English pronunciation evaluator for kids.
Target sentence: "{target_sentence}"
Student said: "{user_transcript}"

Evaluate and return a JSON object with:
- accuracy: 0-100 score for word pronunciation accuracy
- fluency: 0-100 score for natural flow
- completeness: 0-100 score for how complete the sentence is
- feedback: a short encouraging comment in Chinese (1 sentence, use emoji)

Return ONLY valid JSON, no other text."""

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200,
        response_format={"type": "json_object"},
    )

    import json
    content = response.choices[0].message.content or "{}"
    return json.loads(content)
