@echo off
chcp 65001 >nul
echo =========================================
echo   美股投资研究平台 — Stock Research
echo =========================================
echo.

echo [1/2] 启动后端 API 服务 (port 8000)...
start "Stock-Backend" cmd /c "cd /d backend && C:\Users\Yyh20\anaconda3\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] 启动前端开发服务器 (port 5173)...
start "Stock-Frontend" cmd /c "cd /d frontend && npx vite --host"

timeout /t 3 /nobreak >nul

echo.
echo =========================================
echo   ✓ 全部启动成功!
echo.
echo   前端页面: http://localhost:5173
echo   API 文档: http://localhost:8000/docs
echo.
echo   关闭窗口即可停止服务
echo =========================================
pause
