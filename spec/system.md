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
- 新增
    - 做完ui，分析怎么做后端，文件上传相关用minio服务，先实现md、txt、pdf的上传即可
    - 后台启动要先启动minio服务，/home/liudecheng/zenow-test/zenow/backend/spacemit_llm/comon/minio.py
    - 知识库名、简介、描述用数据库保存，可以用,后台服务组件写在：/home/liudecheng/zenow-test/zenow/backend/spacemit_llm/comon/sqlite/sqlit_kb.py
    - 知识库里面有什么文件，文件上传时间等也是在sqlit_kb.py里面写，所以你要做几个表，一个是知识库列表，一个是每个知识库详情。
    - 同个名字的文件上传就是覆盖，然后更新文件上传时间即可
- 新增
    - rag的基本组件写在：/home/liudecheng/zenow-test/zenow/backend/spacemit_llm/rag，具体怎么写，我加了parser和splitter，你觉得不够可以继续加，然后使用import chromadb
    client = chromadb.Client()
    kb_docs = client.get_or_create_collection("kb_docs")
    kb_code = client.get_or_create_collection("kb_code")
    kb_faq  = client.get_or_create_collection("kb_faq")
    实现知识库
