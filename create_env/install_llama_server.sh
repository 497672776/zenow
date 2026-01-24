#!/bin/bash

###############################################################################
# llama-server 自动安装脚本
#
# 功能：
#   1. 下载 llama.cpp 源码
#   2. 编译 llama-server（支持 CPU/GPU）
#   3. 安装到 ~/.local/bin
#   4. 验证安装
###############################################################################

# set -e  # 遇到错误立即退出

INSTALL_DIR="$HOME/.local/bin"
BUILD_DIR="/tmp/llama.cpp-build"
REPO_URL="https://github.com/ggerganov/llama.cpp.git"

echo "=========================================="
echo "🚀 llama-server 自动安装脚本"
echo "=========================================="
echo ""

# 检测 GPU 支持
detect_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        echo "✅ 检测到 NVIDIA GPU"
        USE_CUDA=ON
        GPU_LAYERS="-ngl 35"
    else
        echo "⚠️  未检测到 NVIDIA GPU，使用 CPU 版本"
        USE_CUDA=OFF
        GPU_LAYERS=""
    fi
}

# 安装依赖
install_dependencies() {
    echo "📦 检查依赖..."

    # 检查必要工具
    for cmd in git cmake make g++; do
        if ! command -v $cmd &> /dev/null; then
            echo "❌ 缺少依赖: $cmd"
            echo "请运行: sudo apt-get install -y build-essential cmake git libcurl4-openssl-dev"
            exit 1
        fi
    done

    # 检查 libcurl 开发库
    if ! pkg-config --exists libcurl 2>/dev/null; then
        echo "❌ 缺少依赖: libcurl-dev"
        echo "请运行: sudo apt-get install -y libcurl4-openssl-dev"
        exit 1
    fi

    echo "✅ 依赖检查通过"
}

# 克隆仓库
clone_repo() {
    echo ""
    echo "📥 下载 llama.cpp 源码..."

    # 清理旧的构建目录
    if [ -d "$BUILD_DIR" ]; then
        echo "🧹 清理旧的构建目录..."
        rm -rf "$BUILD_DIR"
    fi

    # 克隆最新代码
    git clone --depth 1 "$REPO_URL" "$BUILD_DIR"
    cd "$BUILD_DIR"

    echo "✅ 源码下载完成"
}

# 编译 llama-server
compile_server() {
    echo ""
    echo "🔨 编译 llama-server..."

    cd "$BUILD_DIR"

    # 创建构建目录
    mkdir -p build
    cd build

    # CMake 配置
    if [ "$USE_CUDA" = "ON" ]; then
        echo "🎮 使用 CUDA 加速编译..."
        cmake .. -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
    else
        echo "💻 使用 CPU 编译..."
        cmake .. -DCMAKE_BUILD_TYPE=Release
    fi

    # 编译（使用所有 CPU 核心）
    NPROC=$(nproc)
    echo "⚙️  使用 $NPROC 核心并行编译..."
    make llama-server -j$NPROC

    echo "✅ 编译完成"
}

# 安装到系统
install_binary() {
    echo ""
    echo "📦 安装 llama-server..."

    # 确保安装目录存在
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$HOME/.local/lib"

    # 复制可执行文件
    cp "$BUILD_DIR/build/bin/llama-server" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/llama-server"

    # 复制所有共享库到 ~/.local/lib
    echo "📚 复制共享库..."
    cp "$BUILD_DIR/build/bin/"*.so* "$HOME/.local/lib/" 2>/dev/null || true

    # 创建启动包装脚本（设置 LD_LIBRARY_PATH）
    cat > "$INSTALL_DIR/llama-server-wrapper" <<'EOF'
#!/bin/bash
export LD_LIBRARY_PATH="$HOME/.local/lib:$LD_LIBRARY_PATH"
exec "$HOME/.local/bin/llama-server" "$@"
EOF
    chmod +x "$INSTALL_DIR/llama-server-wrapper"

    echo "✅ 已安装到: $INSTALL_DIR/llama-server"
    echo "✅ 共享库已安装到: $HOME/.local/lib"
    echo "💡 建议使用包装脚本: llama-server-wrapper"
}

# 验证安装
verify_installation() {
    echo ""
    echo "🔍 验证安装..."

    if [ -f "$INSTALL_DIR/llama-server" ]; then
        VERSION=$("$INSTALL_DIR/llama-server" --version 2>&1 | head -1 || echo "unknown")
        echo "✅ llama-server 安装成功"
        echo "   版本: $VERSION"
        echo "   路径: $INSTALL_DIR/llama-server"

        # 检查是否在 PATH 中
        if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
            echo "✅ $INSTALL_DIR 已在 PATH 中"
        else
            echo "⚠️  $INSTALL_DIR 不在 PATH 中"
            echo "   请添加到 ~/.bashrc:"
            echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
        fi
    else
        echo "❌ 安装失败"
        exit 1
    fi
}

# 清理构建目录
cleanup() {
    echo ""
    echo "🧹 清理构建文件..."
    rm -rf "$BUILD_DIR"
    echo "✅ 清理完成"
}

# 主流程
main() {
    # detect_gpu
    # install_dependencies
    # clone_repo
    # compile_server
    install_binary
    verify_installation
    # cleanup

    echo ""
    echo "=========================================="
    echo "🎉 llama-server 安装成功！"
    echo "=========================================="
    echo ""
    echo "使用方法:"
    echo "  llama-server -m /path/to/model.gguf -c 4096 $GPU_LAYERS"
    echo ""
    echo "查看帮助:"
    echo "  llama-server --help"
    echo ""
}

# 运行主流程
main
