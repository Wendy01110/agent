"""Entry point for the smart_agent project."""
from __future__ import annotations

import sys

from workflow.flow import run_flow


def main() -> None:
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        #  "帮我查今天北京天气，规划一下当天游玩路线安排。"
        #  "写一段常见算法代码，并运行给出结果。"
        result = run_flow(user_input, stream=True)
        print("\n=== Plan ===")
        print(result["plan"])
        print("\n=== Final ===")
        print(result["final"])
        return

    history: list[tuple[str, str]] = []
    print("进入交互模式。命令：/reset 清空上下文，/exit 退出。")
    while True:
        try:
            user_input = input("\n你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出。")
            break

        if not user_input:
            continue
        if user_input in {"/exit"}:
            print("退出。")
            break
        if user_input in {"/reset"}:
            history.clear()
            print("上下文已清空。")
            continue

        if history:
            context_lines = []
            for u, a in history[-5:]:
                context_lines.append(f"用户：{u}")
                context_lines.append(f"助手：{a}")
            context = "\n".join(context_lines)
            composed_input = f"{context}\n\n用户：{user_input}"
        else:
            composed_input = user_input

        result = run_flow(composed_input, stream=True)
        # print("\n=== Plan ===")
        # print(result["plan"])
        # print("\n=== Final ===")
        # print(result["final"])
        history.append((user_input, result["final"]))


if __name__ == "__main__":
    main()
