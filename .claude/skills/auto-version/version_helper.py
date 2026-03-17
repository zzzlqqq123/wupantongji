#!/usr/bin/env python3
"""
自动版本管理辅助脚本
用于 AI 修改代码后自动更新版本号、文档和创建 Git 提交
"""
import subprocess
import json
import re
import os
from datetime import datetime
from pathlib import Path


def run_command(cmd, cwd=None, capture_output=True):
    """运行 shell 命令"""
    try:
        work_dir = cwd or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=work_dir,
            capture_output=capture_output,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10
        )
        if capture_output:
            return (result.stdout or "").strip(), result.returncode
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"命令超时: {cmd}")
        return "", 1
    except Exception as e:
        print(f"命令执行失败: {cmd}, 错误: {e}")
        return "", 1


def get_current_version():
    """从 config.json 读取当前版本号"""
    try:
        config_path = "config.json"
        if not os.path.exists(config_path):
            return "2.2"  # 默认版本

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            version = config.get('version', '2.2')

            # 如果版本号带 v 前缀，去掉它
            if version.startswith('v'):
                version = version[1:]

            return version
    except Exception as e:
        print(f"读取版本号失败: {e}")
        return "2.2"


def increment_version(version):
    """递增版本号: v2.2 -> v2.3"""
    try:
        # 提取主版本和次版本
        match = re.match(r'(\d+)\.(\d+)', version)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))

            # 递增次版本号
            minor += 1

            new_version = f"{major}.{minor}"
            return new_version
        else:
            # 如果格式不匹配，默认返回 2.3
            return "2.3"
    except Exception as e:
        print(f"递增版本号失败: {e}")
        return "2.3"


def update_config_version(new_version):
    """更新 config.json 中的版本号"""
    try:
        config_path = "config.json"

        # 读取现有配置
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {"misjudgment_types": []}

        # 更新版本号
        config['version'] = new_version
        config['last_updated'] = datetime.now().strftime("%Y-%m-%d")

        # 写回文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"[OK] Updated config.json version: v{new_version}")
        return True
    except Exception as e:
        print(f"Failed to update config.json: {e}")
        return False


def get_git_changes():
    """获取当前的 git 改动"""
    try:
        # 获取改动的文件列表
        output, _ = run_command("git status --porcelain")
        if not output:
            return [], ""

        changed_files = [line.strip().split()[1] if len(line.split()) > 1 else line.strip()
                        for line in output.split('\n') if line.strip()]

        # 获取 git diff（可能失败如果没有 commit 历史）
        diff_output, rc = run_command("git diff HEAD")
        if rc != 0 or not diff_output:
            # 尝试获取 staged changes
            diff_output, rc = run_command("git diff --cached")
            if rc != 0 or not diff_output:
                diff_output = ""

        return changed_files, diff_output
    except Exception as e:
        print(f"获取 git 改动失败: {e}")
        return [], ""


def determine_commit_type(changed_files, diff_content):
    """根据改动内容确定 commit 类型"""
    # 检查是否只修改了文档
    doc_files = ['.md', '.txt', '.rst']
    if all(any(f.endswith(ext) for ext in doc_files) for f in changed_files):
        return "docs"

    # 检查 diff 内容中的关键词
    diff_lower = diff_content.lower()

    if any(kw in diff_lower for kw in ['修复', 'bug', 'fix', '错误', '问题']):
        return "fix"

    if any(kw in diff_lower for kw in ['性能', '优化', 'optimize', 'perf', '加速']):
        return "perf"

    if any(kw in diff_lower for kw in ['重构', 'refactor', '重组', '调整结构']):
        return "refactor"

    # 默认为 feat
    return "feat"


def generate_changelog_entry(new_version, changed_files, diff_content):
    """生成功能更新说明.md 的版本条目"""
    # 确定 commit 类型
    commit_type = determine_commit_type(changed_files, diff_content)

    # 生成标题
    type_map = {
        "feat": "新增功能",
        "fix": "问题修复",
        "perf": "性能优化",
        "refactor": "代码重构",
        "docs": "文档更新"
    }

    entry_title = f"## 🚀 v{new_version} {type_map.get(commit_type, '功能更新')}"

    # 分析改动文件，按模块分类
    modules = {}
    for file_path in changed_files:
        if file_path.startswith('modules/'):
            module = file_path.split('/')[1].replace('.py', '').replace('_', ' ').title()
            modules.setdefault('核心模块', []).append(file_path)
        elif file_path.startswith('utils/'):
            modules.setdefault('工具函数', []).append(file_path)
        elif file_path.endswith('.py'):
            modules.setdefault('主程序', []).append(file_path)
        else:
            modules.setdefault('配置和文档', []).append(file_path)

    # 生成功能描述
    content_parts = []
    content_parts.append(f"### 1. {type_map.get(commit_type, '功能更新')}")

    if commit_type == "feat":
        content_parts.append("\n**功能描述**：")
        content_parts.append("- 新增功能和改进")
        content_parts.append("- 提升用户体验")

    content_parts.append("\n**技术实现**：")
    for module, files in modules.items():
        content_parts.append(f"- **{module}**：{', '.join(files)}")

    content_parts.append(f"\n**更新时间**：{datetime.now().strftime('%Y-%m-%d')}")

    entry_content = "\n".join(content_parts)

    return entry_title, entry_content


