# Spec:知识库 CRUD 模块

## Problem Statement

项目要构建 Naive RAG(中医病历问答),需要先把知识库数据管理起来。当前有一个 300 例的中医辨证论治病例文件(`knowledge_base/病例.txt`),但没有途径把数据写入 Milvus 向量库,也无法在写入后进行增删改查管理。用户需要一个知识库管理模块:既能手动输入单条病历,也能通过文件批量导入,入库后可按 id 查看、修改、删除。

## Solution

在 RAG 主题下新增独立的「知识库管理」模块,通过 HTTP API 提供完整的 CRUD:

- **Create**:手动输入单条(JSON 提交文本,服务端向量化后入库)+ 文件上传(`.txt`,按病例编号分割后批量向量化入库)
- **Read**:分页列表 + 按 id 查单条详情
- **Update**:按 id 修改文本,自动重新向量化(只影响该条)
- **Delete**:按 id 删除

数据存储在 Milvus collection `tcm_medical_record`,每条病例 = 一条记录(文本 + 向量 + 自增 id)。向量化由智谱 embedding-3 完成。

## User Stories

1. 作为用户,我想手动输入一条病历文本入库,以便单独添加某条知识
2. 作为用户,我想上传 `.txt` 文件批量导入病历,以便一次性建立知识库
3. 作为用户,我想查看知识库的全部分页列表,以便了解已入库内容
4. 作为用户,我想按 id 查看单条记录原文,以便核对入库内容是否正确
5. 作为用户,我想按 id 修改某条记录的文本,以便修正录入错误(系统自动重新向量化)
6. 作为用户,我想按 id 删除某条记录,以便移除错误或不再需要的条目
7. 作为 RAG 学习者,我想确认每条入库记录同时包含原文与向量,以便后续检索阶段直接使用
8. 作为开发者,我想 collection 首次写入时自动创建,以便零手工初始化数据库
9. 作为用户,我想文件上传时自动按病例编号(如「1 感冒・风寒束表证」)分割成独立记录,以便每条病例是完整可检索单元
10. 作为用户,我想上传非 `.txt` 文件时得到明确拒绝,以便了解格式边界
11. 作为用户,我想提交空文本或非法参数时得到清晰错误提示,以便快速定位问题
12. 作为用户,我想修改或删除不存在的 id 时得到明确 404,以便确认操作对象
13. 作为用户,我想列表接口支持分页参数(page/size),以便 300 条记录不会一次全量返回
14. 作为用户,我想手动输入的单条文本直接作为一条记录(不切分),以便保留完整辨证论治链路

## Implementation Decisions

### 模块结构

- 在 RAG 主题(`app/blueprints/rag/`)下新增独立模块 `knowledge_base`,与 `naive_rag`(检索方案)平级,互不依赖
- 模块内部三层:
  - **Controller 层**:只处理 HTTP 请求/响应,路由注册到 rag 主题 blueprint,URL 前缀 `/rag/knowledge`
  - **Service 层**:业务编排——文本分割、向量化调用、参数校验
  - **milvus_store 层**:Milvus 数据访问——建 collection、增删改查(满足既有「出现多处重复数据代码时拆出独立数据访问模块」的准则)

### 数据模型(Milvus collection `tcm_medical_record`)

- 三个字段(用户明确坚持,不加 source 等元数据):
  - `id`:int64 **主键,应用分配**(查询当前最大 id + 1 连续递增;实测确认 Milvus `auto_id` 的 collection 无法用原 id 更新记录——upsert 会重生成 id,与 Update 保持 id 不变的决策冲突,故改为应用分配)
  - `vector`:float_vector,2048 维(智谱 embedding-3 输出)
  - `text`:varchar,原文内容
- collection 首次写入时自动创建(schema + 向量索引),度量方式 COSINE
- Milvus 访问使用新版 `MilvusClient` API(pymilvus 3.x,ORM 风格 API 将在 3.1 移除)

### 数据粒度(关键决策)

- **不做字符切分**:实测 300 条病例每条 172-286 字(中位 218),全部低于 embedding 单输入上限(3072 tokens ≈ 4600 中文字),每条病例本身就是完整检索单元
- 文件上传:按编号行正则(`^\d+ `)把 txt 分割成 300 条独立病例,每条向量化后入库
- 手动输入:单条文本直接入库(一条 = 一条)
- 依据:NVIDIA 基准(page-level 切分最优)+ OpenAI cookbook(结构化文档按逻辑单元切)

### API 契约

| 方法 | 路径 | 请求 | 响应 |
|---|---|---|---|
| POST | `/rag/knowledge` | JSON `{"text": "..."}` | 201 + 新记录 id |
| POST | `/rag/knowledge/upload` | multipart 文件(`.txt`) | 201 + 入库条数 |
| GET | `/rag/knowledge?page=&size=` | - | 200 + 分页列表 |
| GET | `/rag/knowledge/<int:id>` | - | 200 + 单条详情 / 404 |
| PUT | `/rag/knowledge/<int:id>` | JSON `{"text": "..."}` | 200 / 404 |
| DELETE | `/rag/knowledge/<int:id>` | - | 204 / 404 |

- Update 语义:**按 id 改单条 text + 重新向量化**,不是重新上传文件
- 文件格式:仅支持 `.txt`(后期按需扩展 pdf/docx)

### 配置

- 全部走根 `config.py`(已有:`EMBEDDING_*` 智谱、`MILVUS_*`、`RAG_SCHEMES["naive_rag"]["COLLECTION_NAME"]` = `tcm_medical_record`)
- 知识库目录:`KNOWLEDGE_BASE_DIR`(当前指向 `knowledge_base/`)

## Testing Decisions

- **测试 seam:HTTP API 层**(Flask `test_client`)——只测外部行为(请求 → 状态码 + JSON 结构),不测内部函数实现细节,一个 seam 覆盖整个 CRUD
- 好的测试:构造请求 → 断言响应状态码与 JSON 字段;对边界(空文本、不存在 id、非 txt 文件)断言错误响应
- 测试模块:
  - 路由行为(controller):6 个端点的成功/失败路径
  - 文件分割逻辑(service):编号行正则正确分出 300 条
  - Milvus 集成(milvus_store):增删改查在真实 Milvus 上往返(本地已部署 Docker Standalone,可用独立测试 collection 隔离)
- 项目当前无测试基础设施(新建立),无既有先例

## Out of Scope

- 向量检索 / 问答(属于 naive_rag 检索阶段,CRUD 只管数据管理)
- `source`/元数据字段(用户确认三字段足够,溯源需求出现时再加)
- pdf/docx 等多格式支持(后期扩展)
- 批量 Update / 批量 Delete
- 重复导入去重(同一文件重复上传会创建重复记录)
- 前端页面(纯 API)

## Further Notes

- 病历源文件在 `knowledge_base/`,已被 `.gitignore` 忽略(私有数据)
- embedding 模型必须与后续检索阶段一致(智谱 embedding-3),否则检索无意义
- Milvus 需本地运行(用户已部署 Docker Standalone v2.6.x,端口 19530)
- 知识库 CRUD 是数据资产管理层,`naive_rag` 是使用层,未来新 RAG 方案可复用同一知识库
