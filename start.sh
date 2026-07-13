#!/bin/bash
# 美股投资研究平台 — 一键启动脚本

PYTHON="/c/Users/Yyh20/anaconda3/python.exe"
BACKEND_DIR="/c/Users/Yyh20/Desktop/stock/backend"
FRONTEND_DIR="/c/Users/Yyh20/Desktop/stock/frontend"

echo "========================================="
echo "  美股投资研究平台 — Stock Research"
echo "========================================="
echo ""

# 启动后端
echo "[1/2] 启动后端 API 服务 (port 8000)..."
cd "$BACKEND_DIR"
$PYTHON -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 2

# 检查后端是否启动成功
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "  ✓ 后端已启动 → http://localhost:8000"
    echo "  ✓ API 文档 → http://localhost:8000/docs"
else
    echo "  ✗ 后端启动失败"
    exit 1
fi

# 启动前端
echo "[2/2] 启动前端开发服务器 (port 5173)..."
cd "$FRONTEND_DIR"
npx vite --host &
FRONTEND_PID=$!
sleep 3

echo ""
echo "========================================="
echo "  ✓ 全部启动成功!"
echo ""
echo "  前端页面: http://localhost:5173"
echo "  API 文档: http://localhost:8000/docs"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "========================================="

# 捕获退出信号，清理进程
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "已停止所有服务"
    exit 0
}

trap cleanup INT TERM

# 等待子进程
wait
