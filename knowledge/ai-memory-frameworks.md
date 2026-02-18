# 前沿 AI 记忆框架与实现参考

## 1. 异步记忆固化 (Asynchronous Consolidation)
- **SimpleMem**: 三阶段流水线（语义压缩 -> 递归固化 -> 自适应检索）。降低 Token 消耗 30x。
- **Mem0**: 生产级记忆层。自动冲突解决 (Conflict Resolution) 和信息褪色 (Fading)。
- **Zep**: 自动生成摘要、提取事实，构建"时间知识图谱"。

## 2. 双重架构 (Dual Architecture)
- **MeridianDB**: 模仿海马体-皮层。Vectorize (短期) -> D1 关系库 (长期)。
- **HippocampAI**: 明确提出 "Dreaming" 相位，用于后台聚类和重要性校准。

## 3. 反思与自编辑 (Reflection & Self-Editing)
- **Letta (MemGPT)**: LLM-OS 概念。心跳机制自主整理，`memory_replace` 更新知识。
- **Generative Agents**: "睡觉"前进行 Reflection，合成高阶 Insights。
- **ReasoningBank**: 从失败中学习，提取逻辑断点。

## 4. 多智能体协作 (AMA Framework)
- **Constructor**: 构建数据。
- **Judge**: 审核逻辑一致性。
- **Refresher**: 更新过时记忆。
- 效果: Token 消耗降低 80%。

## 5. 工程 Skill
- **ICAL**: 上下文抽象学习。
- **OMEGA**: Coding 场景专用，跨会话记忆。
- **智能衰减**: 基于 Recency, Frequency, Saliency 的指数衰减。

---
*Source: User Contribution (2026-02-18)*
