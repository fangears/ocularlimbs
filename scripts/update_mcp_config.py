#!/usr/bin/env python3
"""
更新 Claude Desktop MCP 配置
"""

import json
import os
from pathlib import Path


def update_mcp_config():
    """更新 MCP 配置文件"""

    claude_dir = Path.home() / '.claude'
    config_file = claude_dir / 'claude_desktop_config.json'

    # 确保目录存在
    claude_dir.mkdir(parents=True, exist_ok=True)

    # 读取现有配置
    config = {}
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

    # 确保 mcpServers 节点存在
    if 'mcpServers' not in config:
        config['mcpServers'] = {}

    # 添加 OcularLimbs MCP 服务器
    config['mcpServers']['ocularlimbs'] = {
        "command": "python",
        "args": ["-m", "ocularlimbs.mcp_server"],
        "env": {
            "OCULARLIMBS_HOME": str(Path.home() / '.ocularlimbs')
        }
    }

    # 写入配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"✓ MCP 配置已更新: {config_file}")


if __name__ == '__main__':
    update_mcp_config()
