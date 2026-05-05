"""
Dumps the game map HTML structure so we can write a proper DOM-based detector.
    python inspect_dom.py
"""
import asyncio, os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT); sys.path.insert(0, ROOT)

from config import CDP_URL
from core.browser import BrowserSession

async def main():
    browser = BrowserSession()
    if not await browser.attach(CDP_URL):
        print("Cannot attach to Chrome."); return

    page = browser.page
    print(f"Page: {page.url}\n")

    # Dump the full map table HTML (first 6000 chars)
    html = await page.evaluate("() => document.body.innerHTML")
    snippet = html[:6000]
    with open("screenshots/dom_dump.txt", "w", encoding="utf-8") as f:
        f.write(html)
    print("Full HTML saved to screenshots/dom_dump.txt")
    print("\n--- First 3000 chars ---")
    print(snippet[:3000])

    # Try to find the map table
    tables = await page.evaluate("""() => {
        const tables = document.querySelectorAll('table');
        return Array.from(tables).map((t, i) => ({
            index: i,
            rows: t.rows.length,
            cols: t.rows[0] ? t.rows[0].cells.length : 0,
            id: t.id,
            className: t.className,
            snippet: t.innerHTML.substring(0, 200)
        }));
    }""")
    print(f"\n--- Found {len(tables)} tables ---")
    for t in tables:
        print(f"  [{t['index']}] id={t['id']!r} class={t['className']!r} rows={t['rows']} cols={t['cols']}")
        print(f"       {t['snippet'][:120]}")

    # Find all links/cells that look like sector numbers
    links = await page.evaluate("""() => {
        const links = document.querySelectorAll('a');
        return Array.from(links)
            .filter(a => /^\\d+$/.test(a.innerText.trim()))
            .slice(0, 20)
            .map(a => ({
                text: a.innerText.trim(),
                href: a.href,
                class: a.className,
                parent: a.parentElement ? a.parentElement.tagName : ''
            }));
    }""")
    print(f"\n--- Sector number links (first 20) ---")
    for l in links:
        print(f"  [{l['text']:>4}]  href={l['href']}  class={l['class']!r}  parent={l['parent']}")

    await browser.close()

asyncio.run(main())
input("\nPress Enter to exit")
