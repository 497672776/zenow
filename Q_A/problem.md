## Q: 为什么不能前端看不到流式回答
A: 后端的流式问答不是异步的

  你的后端使用的是同步的 requests 库，而 airag_knowledge_base 使用的是异步的 httpx 库。

  requests.iter_content() 即使设置 chunk_size=1，底层仍然会有缓冲，导致数据不是真正的流式传输。

  修改内容

  1. /home/liudecheng/zenow-test/zenow/backend/src/model/llm.py
    - 添加 import httpx
    - 添加 AsyncIterator 类型
    - 新增 async_stream_chat_completion() 异步方法，使用 httpx.AsyncClient 和 aiter_lines() 实现真正的流式传输
    - 修改 chat_completion() 为同步版本（非流式）
  2. /home/liudecheng/zenow-test/zenow/backend/src/main.py
    - 修改 /api/chat 端点，使用新的 async_stream_chat_completion() 方法
  3. /home/liudecheng/zenow-test/zenow/backend/pyproject.toml
    - 添加 httpx>=0.25.0 依赖

  关键差异

  旧代码（同步 + 缓冲）：
  response = requests.post(url, json=payload, stream=True, timeout=300)
  for chunk in response.iter_content(chunk_size=1):  # ❌ 仍然会缓冲
      ...

  新代码（异步 + 真正流式）：
  async with httpx.AsyncClient(timeout=300.0) as client:
      async with client.stream("POST", url, json=payload) as response:
          async for line in response.aiter_lines():  # ✅ 真正的流式传输
              ...