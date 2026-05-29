"""
Strategy C: Aggressive asset blocking to protect 1GB RAM.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

BLOCKED_RESOURCE_TYPES = {
  "image",
  "stylesheet",
  "font",
  "media",
  "imageset",
  "websocket",
  "manifest",
  "texttrack",
  "eventsource",
  "beacon",
}

BLOCKED_URL_PATTERNS = [
  "google-analytics",
  "googletagmanager",
  "facebook.com",
  "doubleclick.net",
  "hotjar.com",
  "intercom.io",
  "segment.com",
  "mixpanel.com",
  "amplitude.com",
  "cdn.jsdelivr",
  "recaptcha",
  "captcha",
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".webp",
  ".woff",
  ".woff2",
  ".ttf",
  ".eot",
  ".mp4",
  ".mp3",
  ".avi",
  ".mov",
]


async def create_memory_safe_context(playwright):
  """
  Create a Playwright browser context optimized for 1GB RAM.
  Blocks all non-essential resources aggressively.
  """
  browser = await playwright.chromium.launch(
    headless=True,
    args=[
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--disable-extensions",
      "--disable-plugins",
      "--disable-images",
      "--disable-javascript-harmony-shipping",
      "--memory-pressure-off",
      "--max_old_space_size=256",
      "--single-process",
      "--no-zygote",
    ],
  )
  context = await browser.new_context(
    viewport={"width": 1280, "height": 720},
    java_script_enabled=True,
    bypass_csp=True,
    extra_http_headers={
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36"
      )
    },
  )

  async def block_resources(route, request):
    if request.resource_type in BLOCKED_RESOURCE_TYPES:
      await route.abort()
      return
    url = request.url.lower()
    if any(p in url for p in BLOCKED_URL_PATTERNS):
      await route.abort()
      return
    await route.continue_()

  await context.route("**/*", block_resources)
  return browser, context


async def safe_page_fetch(
  url: str,
  wait_selector: str = None,
  timeout: int = 15000,
) -> Optional[str]:
  """
  Fetch a JS-heavy page with memory-safe Playwright.
  Returns HTML string or None on failure.
  Always cleans up browser resources.
  """
  try:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
      browser, context = await create_memory_safe_context(pw)
      try:
        page = await context.new_page()
        await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        if wait_selector:
          try:
            await page.wait_for_selector(wait_selector, timeout=5000)
          except Exception:
            pass
        html = await page.content()
        return html
      finally:
        await context.close()
        await browser.close()
  except Exception as e:
    logger.warning("Playwright fetch failed for %s: %s", url[:50], e)
    return None
