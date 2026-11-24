# 整活片场 · Zhenghuo Studio

**一个 Codex 技能，十三个按需模块。** 从商品事实、参考拆解和创意，走到分镜、台词、关键帧、模型交接与发布文案。默认图片用本地模型，视频走 H3 API。

版本：**0.1.0**。支持原创、多参考创作、参考裂变和精确拆解；不覆盖已有完整版／轻量版工作流。它是技能与本地规划工具箱，实际媒体生成复用运行环境中已配置的模型工具。

## 安装到 Codex

下载并解压本仓库或完整发行包，在解压目录运行：

```text
python install.py
```

需要 Python 3.11+，无额外 Python 依赖。默认安装到 `CODEX_HOME/skills`，未设置时使用用户目录下的 `.codex/skills`。支持 `--skill-root` 指定其他技能目录。已有不同内容的同名技能会拒绝覆盖；相同版本可重复执行。

安装后在新的 Codex 对话中输入：

```text
用 $zhenghuo-studio 帮我做一条新的商品视频工作流。
生图用本地图片模型，视频用 H3 API。先根据我提供的素材确定路线。
```

也可以说“用整活片场的啪啪啪裂变”“让挑刺评审团检查这个方案”“用口吻分身改这段文案”。技能入口是 [SKILL.md](skills/zhenghuo-studio/SKILL.md)。宿主是否立即刷新技能列表以实际界面为准。

## 全部模块

| 模块 | 职责 |
|---|---|
| 总导演 | 需求、事实、路线、选案与状态 |
| 脑洞搅拌机 | 新角度；选题扩写 |
| 反差整活导演 | 冲突、反转、开头 |
| 挑刺评审团 | 模拟多视角评估与具体问题 |
| 原片拆解台 | 原“关键帧改写复刻视频”；源证据与 39／43 列精确视图 |
| 啪啪啪裂变 | 四步裂变、商品适配、关键帧与宫格 |
| 分镜施工图 | 唯一镜头计划与连续性 |
| 现场质感师 | 光线、空间、动作、情绪与声音 |
| 口播翻译官 | 源语、目标语、中文核对与时间 |
| 收尾吆喝官 | 发布文字、CTA 与标签 |
| 口吻分身 | 风格卡、台词与通用写作 |
| 省脑场务 | 真实任务、精力与截止时间 |
| 开工小抄 | 开工、会议及复盘准备 |

模块按需读取，使用顺序由任务决定。总导演负责路由，其他岗位各有独立产物；源证据、台词、分镜和最终提示词分别只维护一份有效版本。

## 本地工具

以下命令从仓库根目录运行；安装后也可用技能目录下同一脚本。

```text
python skills/zhenghuo-studio/scripts/studio.py modules
python skills/zhenghuo-studio/scripts/studio.py init --project-dir work/demo --route original --duration 30 --market 示例市场 --language 示例语言
python skills/zhenghuo-studio/scripts/studio.py check-plan --plan work/demo/project.json
python skills/zhenghuo-studio/scripts/studio.py prepare-handoff --plan work/demo/project.json --output work/demo/handoff.json
python skills/zhenghuo-studio/scripts/studio.py doctor --local-url http://127.0.0.1:8198
```

空计划需要先补分镜、素材和真实模型参数，预检拒绝空计划是正常行为。工具检查非零分段、真实允许时长、裁切、转场、目标总长、素材存在性与版本哈希。交接不会上传文件、发起收费任务或自动批准费用。

[模型交接与配置](skills/zhenghuo-studio/references/backends.md) · [协作协议](skills/zhenghuo-studio/references/protocol.md) · [精确字段与时长](skills/zhenghuo-studio/references/precise-fields.md)

## 验证与使用边界

```text
python -m unittest discover -s tests -v
python verify_package.py
```

本地测试覆盖计划边界、文件版本、交接和安装行为。源技能功能已经逐项映射到 13 个模块，39／43 列字段保留。**本发行版未进行真实商品端到端图片／H3 成片测试。** 本地队列可读不代表模型就绪，提示词也不保证商品、口型或销量表现。

开始实际制作仍遵循当前项目的确认、费用、上传与验收要求。H3 服务商、型号、价格和输入能力需在执行时核实。公开工具包不包含第三方课程全文、模型权重、密钥、账号资料或真实商品素材。

代码与本仓库重写文档采用 [MIT License](LICENSE)。来源说明见 [NOTICE.md](NOTICE.md)。
