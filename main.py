"""
=============================================================================
 main.py — wecode 项目入口文件
=============================================================================
 启动流程:
   1. 加载配置文件 (config.yaml)
   2. 自动发现并注册所有工具
   3. 初始化 LLM 客户端
   4. 创建 Agent 实例
   5. 启动交互式对话

 运行方式:
   cd D:\2026_code\my_agent
   python wecode\main.py

 环境要求:
   设置 DEEPSEEK_API_KEY 环境变量或在 .env 文件中定义
=============================================================================
"""

import sys          # 系统模块，用于修改模块搜索路径
import os           # 操作系统接口
import warnings     # 警告控制

# 忽略 requests 库的版本兼容性警告（urllib3/chardet 版本不匹配时）
warnings.filterwarnings("ignore", category=Warning, module="requests")

# 将 wecode/ 目录添加到 Python 模块搜索路径
# 这样即使从不同目录运行，也能正确导入 wecode 内的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---- 导入项目模块 ----
from config import load_config    # 配置加载
from llm import LLMConfig, LLMClient  # LLM 客户端
from agent import Agent           # Agent 核心


def main():
    """
    主函数 — 启动 wecode Agent。

    执行顺序:
      1. load_config():    读取 config.yaml → Config 数据类
      2. discover_tools(): 扫描 tools/ 目录 → 自动注册所有工具
      3. LLMClient():      初始化与大语言模型的连接
      4. Agent():          创建 Agent 实例（注入 LLM + 配置参数）
      5. agent.chat():     启动 CLI 交互式对话
    """
    # ---- 步骤 1: 加载配置 ----
    # 从 config.yaml 读取模型、Agent 和工具配置
    config = load_config("config.yaml")

    # ---- 步骤 2: 注册工具 ----
    # 延迟导入，避免循环依赖
    from tools import discover_tools
    discover_tools()  # 自动扫描并注册 tools/ 下的所有工具模块

    # ---- 步骤 3: 初始化 LLM 客户端 ----
    # 将 Config.model 的字段解包为 LLMConfig 的构造函数参数
    llm_config = LLMConfig(**config.model.__dict__)
    llm = LLMClient(llm_config)

    # ---- 步骤 4: 创建 Agent ----
    agent = Agent(
        llm=llm,
        system_prompt=config.agent.system_prompt,
        max_turns=config.agent.max_turns,
        temperature=config.agent.temperature,
    )

    # ---- 步骤 5: 启动对话 ----
    agent.chat()


# ===== 程序入口 =====
# 当直接运行 python wecode/main.py 时执行
if __name__ == "__main__":
    main()
