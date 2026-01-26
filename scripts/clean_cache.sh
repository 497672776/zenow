#!/bin/bash

# Zenow 缓存清理脚本
# 用于清理 ~/.cache/zenow/ 目录中的数据

set -e

ZENOW_CACHE_DIR="$HOME/.cache/zenow"
ZENOW_CONFIG_DIR="$HOME/.config/zenow"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示标题
show_header() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           Zenow 缓存清理工具 v1.0                         ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

# 检查目录是否存在
check_directories() {
    if [ ! -d "$ZENOW_CACHE_DIR" ]; then
        print_warning "缓存目录不存在: $ZENOW_CACHE_DIR"
        return 1
    fi
    return 0
}

# 获取目录大小
get_dir_size() {
    local dir=$1
    if [ -d "$dir" ]; then
        du -sh "$dir" 2>/dev/null | cut -f1
    else
        echo "0B"
    fi
}

# 获取文件数量
get_file_count() {
    local dir=$1
    if [ -d "$dir" ]; then
        find "$dir" -type f 2>/dev/null | wc -l
    else
        echo "0"
    fi
}

# 显示当前缓存状态
show_cache_status() {
    print_info "当前缓存状态:"
    echo ""

    if [ -d "$ZENOW_CACHE_DIR" ]; then
        echo "  📁 缓存根目录: $ZENOW_CACHE_DIR"
        echo "     总大小: $(get_dir_size "$ZENOW_CACHE_DIR")"
        echo ""

        # LLM 模型
        if [ -d "$ZENOW_CACHE_DIR/models/llm" ]; then
            local llm_size=$(get_dir_size "$ZENOW_CACHE_DIR/models/llm")
            local llm_count=$(get_file_count "$ZENOW_CACHE_DIR/models/llm")
            echo "  🤖 LLM 模型目录: $llm_size ($llm_count 个文件)"
        fi

        # Embed 模型
        if [ -d "$ZENOW_CACHE_DIR/models/embed" ]; then
            local embed_size=$(get_dir_size "$ZENOW_CACHE_DIR/models/embed")
            local embed_count=$(get_file_count "$ZENOW_CACHE_DIR/models/embed")
            echo "  📊 Embed 模型目录: $embed_size ($embed_count 个文件)"
        fi

        # Rerank 模型
        if [ -d "$ZENOW_CACHE_DIR/models/rerank" ]; then
            local rerank_size=$(get_dir_size "$ZENOW_CACHE_DIR/models/rerank")
            local rerank_count=$(get_file_count "$ZENOW_CACHE_DIR/models/rerank")
            echo "  🔄 Rerank 模型目录: $rerank_size ($rerank_count 个文件)"
        fi

        # 旧模型目录（兼容性）
        if [ -d "$ZENOW_CACHE_DIR/model" ]; then
            local old_size=$(get_dir_size "$ZENOW_CACHE_DIR/model")
            local old_count=$(get_file_count "$ZENOW_CACHE_DIR/model")
            echo "  📦 旧模型目录: $old_size ($old_count 个文件)"
        fi

        # 数据库
        if [ -d "$ZENOW_CACHE_DIR/data/db" ]; then
            local db_size=$(get_dir_size "$ZENOW_CACHE_DIR/data/db")
            local db_count=$(get_file_count "$ZENOW_CACHE_DIR/data/db")
            echo "  💾 数据库目录: $db_size ($db_count 个文件)"
        fi
    else
        print_warning "缓存目录不存在"
    fi

    # 配置目录
    if [ -d "$ZENOW_CONFIG_DIR" ]; then
        local config_size=$(get_dir_size "$ZENOW_CONFIG_DIR")
        echo ""
        echo "  ⚙️  配置目录: $ZENOW_CONFIG_DIR"
        echo "     大小: $config_size"
    fi

    echo ""
}

