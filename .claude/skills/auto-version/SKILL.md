---
name: auto-version
description: Automatically manage version numbers, update documentation, and create git commits after code modifications. Analyzes changes and generates changelogs. Use this skill whenever code files are modified.
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# 自动版本管理 Skill

## 功能概述

此 skill 会在每次 AI agent 修改代码文件后自动触发，执行以下操作：

1. **检测改动**：分析 git diff，识别修改的文件
2. **版本管理**：自动递增版本号（v2.2 → v2.3）
3. **更新文档**：
   - 更新 `config.json` 中的版本号
   - 在 `功能更新说明.md` 顶部添加新版本条目
   - 更新 `README.md` 的版本徽章
4. **创建提交**：自动生成详细的 commit message 并创建 git commit

## 触发方式

### 自动触发（推荐）
- 每次 AI agent 使用 `Edit` 或 `Write` 工具修改代码文件后自动触发
- 通过 `after:write` hook 实现
- 无需任何手动操作

### 手动调用
- 也可以通过 `/auto-version` 命令手动触发
- 适用于需要立即提交当前改动的情况

## 版本号规则

### 格式
- 使用简单递增格式：`v{major}.{minor}`
- 例如：v2.2 → v2.3 → v2.4

### 递增策略
- **新功能**：递增版本号（v2.2 → v2.3）
- **Bug 修复**：递增版本号（v2.2 → v2.3）
- **性能优化**：递增版本号（v2.2 → v2.3）
- **代码重构**：递增版本号（v2.2 → v2.3）
- **文档更新**：递增版本号（v2.2 → v2.3）

**注**：当前版本管理策略不区分 PATCH 和 MINOR，所有改动都递增次版本号。

## Commit 类型判断

Skill 会自动分析代码改动，判断 commit 类型：

| 类型 | 前缀 | 触发条件 |
|------|------|----------|
| 新功能 | `feat` | 默认类型，添加新功能或改进 |
| 问题修复 | `fix` | 关键词：修复、bug、fix、错误、问题 |
| 性能优化 | `perf` | 关键词：性能、优化、optimize、perf、加速 |
| 代码重构 | `refactor` | 关键词：重构、refactor、重组、调整结构 |
| 文档更新 | `docs` | 只修改了文档文件（.md、.txt、.rst） |

## Commit Message 格式

自动生成的 commit message 遵循以下格式：

```
{type}: v{version} - {brief_description}

详细改动：
- [改动点1]
- [改动点2]

技术实现：
- [技术细节1]
- [技术细节2]

文件变更：
- [file1.py]
- [file2.py]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### 示例

```
feat: v2.3 - 新增功能

详细改动：
- 新增功能模块

技术实现：
- modules/gui_manager.py
- main.py

文件变更：
- modules/gui_manager.py
- main.py
- config.json
- 功能更新说明.md
- README.md

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## 文档更新详情

### config.json
更新或添加以下字段：
```json
{
  "version": "2.3",
  "last_updated": "2026-01-22"
}
```

### 功能更新说明.md
在文件顶部插入新版本条目：
```markdown
# 功能更新说明 v2.3

## 更新日期
2026-01-22

---

## 🚀 v2.3 新增功能

### 1. 新增功能

**功能描述**：
- 功能描述内容

**技术实现**：
- modules/xxx.py
- main.py

**更新时间**：2026-01-22

---

[保留所有历史内容...]
```

### README.md
更新或添加版本徽章：
```markdown
[![Version](https://img.shields.io/badge/Version-v2.3-blue)](功能更新说明.md)
```

## 实现细节

### 核心脚本
- **位置**：`.claude/skills/auto-version/version_helper.py`
- **功能**：
  - 读取和递增版本号
  - 分析 git diff
  - 生成 changelog
  - 更新文档文件
  - 创建 git commit

### 执行流程
```python
1. get_git_changes()          # 检测改动
2. get_current_version()      # 读取当前版本
3. increment_version()        # 递增版本号
4. update_config_version()    # 更新 config.json
5. update_changelog()         # 更新功能更新说明.md
6. update_readme()            # 更新 README.md
7. generate_commit_message()  # 生成 commit message
8. create_git_commit()        # 创建 git commit
```

