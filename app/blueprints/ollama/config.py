class Conf:
    # --- 连接与模型(专题内独立配置,直接对照课程)---
    HOST = "http://127.0.0.1:11434"
    CHAT_MODEL = "qwen2.5:7b"

    # --- 案例 1:采样参数 ---
    TEMPERATURE = 0.3   # 越小越确定(专业 0.1~0.4,创意 0.7~1.0)
    TOP_P = 0.9         # 候选词概率累积阈值
    NUM_PREDICT = 2048  # 最大输出 token 数
