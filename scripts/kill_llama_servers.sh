#!/bin/bash
#
# 杀除所有 llama-server 进程
# 用法: ./kill_llama_servers.sh [选项]
#
# 选项:
#   -f, --force    强制杀除（使用 SIGKILL）
#   -h, --help     显示帮助信息
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认使用 SIGTERM（优雅退出）
SIGNAL="TERM"
FORCE=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            SIGNAL="KILL"
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -f, --force    强制杀除（使用 SIGKILL）"
            echo "  -h, --help     显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0              # 优雅地停止所有 llama-server"
            echo "  $0 --force      # 强制杀除所有 llama-server"
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知选项 $1${NC}"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  清理 llama-server 进程${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 查找所有 llama-server 进程
PIDS=$(pgrep -f "llama-server" || true)

if [ -z "$PIDS" ]; then
    echo -e "${GREEN}✓ 没有找到运行中的 llama-server 进程${NC}"
    exit 0
fi

# 统计进程数量
COUNT=$(echo "$PIDS" | wc -l)
echo -e "${YELLOW}找到 $COUNT 个 llama-server 进程:${NC}"
echo ""

# 显示进程详情
echo -e "${BLUE}PID     端口    命令${NC}"
echo "----------------------------------------"
for PID in $PIDS; do
    # 获取进程信息
    CMD=$(ps -p $PID -o args= 2>/dev/null || echo "N/A")

    # 尝试获取端口号
    PORT=$(lsof -Pan -p $PID -i 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1 || echo "N/A")

    printf "%-7s %-7s %s\n" "$PID" "$PORT" "$(echo $CMD | cut -c1-60)"
done
echo ""

# 确认操作
if [ "$FORCE" = true ]; then
    echo -e "${RED}⚠️  将强制杀除所有进程（SIGKILL）${NC}"
else
    echo -e "${YELLOW}将优雅地停止所有进程（SIGTERM）${NC}"
fi

read -p "确认继续？[y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}操作已取消${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}正在停止进程...${NC}"

# 杀除进程
SUCCESS_COUNT=0
FAIL_COUNT=0

for PID in $PIDS; do
    if kill -$SIGNAL $PID 2>/dev/null; then
        echo -e "${GREEN}✓ 已停止进程 $PID${NC}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "${RED}✗ 无法停止进程 $PID${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

echo ""

# 等待进程退出
if [ "$FORCE" = false ]; then
    echo -e "${BLUE}等待进程退出...${NC}"
    sleep 2

    # 检查是否还有残留进程
    REMAINING=$(pgrep -f "llama-server" || true)
    if [ -n "$REMAINING" ]; then
        echo -e "${YELLOW}⚠️  发现残留进程，尝试强制杀除...${NC}"
        for PID in $REMAINING; do
            kill -KILL $PID 2>/dev/null && echo -e "${GREEN}✓ 强制停止进程 $PID${NC}"
        done
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 成功停止: $SUCCESS_COUNT 个进程${NC}"
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}✗ 失败: $FAIL_COUNT 个进程${NC}"
fi
echo -e "${BLUE}========================================${NC}"

# 最终验证
FINAL_CHECK=$(pgrep -f "llama-server" || true)
if [ -z "$FINAL_CHECK" ]; then
    echo -e "${GREEN}✓ 所有 llama-server 进程已清理完毕${NC}"
    exit 0
else
    echo -e "${RED}⚠️  仍有进程残留，请手动检查${NC}"
    exit 1
fi