# 清理 LLM 模型
clean_llm_models() {
    local dir="$ZENOW_CACHE_DIR/models/llm"
    if [ -d "$dir" ]; then
        print_info "清理 LLM 模型..."
        rm -rf "$dir"/*
        print_success "LLM 模型已清理"
    else
        print_warning "LLM 模型目录不存在"
    fi
}

# 清理 Embed 模型
clean_embed_models() {
    local dir="$ZENOW_CACHE_DIR/models/embed"
    if [ -d "$dir" ]; then
        print_info "清理 Embed 模型..."
        rm -rf "$dir"/*
        print_success "Embed 模型已清理"
    else
        print_warning "Embed 模型目录不存在"
    fi
}

# 清理 Rerank 模型
clean_rerank_models() {
    local dir="$ZENOW_CACHE_DIR/models/rerank"
    if [ -d "$dir" ]; then
        print_info "清理 Rerank 模型..."
        rm -rf "$dir"/*
        print_success "Rerank 模型已清理"
    else
        print_warning "Rerank 模型目录不存在"
    fi
}

# 清理所有模型
clean_all_models() {
    print_info "清理所有模型..."
    clean_llm_models
    clean_embed_models
    clean_rerank_models

    # 清理旧模型目录
    if [ -d "$ZENOW_CACHE_DIR/model" ]; then
        print_info "清理旧模型目录..."
        rm -rf "$ZENOW_CACHE_DIR/model"/*
        print_success "旧模型目录已清理"
    fi
}

# 清理数据库
clean_database() {
    local db_dir="$ZENOW_CACHE_DIR/data/db"
    if [ -d "$db_dir" ]; then
        print_warning "⚠️  警告: 清理数据库将删除所有模型配置和参数设置！"
        read -p "确定要继续吗? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            print_info "清理数据库..."
            rm -rf "$db_dir"/*
            print_success "数据库已清理"
        else
            print_info "已取消数据库清理"
        fi
    else
        print_warning "数据库目录不存在"
    fi
}

# 清理配置文件
clean_config() {
    if [ -d "$ZENOW_CONFIG_DIR" ]; then
        print_warning "⚠️  警告: 清理配置文件将删除后端端口配置！"
        read -p "确定要继续吗? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            print_info "清理配置文件..."
            rm -rf "$ZENOW_CONFIG_DIR"/*
            print_success "配置文件已清理"
        else
            print_info "已取消配置文件清理"
        fi
    else
        print_warning "配置目录不存在"
    fi
}

# 完全清理（删除整个目录）
clean_all() {
    print_error "⚠️  危险操作: 这将删除所有 Zenow 缓存和配置！"
    print_warning "包括:"
    echo "  - 所有模型文件"
    echo "  - 数据库配置"
    echo "  - 应用配置"
    echo ""
    read -p "确定要继续吗? 输入 'YES' 确认: " confirm
    if [[ $confirm == "YES" ]]; then
        print_info "执行完全清理..."

        if [ -d "$ZENOW_CACHE_DIR" ]; then
            rm -rf "$ZENOW_CACHE_DIR"
            print_success "缓存目录已删除: $ZENOW_CACHE_DIR"
        fi

        if [ -d "$ZENOW_CONFIG_DIR" ]; then
            rm -rf "$ZENOW_CONFIG_DIR"
            print_success "配置目录已删除: $ZENOW_CONFIG_DIR"
        fi

        print_success "完全清理完成！"
    else
        print_info "已取消完全清理"
    fi
}

# 显示菜单
show_menu() {
    echo ""
    echo "请选择要执行的操作:"
    echo ""
    echo "  1) 查看缓存状态"
    echo "  2) 清理 LLM 模型"
    echo "  3) 清理 Embed 模型"
    echo "  4) 清理 Rerank 模型"
    echo "  5) 清理所有模型（保留数据库）"
    echo "  6) 清理数据库"
    echo "  7) 清理配置文件"
    echo "  8) 完全清理（删除所有）"
    echo "  0) 退出"
    echo ""
}

# 主函数
main() {
    show_header

    # 检查目录
    if ! check_directories; then
        print_info "Zenow 缓存目录不存在，无需清理"
        exit 0
    fi

    # 显示初始状态
    show_cache_status

    # 主循环
    while true; do
        show_menu
        read -p "请输入选项 [0-8]: " choice

        case $choice in
            1)
                show_cache_status
                ;;
            2)
                clean_llm_models
                ;;
            3)
                clean_embed_models
                ;;
            4)
                clean_rerank_models
                ;;
            5)
                clean_all_models
                ;;
            6)
                clean_database
                ;;
            7)
                clean_config
                ;;
            8)
                clean_all
                ;;
            0)
                print_info "退出清理工具"
                exit 0
                ;;
            *)
                print_error "无效选项，请重新选择"
                ;;
        esac

        # 操作后显示状态
        if [[ $choice != "1" && $choice != "0" ]]; then
            echo ""
            print_info "操作完成后的状态:"
            show_cache_status
        fi
    done
}

# 运行主函数
main
