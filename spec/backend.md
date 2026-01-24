
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
    - 