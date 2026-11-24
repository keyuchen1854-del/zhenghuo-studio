# 精确字段与时长规则

## 精确分析能力保留

裂变第 1 步的 39 列作为源观察视图保留；三合一的 43 列是这 39 列追加 4 列改写／选帧信息。同一份证据按需导出，不重复分析。

39 个公共字段：

```text
shot_id, start_sec, end_sec, duration_sec, scene_group_id,
scene_title_cn, shot_title_cn, shot_goal, aspect_ratio, video_type_tag,
visual_content_description, location_setting, character_desc, emotion_state,
action_blocking, product_desc, must_show, on_screen_text_graphics,
camera_shot_size, camera_angle, camera_movement, composition_notes,
lighting_atmosphere, color_grading, dialogue_vo_original, dialogue_vo_zh,
language_style, emphasis_notes, audio_bgm, audio_sfx, ambient_sound,
editing_transition, pacing_notes, constraints_real_shoot, constraints_compliance,
reverse_constraints, assets_needed, sentence_mapping, mapping_notes
```

43 列追加字段：

```text
rewrite_vo_target_language, rewrite_vo_zh_translation,
ref_frame_timestamp_sec, ref_frame_basis
```

源表描述原片商品、口播和时间码；新商品放在关联改编记录中，不能覆盖原证据。原格式按顺序输出；内部可用关联表避免重复长文本。逐句证据保留编号、起止时间、时长、原文、中文翻译、画面文字、信息说明和听清程度。估计时间明确标记，覆盖检查必须逐镜执行，不能只看最后一行。

## 时长修正

原第 2 步的极简公式 `N = floor(T/L)` 在原视频短于单元上限时会得到零段，不能直接保留。“目标时长不得长于原视频”只适用于用户要求的压缩任务，不能限制独立原创故事。

分别记录源时长、成片目标时长、接口接受并计费的生成时长、每段实际保留区间、剪辑转场重叠。源时长是证据，不因改编变化。

- 有内容的任务至少 1 段。
- 接口允许连续可变时长、上限为 L 时，`ceil(目标时长/L)` 只是段数下界；动作、切点、口播和真实允许值可能要求更多段。
- 固定时长接口按真实允许值生成并记录裁切，不伪造可变时长参数。
- 成片计划时长 = 各段保留区间长度之和 − 实际转场重叠时长。
- 用源重叠保证衔接时，回拼要实际去掉重复内容，不能只在公式里扣除。
- 口播和必要动作必须落在保留区间；最终用成片媒体时长复验。
- 未知时长范围、分辨率或价格只能形成待核计划，不能付费提交。

以下 L=15 秒仅为演算，不代表 H3 当前参数：

| 输入 | 正确判断 |
|---|---|
| 目标 5 秒，上限 15 秒 | 至少 1 段，不能得到 0；实际生成长度按允许值 |
| 目标 30 秒，上限 15 秒 | 最少 2 段；不能把完整使用的 3×15 秒称为 30 秒 |
| 目标 31 秒，上限 15 秒 | 最少 3 段；不能把过多台词和动作塞进最后 1 秒 |
| 源 45 秒，原创目标 30 秒 | 源证据保留 45 秒，明确删改后按 30 秒规划 |
| 源 20 秒，原创目标 30 秒 | 新增部分标为创作，不冒充源内容 |
| 固定生成 3×15 秒，目标 30 秒 | 按真实 45 秒计费，通过明确保留区间／转场实现 30 秒 |

`scripts/studio.py check-plan` 已实现这些本地预检。脚本检查计划与文件；实际画面、口播自然度、商品结构和动作仍需视听验收。
