# GRID Pipeline Project

> 仓库维护者：**Zeng Xian, GRID team**

> 用途：统一的 GRID 数据处理与可视化流水线（pipeline）工程，涵盖载荷处理、快速质检（quicklook）、与部署说明。

---

## 项目目录结构

```
.
├─docs                          # 说明文档
│  ├─GIRD-11B                   # GRID-11B 说明文档
│  ├─GRID-02                    # GRID-02  说明文档
│  ├─GRID-09B                   # GRID-09B 说明文档
│  └─温度偏压标定数据
│      ├─03B
│      ├─04
│      ├─05B
│      ├─07
│      ├─10B_ch012
│      └─11B_ch012
|
├─grid11b_quicklook             # 基于 pipeline 产出的“快速浏览”可视化
│  └─quicklook-frontend         # 轻量可视化 Web 网页前端
|
├─readme                        # 部署与运维说明文档（补充 README 的细节）
│  ├─MD                         # markdown 格式
│  └─PDF                        # pdf 格式
|
└─src                           # 核心源码：pipeline 及各类“载荷”处理模块
|   ├─detectors                 # 探测器类定义
|   └─temp_bias_data            # 温度偏压标定数据
|   
| README.md                     # 本文件
```

---

## 环境要求

* **Python**：3.11 及以上版本

---

## 分支策略与提交规范

### 分支说明

* **`master`**：受保护的稳定分支，对应**已发布**或**可随时发布**状态；仅通过 PR 合并，需通过 CI。
* **`dev`**：日常开发集成分支；功能分支合并目标。
* **`grid-xx-feature/*`**：功能开发分支（从 `dev` 切出），分支名中需包含分支开发的载荷名称，完成后发起 PR 合并至 `dev`。

### 提交信息（Commit）

* 请在每条提交信息里加上如下关键词 (key-word)：
  * `feat:` 新功能
  * `fix:` 缺陷修复
  * `docs:` 文档更新
  * `refactor:` 重构
  * `test:` 测试

* 示例提交：
- `feat(grid-11b): 支持 grid-11b 载荷的完整日志查看`
- `fix(grid-11b): 修复 gird-11b 载荷在输入文件中缺少 housekeeping 文件时报错的问题`
- `refactor(grid-11b): 重构 grid-11b 载荷处理程序在 extractor 部分的代码，提升代码性能`
- `docs(repo): 更新了仓库整体的 README.md 文档，增加了团队协作要求的说明`

---

## 许可证
本项目采用 **PolyForm Noncommercial 1.0.0** 许可：允许学术/研究用途的使用、修改与再分发，但**禁止任何商业用途**。  
若有商业合作或再授权需求，请联系仓库维护者（Zeng Xian, GRID）。

---