## 使用示例

### 场景 1：AI 修复 Bug

**用户请求**：
```
修复误判率计算不更新的问题
```

**AI 执行**：
1. 分析代码，找到 bug
2. 使用 Edit 工具修改 `modules/statistics.py`
3. **Hook 自动触发**
4. 自动执行版本管理流程

**结果**：
```
fix: v2.3 - 问题修复

详细改动：
- 修复已知问题

技术实现：
- modules/statistics.py

文件变更：
- modules/statistics.py
- config.json
- 功能更新说明.md
- README.md

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### 场景 2：AI 添加新功能

**用户请求**：
```
新增图片旋转功能
```

**AI 执行**：
1. 实现旋转逻辑
2. 修改 `modules/gui_manager.py` 和 `main.py`
3. **Hook 自动触发**
4. 自动执行版本管理流程

**结果**：
```
feat: v2.3 - 新增功能

详细改动：
- 新增功能模块

技术实现：
- modules/gui_manager.py
- main.py

文件变更：
- modules/gui_manager.py
- main.py
- config.json
- 功能更新说明.md
- README.md

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## 配置要求

### Hooks 配置
在 `.claude/settings.local.json` 中配置：
```json
{
  "hooks": {
    "after:write": [
      {
        "description": "Auto version management",
        "command": "python .claude/skills/auto-version/version_helper.py"
      }
    ]
  }
}
```

### 权限配置
在 `.claude/settings.local.json` 中添加权限：
```json
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git diff)",
      "Bash(git add)",
      "Bash(git commit)",
      "Bash(python .claude/skills/auto-version/*)",
      "Read(*)",
      "Write(*.md)",
      "Edit(*.md)",
      "Read(config.json)",
      "Write(config.json)"
    ]
  }
}
```

## 故障排除

### Skill 没有自动触发
**检查**：
1. `.claude/settings.local.json` 是否正确配置了 hooks
2. `version_helper.py` 是否有执行权限
3. 运行 `python .claude/skills/auto-version/version_helper.py` 手动测试

### 版本号没有更新
**检查**：
1. `config.json` 是否存在且可写
2. 版本号格式是否正确（应为 "2.2" 而非 "v2.2"）
3. 查看脚本输出的错误信息

### Commit 创建失败
**检查**：
1. Git 仓库是否已初始化
2. 是否有 git 配置（user.name, user.email）
3. 运行 `git status` 查看仓库状态

### Changelog 格式错误
**检查**：
1. `功能更新说明.md` 是否存在
2. 文件编码是否为 UTF-8
3. 手动运行脚本查看详细错误

## 回滚操作

如果自动版本管理出现问题，可以手动回滚：

```bash
# 撤销最后一次 commit（保留改动）
git reset --soft HEAD~1

# 恢复文件到上一个版本
git checkout HEAD~1 -- config.json 功能更新说明.md README.md

# 检查状态
git status
```

## 高级用法

### 自定义版本号
手动指定版本号（需要修改 `version_helper.py`）：
```python
def increment_version(version):
    # 自定义递增逻辑
    return "2.5"  # 固定版本号
```

### 跳过版本管理
如果不想为某个改动创建版本，可以：
1. 使用 `git commit --amend` 合并到最后一个 commit
2. 或者修改 `version_helper.py` 添加文件过滤逻辑

### 调试模式
手动运行脚本查看详细输出：
```bash
python .claude/skills/auto-version/version_helper.py
```

## 最佳实践

1. **代码改动后及时提交**：Hook 会在每次 Edit/Write 后触发，确保改动及时记录
2. **检查生成的 commit message**：虽然自动生成，但建议定期检查质量
3. **保持 .gitignore 更新**：确保不会意外提交敏感文件
4. **定期备份**：在重要改动前，建议先创建分支或标签
5. **团队协作**：如果是团队项目，确保所有成员都了解此 skill 的行为

## 参考资料

- [Claude Code Skills 文档](https://code.claude.com/docs/en/skills)
- [Hooks 文档](https://code.claude.com/docs/en/hooks)
- 项目内部文档：`CLAUDE.md`、`Git使用说明.md`

---

**版本**：v1.0
**创建日期**：2026-01-21
**维护者**：Claude Code + 用户
