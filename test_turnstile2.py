import asyncio
import nodriver as uc

TURNSTILE_SITEKEY = "0x4AAAAAAA1jQEh8YFk064tz"

HTML_PAGE = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
</head>
<body>
    <div id="turnstile-widget"></div>
    <script>
        window.addEventListener('load', function() {{
            if (typeof turnstile !== 'undefined') {{
                turnstile.render('#turnstile-widget', {{
                    sitekey: '{TURNSTILE_SITEKEY}',
                    callback: function(token) {{
                        document.title = 'TURNSTILE_TOKEN:' + token;
                    }},
                    'error-callback': function(e) {{
                        document.title = 'TURNSTILE_ERROR:' + (e || 'unknown');
                    }}
                }});
            }} else {{
                document.title = 'TURNSTILE_ERROR:NOT_LOADED';
            }}
        }});
        setTimeout(function() {{
            if (!document.title.startsWith('TURNSTILE_')) {{
                document.title = 'TURNSTILE_ERROR:TIMEOUT';
            }}
        }}, 30000);
    </script>
</body>
</html>"""

async def main():
    browser = await uc.start()
    
    # Use data URL instead of file://
    import urllib.parse
    data_url = "data:text/html;charset=utf-8," + urllib.parse.quote(HTML_PAGE)
    page = await browser.get(data_url)
    
    for i in range(30):
        await page.sleep(1)
        title = await page.evaluate("document.title")
        print(f"Title: {title}")
        if title and title.startswith("TURNSTILE_TOKEN:"):
            token = title.replace("TURNSTILE_TOKEN:", "")
            print(f"SUCCESS! Token ({len(token)} chars): {token[:50]}...")
            break
        elif title and "ERROR" in title:
            print(f"Error state: {title}")
            break
    
    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
