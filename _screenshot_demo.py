"""用 Playwright 截图验证 Streamlit Demo UI"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()

    # 首页
    print('Loading home page...')
    page.goto('http://localhost:8502/', wait_until='networkidle', timeout=30000)
    time.sleep(5)  # Wait for streamlit to render
    page.screenshot(path='D:/shFintech/_demo_screenshot_home.png', full_page=True)
    print('Home screenshot saved')

    # AI 问答页
    page.goto('http://localhost:8502/', wait_until='networkidle')
    time.sleep(3)
    # 通过 URL 参数或点击切换
    # Streamlit 不会通过 URL 切换页面，只能通过 sidebar
    # 试用 query param 切换
    print('Trying AI page...')

    browser.close()
    print('Done')