def update_changelog(new_version, changed_files, diff_content):
    """更新 功能更新说明.md"""
    try:
        changelog_path = "功能更新说明.md"

        # 生成新版本条目
        entry_title, entry_content = generate_changelog_entry(new_version, changed_files, diff_content)

        # 读取现有内容
        existing_content = ""
        if os.path.exists(changelog_path):
            with open(changelog_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()

        # 构建新内容
        new_content = f"""# 功能更新说明 v{new_version}

## 更新日期
{datetime.now().strftime('%Y-%m-%d')}

---

{entry_title}

{entry_content}

---

{existing_content}
"""

        # 写入文件
        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"[OK] Updated 功能更新说明.md")
        return True
    except Exception as e:
        print(f"Failed to update 功能更新说明.md: {e}")
        return False


def update_readme(new_version):
    """更新 README.md 的版本徽章"""
    try:
        readme_path = "README.md"

        if not os.path.exists(readme_path):
            print("[SKIP] README.md not found")
            return False

        # 读取现有内容
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 更新版本徽章（如果存在）
        # 查找并替换版本徽章（包括链接目标）
        version_badge_pattern = r'\[!\[Version\]\(https://img\.shields\.io/badge/Version-[^)]+\)\]\(功能更新说明\.md\)'

        new_badge = f'[![Version](https://img.shields.io/badge/Version-v{new_version}-blue)](功能更新说明.md)'

        if re.search(version_badge_pattern, content):
            # 替换现有徽章
            content = re.sub(version_badge_pattern, new_badge, content)
        else:
            # 在第一个徽章后插入版本徽章
            # 在 <div align="center"> 后插入
            content = re.sub(
                r'(<div align="center">\n)',
                r'\1\n' + new_badge + '\n',
                content
            )

        # 写回文件
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[OK] Updated README.md version badge")
        return True
    except Exception as e:
        print(f"Failed to update README.md: {e}")
        return False


def generate_commit_message(new_version, changed_files, diff_content):
    """生成 Git commit message"""
    commit_type = determine_commit_type(changed_files, diff_content)

    type_map = {
        "feat": "新增功能",
        "fix": "问题修复",
        "perf": "性能优化",
        "refactor": "代码重构",
        "docs": "文档更新"
    }

    title = f"{commit_type}: v{new_version} - {type_map.get(commit_type, '功能更新')}"

    # 生成详细描述
    details = []
    details.append("详细改动：")

    if commit_type == "feat":
        details.append("- 新增功能模块")
    elif commit_type == "fix":
        details.append("- 修复已知问题")
    elif commit_type == "perf":
        details.append("- 优化性能表现")
    elif commit_type == "refactor":
        details.append("- 重构代码结构")
    elif commit_type == "docs":
        details.append("- 更新项目文档")

    details.append("\n技术实现：")
    for file_path in changed_files[:5]:  # 最多显示5个文件
        details.append(f"- {file_path}")

    if len(changed_files) > 5:
        details.append(f"- 等共 {len(changed_files)} 个文件")

    details.append(f"\n文件变更：")
    for file_path in changed_files:
        details.append(f"- {file_path}")

    body = "\n".join(details)

    commit_message = f"""{title}

{body}

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"""

    return commit_message


def create_git_commit(commit_message):
    """创建 Git commit"""
    try:
        # 添加所有改动
        run_command("git add .")

        # 创建 commit（使用临时文件避免编码问题）
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            f.write(commit_message)
            temp_file = f.name

        try:
            run_command(f'git commit -F "{temp_file}"', capture_output=False)
            print(f"[OK] Created Git commit")
            return True
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass

    except Exception as e:
        print(f"Failed to create Git commit: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Auto Version Management Skill")
    print("=" * 60)

    # 1. 检查是否有改动
    changed_files, diff_content = get_git_changes()
    if not changed_files:
        print("[SKIP] No changes detected")
        return

    print(f"\n[INFO] Detected {len(changed_files)} changed file(s):")
    for f in changed_files[:10]:
        print(f"  - {f}")
    if len(changed_files) > 10:
        print(f"  ... and {len(changed_files) - 10} more")

    # 2. 读取当前版本号
    current_version = get_current_version()
    print(f"\n[INFO] Current version: v{current_version}")

    # 3. 递增版本号
    new_version = increment_version(current_version)
    print(f"[INFO] New version: v{new_version}")

    # 4. 更新 config.json
    if not update_config_version(new_version):
        return

    # 5. 更新 功能更新说明.md
    if not update_changelog(new_version, changed_files, diff_content):
        return

    # 6. 更新 README.md
    update_readme(new_version)

    # 7. 生成 commit message
    commit_message = generate_commit_message(new_version, changed_files, diff_content)

    print("\n" + "=" * 60)
    print("Commit Message:")
    print("=" * 60)
    print(commit_message)
    print("=" * 60 + "\n")

    # 8. 创建 Git commit
    if not create_git_commit(commit_message):
        return

    print("\n[SUCCESS] Auto version management completed!")
    print(f"   Version: v{current_version} -> v{new_version}")
    print(f"   Files: {len(changed_files)}")
    print(f"   Type: {determine_commit_type(changed_files, diff_content)}")


if __name__ == "__main__":
    main()
