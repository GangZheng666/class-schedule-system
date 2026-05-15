"""课表系统 - 启动入口"""
import sys
import os

# Hack: 在导入 streamlit 之前修复 importlib.metadata.version 的问题
def hack_streamlit_version():
    import importlib.metadata
    
    # 保存原始的 version 函数
    original_version = importlib.metadata.version
    
    def patched_version(package_name):
        if package_name == "streamlit":
            # 硬编码一个版本号
            return "1.57.0"
        return original_version(package_name)
    
    # 替换 version 函数
    importlib.metadata.version = patched_version

# Hack: 设置环境变量来禁用 developmentMode
os.environ["STREAMLIT_SERVER_PORT"] = "8501"
os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

if __name__ == "__main__":
    hack_streamlit_version()
    
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    import webbrowser
    import threading
    
    def open_browser():
        import time
        time.sleep(2)
        webbrowser.open("http://localhost:8501")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", os.path.join(app_dir, "app.py")]
    stcli.main()
