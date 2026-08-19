"""Run the five-query bonus demonstration from the repository root."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bonus.agent import HybridMemoryAgent


MEMORIES = [
    "Tôi đã đọc về Kubernetes, autoscaling và cách vận hành cluster cloud ổn định.",
    "Tôi quan tâm cloud security, mã hóa dữ liệu, OAuth và zero-trust.",
    "Tôi muốn học thêm observability, FinOps và tối ưu chi phí hạ tầng.",
]

QUERIES = [
    "Tôi đã đọc gì về Kubernetes?",
    "Recommend đọc gì tiếp",
    "Tôi đang quan tâm gì gần đây?",
    "Tài liệu về tự động mở rộng hạ tầng?",
    "Cho tôi summary cloud security",
]


def main() -> None:
    agent = HybridMemoryAgent()
    for memory in MEMORIES:
        agent.remember(memory)
    for number, query in enumerate(QUERIES, 1):
        print(f"\n[{number}] {query}")
        print(agent.recall(query))


if __name__ == "__main__":
    main()
