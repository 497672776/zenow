
- 新增
    - 技术栈：python+uv管理python包
- 新增
    - zenow/backend/src/model/llm.py，写两个类，一个是llm server，一个是llm client，做的是如下功能
        ```
        llama-server -m ~/Qwen3-30B-A3B-Instruct-2507-Q4_0.gguf -t 8 --host 127.0.0.1 --port 8080 --ctx-size 15360 --n-gpu-layers 0 --batch-size 512 --metrics --no-mmap

        curl http://localhost:8080/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{
            "model": "qwen3",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "where is zhuhai?"},
                {"role": "assistant", "content": "Zhuhai is a city in Guangdong, China."},
                {"role": "user", "content": "What is it famous for?"}
            ]
        }'
        ``` 
    - llm server 要实现的是：
        - 模型切换，启动模型，如果模型使用的gguf有问题，要提示，server状态：模型名，模型状态（启动中，未启动，启动成功），添加可切换模型：可以添加gguf文件绝对路径，来增加目前可以切换模型列表，下载模型：提供gguf下载链接即可，
    - llm client 要实现的是：
        - 连接llm server的base_url,然后实现stream功能，可以接收messages作为输入，也可以控制参数，如 "temperature": 0.7,     "repeat_penalty": 1.1, 支持对话中断
    - zenow/backend/src/config.py 负责默认配置管理，默认配置都在这里写
    - zenow/backend/src/comon/sqlite/sqlite_base.py 负责数据库基类
    - zenow/backend/src/comon/sqlite/sqlite_config.py 负责配置相关的数据库类，如记录当前模型配置，参数，为了下次重启后端恢复配置
- 新增
    - zenow/backend/tests/llm_test.py 写个测试，验证llm功能，使用的是/home/liudecheng/Downloads/models里面两个模型进行测试 
- 新增
    - api 接口
        api/models/current	get	查看当前模型、是否已经下载、	mode（llm、embed、rerank）	
        api/models/list	get	查模型列表以及当前使用模型、是否已经下载	mode	模型名、模型是否下载、当前使用模型
        api/models/load	post	下载进度、模型切换	mode	下载进度条、
        api/models/download	post	下载模型	mode、模型名	
        api/models/get_param	get		mode	
        api/models/update_param	post		mode、模型名	
    - 下载目录：
        1. ~/.cache/zenow/models/llm/Qwen2.5-0.5B-Instruct-Q4_0.gguf：https://modelscope.cn/models/second-state/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/Qwen2.5-0.5B-Instruct-Q4_0.gguf
        2. ~/.cache/zenow/models/llm/Qwen3-0.6B-Q4_K_M.gguf：https://modelscope.cn/models/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf
        3. ~/.cache/zenow/models/embed/nomic-embed-text-v2-moe.Q4_0.gguf：https://hf-mirror.com/nomic-ai/nomic-embed-text-v2-moe-GGUF/resolve/main/nomic-embed-text-v2-moe.Q4_0.gguf
        4. ~/.cache/zenow/models/rerank/bge-reranker-v2-m3-Q4_0.gguf：https://modelscope.cn/models/gpustack/bge-reranker-v2-m3-GGUF/resolve/master/bge-reranker-v2-m3-Q4_0.gguf
    - 对应的：zenow-test/zenow/backend/src/config.py
        # Default model download URLs
        DEFAULT_MODEL_DOWNLOAD_URLS = [
            "https://modelscope.cn/models/second-state/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/Qwen2.5-0.5B-Instruct-Q4_0.gguf",
            "https://modelscope.cn/models/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf"
        ]
        也要改改
    - 用户可以启动三种模型，每种模型的llama-server进程都可以同时存在一个，相同类型的模型就是切换
- 新增
    - 加一个会话数据库，用来存聊天历史，并且可以实现多轮对话，即从会话数据库中取不超过config.db中 LLMServer 参数 :context_size的一半，每个聊天记录有token预估数，通过这个计算，获得不超过预期prompt长度，且保证会话历史完整性的历史消息，设计完告诉我你是怎么预估预估token数的，这个token预估也要包含系统提示词，系统提示词可以/home/liudecheng/zenow-test/zenow/backend/src/config.py里面加个变量，并且记录在config.db的llm_parameter表格中，在前端也可以修改
    - 你先定一下会话数据库的样式，/home/liudecheng/zenow-test/zenow/backend/src/comon/sqlite/sqlite_session.py,然后问下我是否合理，我觉得要有，会话更新时间，用于排序，会话中每个消息的token预估数，会话名，根据用户问题的前多少个字符来取
    - 支持中断，支持消息记录到会话历史，选择会话，可以获得该消息列表，来让用户重新继续对话
    - 消息列表显示在sidebar历史聊天下面，支持会话名的修改，具体设计ui参考/home/liudecheng/airag_knowledge_base_test/airag_knowledge_base/src/renderer/components/HistoryPage.tsx，以及/home/liudecheng/airag_knowledge_base_test/airag_knowledge_base/src/renderer/components/Sidebar.tsx  {/* Chat group - 严格按照 DESIGN_SPEC.md 第5-6节 */}， 你觉得什么适合做成component你就做。
    - 现在新对话只是负责获得用户问题，然后创建会话，并跳转到对应会话历史，继续对话
- 新增
    - config.py应该只在应用的顶层（main.py 和routers）使用，而不应该在底层的 pipeline 和 model模块中使用。
