- 新增
    - 实现llm聊天功能
    - 前后端分离：使用fastapi
    - npm run back: 开启前端
    - npm run front：开启后端
    - npm run all：开启前后端
    - 每个文件不能超过1000行
- 新增
    - 后端关闭
- 新增
    - 前后端增加模型下载，可以显示下载进度
    - 在config.py可以添加一个下载列表为默认配置
        [ "https://modelscope.cn/models/second-state/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/Qwen2.5-0.5B-Instruct-Q4_0.gguf", "https://modelscope.cn/models/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf"]
- 新增
    - ChatPage有两种模式，一种是点击新对话进入Page，不是用来聊天的，是用来创建会话，并跳转到会话历史对应的ChatPage界面，另一种是点击历史对话，跳转到会话历史对应的界面
- 新增
    - 使用sse，后端向前端通信，当连接建立时，服务器应立即发送当前的最新数据，保证前端能得到第一次的数据。这里说的数据是session.db的数据，后面如果session.db更新，就通知前端，触发这个内容的重新渲染，你觉得可行吗，我是小白，只是猜想。说的是      {/* 会话列表 */}
      <div className="sidebar-sessions">
        <SessionList
          currentSessionId={currentSessionId}
          onSessionSelect={handleSessionSelect}
          onNewChat={handleNewChat}
        />
      </div>