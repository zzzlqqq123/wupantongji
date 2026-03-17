"""
版本信息工具模块
用于从Git获取版本信息
"""
import subprocess
import os
from datetime import datetime


def get_git_commit_count():
    """
    获取Git提交总数

    Returns:
        int: 提交次数，如果获取失败返回0
    """
    try:
        # 获取项目根目录
        # 从当前文件向上查找.git目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)

        # 检查是否在git仓库中
        git_dir = os.path.join(project_root, '.git')
        if not os.path.exists(git_dir):
            return 0

        # 获取提交总数
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return int(result.stdout.strip())
        return 0
    except Exception:
        return 0


def get_current_date():
    """
    获取当前日期（年月日格式）

    Returns:
        str: 格式为YYYYMMDD的日期字符串
    """
    return datetime.now().strftime("%Y%m%d")


def get_version_string():
    """
    获取版本号字符串（格式：年月日/第几次commit）

    Returns:
        str: 版本号字符串，例如 "20250112/142"
    """
    commit_count = get_git_commit_count()
    date_str = get_current_date()

    if commit_count > 0:
        return f"{date_str}/{commit_count}"
    else:
        # 如果无法获取git提交数，只返回日期
        return f"{date_str}/0"


def get_formatted_version():
    """
    获取格式化的版本号（用于显示）

    Returns:
        str: 格式化的版本号，例如 "v2025.01.12 (build 142)"
    """
    commit_count = get_git_commit_count()
    date_str = datetime.now().strftime("%Y.%m.%d")

    if commit_count > 0:
        return f"v{date_str} (build {commit_count})"
    else:
        return f"v{date_str} (dev)"
