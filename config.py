"""配置层:集中管理应用配置。

用法:应用工厂通过 config_name 选择配置类:
    create_app("development")   # 开发环境
    create_app("production")    # 生产环境
不传则用 default。

密钥等敏感信息从 .env 读取(不入 git),配置类只做读取和分类。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录的 .env(密钥)
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / ".env")


class Config:
    """基础配置:所有环境共用的值。"""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-key")

    # OpenAI 相关
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or None


class DevelopmentConfig(Config):
    """开发环境配置。"""

    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置。"""

    DEBUG = False


class TestingConfig(Config):
    """测试环境配置。"""

    TESTING = True
    OPENAI_API_KEY = "test-key-not-real"


# 配置注册表:create_app 用字符串索引选择环境
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
