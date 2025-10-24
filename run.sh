#!/bin/bash
# -----------------------------
# 启动项目
# -----------------------------

# 虚拟环境名称
VENV_NAME="venv"
# 激活虚拟环境
source $VENV_NAME/bin/activate

# 执行 main.py
python main.py
