"""Headless Chromium E2E: independent public LOOP UI -> local synthetic API.

No company credentials, external APIs or production PHISIGHT components.
"""
import json
import threading
from http.server import ThreadingHTTPServer

import pytest
from playwright.sync_api import expect, sync_playwright
from backend.server import Handler


@pytest.fixture(scope="module")
def local_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)


def test_browser_form_runs_api_and_renders_two_rounds(local_url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        javascript_errors = []
        page.on("pageerror", lambda error: javascript_errors.append(str(error)))
        page.goto(local_url, wait_until="networkidle")
        expect(page.locator("#workflow-form")).to_be_visible()
        page.locator("#topic").fill("합성 문서 검수")
        page.locator("#max_rounds").select_option("5")
        page.locator("#run").click()
        expect(page.locator("#status")).to_have_text("조건 충족")
        expect(page.locator("#rounds .round")).to_have_count(2)
        expect(page.locator("#summary")).to_contain_text("총 2회 실행")
        expect(page.locator("#summary")).to_contain_text("최종 승인: 예")
        expect(page.locator("#error")).to_have_text("")
        expect(page.locator("#run")).to_be_enabled()
        assert javascript_errors == []
        browser.close()


def test_browser_max_one_round_is_not_approved(local_url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(local_url, wait_until="networkidle")
        page.locator("#max_rounds").select_option("1")
        page.locator("#run").click()
        expect(page.locator("#status")).to_have_text("반복 상한 도달")
        expect(page.locator("#rounds .round")).to_have_count(1)
        expect(page.locator("#summary")).to_contain_text("최종 승인: 아니요")
        browser.close()


def test_browser_surfaces_api_error_and_recovers_button(local_url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(local_url, wait_until="networkidle")
        page.route("**/api/run", lambda route: route.fulfill(
            status=400, content_type="application/json",
            body=json.dumps({"error": "synthetic test error"})
        ))
        page.locator("#run").click()
        expect(page.locator("#status")).to_have_text("오류")
        expect(page.locator("#error")).to_have_text("synthetic test error")
        expect(page.locator("#run")).to_be_enabled()
        browser.close()
