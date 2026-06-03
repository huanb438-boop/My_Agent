"""
=============================================================================
 config.py — 配置加载模块
=============================================================================
 职责:
   读取 config.yaml 配置文件，将其转换为类型安全的 Python 数据类对象。
   支持环境变量引用解析（${VAR_NAME} 语法）和默认值回退。

 数据流:
   config.yaml (YAML)
     ↓ yaml.safe_load()
   Python dict
     ↓ 逐字段提取 + 默认值 + 环境变量解析
   Config dataclass (类型安全的 Python 对象)
     ↓ config.model.name / config.agent.max_turns / config.tools.enabled
   main.py 中使用
=============================================================================
"""

import os                    # 操作系统接口，用于读取环境变量
import yaml                  # YAML 解析库（需要 PyYAML 包）
from dataclasses import dataclass, field  # 数据类装饰器


# ============================================================================
# 模型配置类
# ============================================================================
@dataclass
class ModelConfig:
    """
    AI 模型的连接参数。

    属性:
      provider: 模型提供商名称（如 deepseek, openai, anthropic）
      name:     模型名称（对应 API 的 "model" 字段）
      base_url: API 基础地址
      api_key:  API 密钥（由 _resolve_env 从环境变量解析）
    """
    provider: str        # 模型提供商
    name: str            # 模型名称
    base_url: str        # API 基础 URL
    api_key: str = ""    # API 密钥（默认空字符串，由环境变量注入）


# ============================================================================
# Agent 配置类
# ============================================================================
@dataclass
class AgentConfig:
    """
    Agent 的行为参数。

    属性:
      max_turns:     最大对话轮数（防止无限循环）
      system_prompt: 系统提示词（定义 Agent 角色和行为）
      temperature:   生成温度（控制输出的随机性）
    """
    max_turns: int = 50              # 默认最大 50 轮
    system_prompt: str = "You are a helpful AI assistant with tool access."
    temperature: float = 0.3         # 默认低温度，适用于工具调用场景


# ============================================================================
# 工具配置类
# ============================================================================
@dataclass
class ToolConfig:
    """
    可用工具配置。

    属性:
      enabled: 启用的工具名称列表
               ★ 注意：此配置当前被读取但未在 agent.py 中强制执行权限检查
    """
    enabled: list = field(
        default_factory=lambda: ["bash", "read_file"]
    )


# ============================================================================
# 全局配置类
# ============================================================================
@dataclass
class Config:
    """
    顶层配置，聚合所有子配置。

    属性:
      model: 模型连接配置
      agent: Agent 行为配置
      tools: 工具权限配置
    """
    model: ModelConfig
    agent: AgentConfig = field(default_factory=AgentConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)


# ============================================================================
# 环境变量解析函数
# ============================================================================
def _resolve_env(value: str) -> str:
    """
    解析 YAML 中的环境变量引用。

    规则:
      - ${VAR_NAME} 格式 → 从环境变量读取 VAR_NAME
      - 其他格式        → 原样返回

    示例:
      _resolve_env("${DEEPSEEK_API_KEY}")  → os.environ["DEEPSEEK_API_KEY"]
      _resolve_env("https://api.example.com")  → "https://api.example.com"

    安全:
      如果环境变量未设置，抛出 ValueError 避免静默使用空密钥。
    """
    # 判断是否为 ${VAR} 格式
    if value.startswith("${") and value.endswith("}"):
        # 提取变量名（去掉 ${ 和 }）
        env_var = value[2:-1]
        # 从环境变量读取
        resolved = os.environ.get(env_var)
        if not resolved:
            raise ValueError(
                f"Environment variable {env_var} not set. "
                f"Please set it or add it to your .env file."
            )
        return resolved
    # 非环境变量引用，原样返回
    return value


# ============================================================================
# 配置加载入口
# ============================================================================
def load_config(path: str = "config.yaml") -> Config:
    """
    加载 YAML 配置文件并返回类型安全的 Config 对象。

    参数:
      path: 配置文件路径（默认 "config.yaml"）

    返回:
      Config — 包含 model、agent、tools 三个子配置的顶层对象

    处理流程:
      1. 打开并读取 YAML 文件
      2. 逐节提取配置并应用默认值
      3. 解析环境变量引用
      4. 构造并返回 Config 数据类实例
    """
    # ---- 步骤 1: 读取 YAML 文件 ----
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}  # 或 {} 保证即使文件为空也不会崩溃

    # ---- 步骤 2: 提取模型配置 ----
    raw_model = raw.get("model", {})
    model = ModelConfig(
        provider=raw_model.get("provider", "deepseek"),
        name=raw_model.get("name", "deepseek-v4-flash"),
        base_url=raw_model.get("base_url", "https://api.deepseek.com/v1"),
        api_key=_resolve_env(
            raw_model.get("api_key", "${DEEPSEEK_API_KEY}")
        ),
    )

    # ---- 步骤 3: 提取 Agent 配置 ----
    raw_agent = raw.get("agent", {})
    agent = AgentConfig(
        max_turns=raw_agent.get("max_turns", 50),
        system_prompt=raw_agent.get(
            "system_prompt",
            "You are a helpful AI assistant with tool access."
        ),
        temperature=raw_agent.get("temperature", 0.3),
    )

    # ---- 步骤 4: 提取工具配置 ----
    raw_tools = raw.get("tools", {})
    tools = ToolConfig(
        enabled=raw_tools.get("enabled", ["bash", "read_file"]),
    )

    # ---- 步骤 5: 返回聚合的配置对象 ----
    return Config(model=model, agent=agent, tools=tools)
