# worklog-template

豆包（Doubao）插件技能：**工作日志模板生成与补齐**。

根据中国法定节假日安排与工作日规则，按用户既有记录格式（幕布大纲式周工作计划），自动生成全年或补齐剩余部分的工作日志模板 Markdown，可一键落库幕布（mubu）文档。

格式规范源自用户实际工作日志《2026--Agent爆发之年》的记录习惯。

## 目录结构

```
worklog-template/
├── SKILL.md                      # 技能入口：触发描述 + 工作流
├── references/
│   ├── worklog-format.md         # 格式规范（周标题/日期节点/跨月/节假日/备注）
│   └── holidays-cn.md            # 中国法定节假日安排参考（内置 2026 官方数据）
└── scripts/
    └── worklog_template.py       # 生成/补齐脚本（Python 3.10+，仅标准库）
```

## 功能特性

- **模式 A：全年骨架** — 从零生成某年全部工作日周节点 + 非双休国家节假日节点（含官方安排备注）。
- **模式 B：补齐现有** — 基于已有文档 Markdown，保留原文全部内容，自动插入缺失的节假日节点、追加剩余工作日周节点。
- **内置 2026 官方数据**（国办发明电〔2025〕7号）— 7 个节假日、6 个调休上班日，来源中国政府网。
- **跨年度可扩展** — 通过 `--holidays` 传入外置 JSON 即可切换任意年份。
- **格式高度贴合个人习惯** — 周标题 `# MMDD-MMDD`、跨月周首日带月份前缀（`- 0401`）、节假日周 `# 0101-03-元旦假期` 等。

## 安装步骤

### 方式一：安装到豆包（推荐）

1. **克隆本仓库**（或用浏览器直接下载 ZIP 解压）：

   ```bash
   git clone https://github.com/qingyuanLee/worklog-template.git
   ```

2. **找到豆包技能目录**。豆包桌面端插件技能的存放位置为：

   ```
   <豆包用户数据目录>\Default\.doubao\agent_mode\workspace\.user_skills\
   ```

   Windows 常见路径示例：

   ```
   C:\Users\<你的用户名>\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills\
   ```

3. **复制技能目录**：将克隆下来的 `worklog-template\worklog-template\` 整个文件夹复制到上述 `.user_skills\` 目录下。

   最终目录应为：

   ```
   .user_skills\
   ├── worklog-template\
   │   ├── SKILL.md
   │   ├── references\
   │   └── scripts\
   ├── ...（你已有的其他技能）
   ```

4. **重启豆包**（或新开会话），技能即被识别加载。之后可直接用自然语言触发，例如：

   > “生成 2027 年工作日志模板”
   > “基于我的幕布工作日志文档，补齐今年剩余工作日节点”

### 方式二：仅作为脚本使用（不装豆包）

不依赖豆包，直接用 Python 运行脚本：

```bash
python scripts/worklog_template.py --year 2026 --output full_2026.md
```

### 安装验证

- 确认 `SKILL.md` 存在且 frontmatter 含 `name` 与 `description` 两个字段。
- 使用豆包技能创建器自带的校验工具：

  ```bash
  python quick_validate.py <你的.user_skills目录>\worklog-template
  ```

  输出 `Skill is valid!` 即通过。

## 使用示例

```bash
# 模式 A：生成 2026 全年骨架（含节假日节点与官方安排备注）
python scripts/worklog_template.py --year 2026 --output full_2026.md

# 模式 B：基于现有文档补齐（保留原文，插入缺失节假日、追加剩余工作日周）
python scripts/worklog_template.py --year 2026 --input existing.md --output filled.md

# 自定义年份：传入外置节假日数据（JSON，结构见脚本内置 HOLIDAYS_2026）
python scripts/worklog_template.py --year 2027 --holidays holidays_2027.json --output full_2027.md

# 节假日节点不带官方安排备注
python scripts/worklog_template.py --year 2026 --no-desc --output full_2026_bare.md
```

输出为幕布（mubu）可导入的 Markdown 骨架：`#` 周标题平铺为第 1 层、`-` 日期节点为第 2 层、`> ` 为周备注。

## 更新节假日数据

国务院办公厅每年 11 月发布次年《关于部分节假日安排的通知》。**新年度使用前必须替换数据**：

- 方式 1：编辑 `scripts/worklog_template.py` 中的 `HOLIDAYS_2026` 字典（改年份、节假日起止、调休上班日）。
- 方式 2：编写外置 JSON（同结构），用 `--holidays` 参数传入，无需改代码。

节假日/调休数据务必以中国政府网（www.gov.cn）当年官方通知为准，并用日历工具逐日核算星期，不要凭记忆。

## 依赖

- Python 3.10+（仅标准库，无第三方依赖）
- 幕布落库功能需要豆包环境中的 mubu-mcp 技能（见 [qingyuanLee/mcp_mubu](https://github.com/qingyuanLee/mcp_mubu)）

## License

保留所有权利。本技能内容与脚本供个人学习与工作使用。
