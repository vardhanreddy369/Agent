from playwright.sync_api import sync_playwright
import time

def run():
    print("Starting browser...")
    with sync_playwright() as p:
        # Launch browser. headless=False means you see it.
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to Google...")
        page.goto("https://www.google.com")
        
        # Wait for potential "Accept Cookies" dialogs or just load
        time.sleep(1)
        
        print("Typing search query...")
        # Common selector for Google search is textarea[name='q'] or input[name='q']
        try:
            page.fill("textarea[name='q']", "Hello World automation agent")
            page.press("textarea[name='q']", "Enter")
        except:
            # Fallback for some variations of Google
            page.fill("input[name='q']", "Hello World automation agent")
            page.press("input[name='q']", "Enter")
            
        print("Search submitted. Waiting for results...")
        time.sleep(3)
        
        # Take a screenshot
        page.screenshot(path="search_results.png")
        print("Screenshot saved to 'search_results.png'.")
        
        print("Closing browser...")
        browser.close()
        print("Done!")

if __name__ == "__main__":
    run()
