目标                                                                                                                       
                                                                                                                            
 扩展 Zenow 支持三种模型模式：LLM、Embed、Rerank，每种模式独立管理模型和参数。                                              
                                                                                                                            
 核心变更                                                                                                                   
                                                                                                                            
 1. 数据库重构                                                                                                              
                                                                                                                            
 文件: backend/src/comon/sqlite/sqlite_config.py                                                                            
                                                                                                                            
 - 表重命名: model_config → model_info                                                                                      
 - 新增字段: mode (TEXT: 'llm', 'embed', 'rerank')                                                                          
 - 更新所有方法: 添加 mode 参数支持                                                                                         
   - add_model(name, path, mode)                                                                                            
   - get_models_by_mode(mode)                                                                                               
   - get_current_model(mode)                                                                                                
   - set_current_model(model_id, mode)                                                                                      
                                                                                                                            
 迁移策略:                                                                                                                  
 - 创建新表 model_info                                                                                                      
 - 从旧表 model_config 迁移数据（默认 mode='llm'）                                                                          
 - 删除旧表                                                                                                                 
                                                                                                                            
 2. 配置文件更新                                                                                                            
                                                                                                                            
 文件: backend/src/config.py                                                                                                
                                                                                                                            
 # 目录结构调整                                                                                                             
 MODELS_DIR = BASE_DIR / "models"  # 改为 models（复数）                                                                    
 LLM_MODELS_DIR = MODELS_DIR / "llm"                                                                                        
 EMBED_MODELS_DIR = MODELS_DIR / "embed"                                                                                    
 RERANK_MODELS_DIR = MODELS_DIR / "rerank"                                                                                  
                                                                                                                            
 # 默认模型 URLs 按模式分类                                                                                                 
 DEFAULT_MODEL_DOWNLOAD_URLS = {                                                                                            
     "llm": [                                                                                                               
                                                                                                                            
 "https://modelscope.cn/models/second-state/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/Qwen2.5-0.5B-Instruct-Q4_0.gguf",     
         "https://modelscope.cn/models/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf"                         
     ],                                                                                                                     
     "embed": [                                                                                                             
         "https://hf-mirror.com/nomic-ai/nomic-embed-text-v2-moe-GGUF/resolve/main/nomic-embed-text-v2-moe.Q4_0.gguf"       
     ],                                                                                                                     
     "rerank": [                                                                                                            
         "https://modelscope.cn/models/gpustack/bge-reranker-v2-m3-GGUF/resolve/master/bge-reranker-v2-m3-Q4_0.gguf"        
     ]                                                                                                                      
 }                                                                                                                          
                                                                                                                            
 3. API 接口重构                                                                                                            
                                                                                                                            
 文件: backend/src/main.py                                                                                                  
                                                                                                                            
 新增/修改接口:                                                                                                             
 - GET /api/models/current?mode={llm|embed|rerank} - 查看当前模型                                                           
 - GET /api/models/list?mode={llm|embed|rerank} - 查模型列表                                                                
 - POST /api/models/load - 下载进度、模型切换（带 mode 参数）                                                               
 - POST /api/models/download - 下载模型（带 mode 参数）                                                                     
 - GET /api/models/get_param?mode={llm|embed|rerank} - 获取参数                                                             
 - POST /api/models/update_param - 更新参数（带 mode 参数）                                                                 
                                                                                                                            
 保留接口（向后兼容）:                                                                                                      
 - 现有 /api/models/* 接口默认 mode='llm'                                                                                   
                                                                                                                            
 4. 模型管理器扩展                                                                                                          
                                                                                                                            
 文件: backend/src/model/llm.py                                                                                             
                                                                                                                            
 - 重命名为 backend/src/model/model_server.py                                                                               
 - LLMServer → ModelServer                                                                                                  
 - 添加 mode 属性                                                                                                           
 - 支持不同模式的服务器配置                                                                                                 
                                                                                                                            
 新增文件:                                                                                                                  
 - backend/src/model/embed_server.py - Embed 模型服务器                                                                     
 - backend/src/model/rerank_server.py - Rerank 模型服务器                                                                   
                                                                                                                            
 5. Pipeline 更新                                                                                                           
                                                                                                                            
 文件: backend/src/pipeline/model_select.py                                                                                 
                                                                                                                            
 - 添加 mode 参数到所有方法                                                                                                 
 - 根据 mode 选择正确的目录和服务器                                                                                         
 - 更新数据库调用以包含 mode                                                                                                
                                                                                                                            
 6. 前端 UI 重构                                                                                                            
                                                                                                                            
 文件: frontend/src/pages/SettingsPage.tsx                                                                                  
                                                                                                                            
 UI 布局:                                                                                                                   
 ┌─────────────────────────────────────┐                                                                                    
 │ LLM 模型                             │                                                                                   
 │ [模型选择下拉框] [●运行中]           │                                                                                   
 │ [LLM 参数配置...]                    │                                                                                   
 ├─────────────────────────────────────┤                                                                                    
 │ Embed 模型                           │                                                                                   
 │ [模型选择下拉框] [●未启动]           │                                                                                   
 │ [Embed 参数配置...]                  │                                                                                   
 ├─────────────────────────────────────┤                                                                                    
 │ Rerank 模型                          │                                                                                   
 │ [模型选择下拉框] [●未启动]           │                                                                                   
 │ [Rerank 参数配置...]                 │                                                                                   
 └─────────────────────────────────────┘                                                                                    
                                                                                                                            
 组件复用:                                                                                                                  
 - 创建 ModelSection 组件                                                                                                   
 - 接受 props: mode, title, models, currentModel, parameters                                                                
 - 每个模式独立状态管理                                                                                                     
                                                                                                                            
 7. 类型定义更新                                                                                                            
                                                                                                                            
 新增类型:                                                                                                                  
 type ModelMode = 'llm' | 'embed' | 'rerank'                                                                                
                                                                                                                            
 interface ModelInfo {                                                                                                      
   id: number                                                                                                               
   name: string                                                                                                             
   path: string                                                                                                             
   mode: ModelMode                                                                                                          
   is_downloaded: boolean                                                                                                   
 }                                                                                                                          
                                                                                                                            
 interface ModelParameters {                                                                                                
   llm: LLMParameters                                                                                                       
   embed: EmbedParameters                                                                                                   
   rerank: RerankParameters                                                                                                 
 }                                                                                                                          
                                                                                                                            
 实现步骤                                                                                                                   
                                                                                                                            
 Phase 1: 数据库和配置                                                                                                      
                                                                                                                            
 1. 更新 sqlite_config.py - 重命名表、添加 mode 字段                                                                        
 2. 更新 config.py - 调整目录结构和 URLs                                                                                    
 3. 创建数据库迁移脚本                                                                                                      
                                                                                                                            
 Phase 2: 后端核心                                                                                                          
                                                                                                                            
 4. 扩展模型服务器支持多模式                                                                                                
 5. 更新 Pipeline 支持 mode 参数                                                                                            
 6. 重构 API 接口添加 mode 支持                                                                                             
                                                                                                                            
 Phase 3: 前端 UI                                                                                                           
                                                                                                                            
 7. 创建 ModelSection 组件                                                                                                  
 8. 重构 SettingsPage 为三列布局                                                                                            
 9. 更新 API 调用添加 mode 参数                                                                                             
                                                                                                                            
 Phase 4: 测试和验证                                                                                                        
                                                                                                                            
 10. 测试三种模式的模型下载                                                                                                 
 11. 测试模型切换和参数配置                                                                                                 
 12. 验证数据库迁移                                                                                                         
                                                                                                                            
 关键文件清单                                                                                                               
                                                                                                                            
 后端:                                                                                                                      
 - backend/src/comon/sqlite/sqlite_config.py - 数据库表重构                                                                 
 - backend/src/config.py - 配置更新                                                                                         
 - backend/src/main.py - API 接口重构                                                                                       
 - backend/src/model/llm.py - 模型服务器扩展                                                                                
 - backend/src/pipeline/model_select.py - Pipeline 更新                                                                     
                                                                                                                            
 前端:                                                                                                                      
 - frontend/src/pages/SettingsPage.tsx - UI 重构                                                                            
 - frontend/src/components/ModelSection.tsx - 新组件（待创建）                                                              
 - frontend/src/types/models.ts - 类型定义（待创建）                                                                        
                                                                                                                            
 验证方法                                                                                                                   
                                                                                                                            
 1. 数据库验证:                                                                                                             
 sqlite3 ~/.cache/zenow/data/db/config.db                                                                                   
 .schema model_info                                                                                                         
 SELECT * FROM model_info;                                                                                                  
 2. 目录结构验证:                                                                                                           
 ls -la ~/.cache/zenow/models/llm/                                                                                          
 ls -la ~/.cache/zenow/models/embed/                                                                                        
 ls -la ~/.cache/zenow/models/rerank/                                                                                       
 3. API 测试:                                                                                                               
 curl http://localhost:8050/api/models/list?mode=llm                                                                        
 curl http://localhost:8050/api/models/list?mode=embed                                                                      
 curl http://localhost:8050/api/models/list?mode=rerank                                                                     
 4. 前端测试:                                                                                                               
   - 打开设置页，验证三个模型区域并列显示                                                                                   
   - 测试每个模式的模型下载和切换                                                                                           
   - 验证参数配置独立生效                                                                                                   
                                                                                                                            
 注意事项                                                                                                                   
                                                                                                                            
 1. 向后兼容: 现有 API 默认 mode='llm'，不破坏现有功能                                                                      
 2. 数据迁移: 旧数据自动迁移到 mode='llm'                                                                                   
 3. 目录创建: 自动创建三个模式的子目录                                                                                      
 4. 错误处理: 每个模式独立错误处理，互不影响        