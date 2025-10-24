#!/bin/bash
# -----------------------------
# 自动创建 venv 虚拟环境并安装 requirements.txt
# -----------------------------

# 虚拟环境名称
VENV_NAME="venv"

# 创建虚拟环境
python3 -m venv $VENV_NAME

# 激活虚拟环境
source $VENV_NAME/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装 requirements.txt
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt 文件未找到！"
fi

echo "✅ 虚拟环境创建完成并安装依赖。激活方式：source $VENV_NAME/bin/activate"
