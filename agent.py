"""
=============================================================================
 agent.py — AI Agent 核心（ReAct 循环）
=============================================================================
 架构:
   实现 ReAct（Reasoning + Acting）模式的 Agent 循环：
   推理（Think）→ 行动（Act）→ 观察（Observe）→ 循环

 工作流程:
   1. 接收用户输入
   2. 构建消息列表（系统提示 + 用户输入 + 历史记录）
   3. 获取已注册的工具定义
   4. 调用 LLM（传入消息和工具定义）
   5. 如果 LLM 返回文本 → 作为最终回复返回
   6. 如果 LLM 返回工具调用 → 执行工具 → 结果追加到消息 → 回到步骤 4
   7. 达到最大轮数 → 返回超时提示
=============================================================================
"""

from wecode.llm import LLMClient    # LLM API 客户端
from tools.registry import registry  # 工具注册中心单例
import json                         # JSON 序列化/反序列化


# ============================================================================
# Agent 类
# ============================================================================
class Agent:
    """
    AI Agent 核心类，实现 ReAct（推理-行动-观察）循环。

    属性:
      llm:            LLMClient 实例，负责与 AI 模型通信
      system_prompt:  系统提示词，定义 Agent 的角色和行为
      max_turns:      最大对话轮数，防止工具调用陷入无限循环
      temperature:    生成温度，控制输出的随机性（0.0-1.0）
      messages:       消息历史列表，存储完整的对话上下文
    """

    def __init__(
        self,
        llm: LLMClient,                          # LLM 客户端
        system_prompt: str = "You are a helpful AI assistant.",  # 系统提示
        max_turns: int = 50,                     # 最大轮数
        temperature: float = 0.3,                # 温度参数
    ):
        """
        初始化 Agent。

        参数:
          llm:            LLMClient 实例
          system_prompt:  系统提示词
          max_turns:      最大迭代轮数
          temperature:    生成温度
        """
        self.llm = llm
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.temperature = temperature
        self.messages: list = []  # 对话历史列表（每个元素为 role + content 字典）


    def run(self, user_input: str) -> str:
        """
        执行一次完整的对话回合。

        参数:
          user_input: 用户的输入文本

        返回:
          str — Agent 的最终回复文本

        处理流程:
          1. 初始化消息列表（系统提示 + 用户输入）
          2. 进入工具调用循环（最多 max_turns 轮）
             a. 获取所有已注册的工具定义
             b. 调用 LLM 获取回复
             c. 将回复追加到消息列表
             d. 如果回复不含工具调用 → 返回文本内容（结束）
             e. 如果回复含工具调用 → 逐个执行工具 → 结果追加到消息
          3. 达到最大轮数 → 返回超时提示
        """
        # ---- 步骤 1: 构建初始消息列表 ----
        self.messages = [
            {"role": "system", "content": self.system_prompt},  # 系统提示
            {"role": "user", "content": user_input},             # 用户输入
        ]

        # ---- 步骤 2: 进入工具调用循环 ----
        for turn in range(self.max_turns):
            # 2a. 获取工具定义（JSON Schema 格式）
            tools = registry.get_definitions()

            # 2b. 调用 LLM
            response = self.llm.chat(
                self.messages,
                tools,
                temperature=self.temperature,
            )

            # 2c. 将 LLM 回复追加到消息历史
            self.messages.append(response)

            # 2d. 检查 LLM 是否调用了工具
            tool_calls = response.get("tool_calls")
            if not tool_calls:
                # 没有工具调用 → LLM 返回了最终文本回复
                return response.get("content", "")

            # 2e. 执行每个工具调用
            for tc in tool_calls:
                # 解析工具调用的函数名和参数
                func = tc["function"]     # {"name": "bash", "arguments": '{"command":"ls"}'}
                name = func["name"]       # 工具名称
                args = json.loads(func["arguments"])  # 参数（从 JSON 字符串解析）

                # 通过注册中心执行工具
                result = registry.dispatch(name, args)

                # 将工具执行结果添加到消息列表
                self.messages.append({
                    "role": "tool",           # 工具角色
                    "tool_call_id": tc["id"],  # 关联的工具调用 ID
                    "content": result,         # 工具输出（JSON 字符串）
                })

            # 继续下一轮循环 → LLM 会看到工具结果并决定下一步

        # ---- 步骤 3: 达到最大轮数 ----
        return "Max turns reached."


    def chat(self):
        """
        启动交互式 CLI 对话。

        工作在 REPL（Read-Eval-Print Loop）模式：
        1. 读取用户输入
        2. 执行 Agent.run()
        3. 打印回复
        4. 回到步骤 1（直到用户输入 exit 或 quit）
        """
        print("Agent is ready to chat. Type exit to quit.")

        while True:
            # 读取用户输入
            user_input = input("\n> ").strip()

            # 检查退出条件
            if user_input.lower() in ("exit", "quit"):
                print("Agent: Goodbye!")
                break

            # 运行 Agent 并输出回复
            response = self.run(user_input)
            print(f"\nAgent: {response}")
