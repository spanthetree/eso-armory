from __future__ import annotations

import re

import pytest
from playwright.sync_api import Browser, Page, expect


def upload_all_fixtures(page: Page, fixtures_dir) -> None:
    page.get_by_text("Select Files").click()
    page.locator('input[x-ref="iasyncInput"]').set_input_files(str(fixtures_dir / "iasync.lua"))
    page.locator('input[x-ref="wwInput"]').set_input_files(str(fixtures_dir / "WizardsWardrobe.lua"))
    page.locator('input[x-ref="ttcLookupInput"]').set_input_files(str(fixtures_dir / "ItemLookUpTable_EN.lua"))
    page.locator('input[x-ref="ttcPriceInput"]').set_input_files(str(fixtures_dir / "PriceTableNA.lua"))
    page.get_by_role("button", name="Load Files").click()
    expect(page.get_by_role("heading", name="Test Character One")).to_be_visible(timeout=15000)


@pytest.mark.ui
def test_first_load_shows_upload_path_not_source(page: Page, app_url: str):
    page.goto(app_url)

    expect(page.get_by_text("Load Your ESO Data")).to_be_visible(timeout=15000)
    expect(page.locator("body")).not_to_contain_text("iasync_data =")
    expect(page.locator("body")).not_to_contain_text("<!DOCTYPE html>")
    expect(page.locator("body")).not_to_contain_text("function armory()")
    expect(page.locator("body")).not_to_contain_text("return {")


@pytest.mark.ui
def test_upload_fixture_renders_armory(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    expect(page.get_by_text("@test_account · NA · 6 items")).to_be_visible()
    page.get_by_role("button", name="Inventory").click()
    expect(page.get_by_text("Mock Potion")).to_be_visible()
    page.get_by_role("button", name="Collections").click()
    page.get_by_role("button", name=re.compile(r"Dungeons")).click()
    expect(page.get_by_text("Mock Set")).to_be_visible()


@pytest.mark.ui
def test_upload_non_json_error_is_actionable(page: Page, app_url: str, fixtures_dir):
    page.route(
        "**/api/upload?**",
        lambda route: route.fulfill(
            status=502,
            content_type="text/html",
            body="<html><body>Bad Gateway</body></html>",
        ),
    )
    page.goto(app_url)
    page.get_by_text("Select Files").click()
    page.locator('input[x-ref="iasyncInput"]').set_input_files(str(fixtures_dir / "iasync.lua"))
    page.get_by_role("button", name="Load Files").click()

    expect(page.get_by_text(re.compile(r"Upload returned 502")).first).to_be_visible(timeout=15000)
    expect(page.locator("body")).not_to_contain_text("JSON.parse")


@pytest.mark.ui
def test_upload_invalid_json_error_hides_parser_jargon(page: Page, app_url: str, fixtures_dir):
    page.route(
        "**/api/upload?**",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body="<html><body>Not JSON</body></html>",
        ),
    )
    page.goto(app_url)
    page.get_by_text("Select Files").click()
    page.locator('input[x-ref="iasyncInput"]').set_input_files(str(fixtures_dir / "iasync.lua"))
    page.get_by_role("button", name="Load Files").click()

    expect(page.get_by_text(re.compile(r"Upload returned invalid JSON response")).first).to_be_visible(timeout=15000)
    expect(page.locator("body")).not_to_contain_text("unexpected character")
    expect(page.locator("body")).not_to_contain_text("JSON.parse")


@pytest.mark.ui
def test_achievements_tab_shows_error_when_endpoint_fails(page: Page, app_url: str, fixtures_dir):
    page.route(
        "**/api/achievements?**",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"error":"Achievements backend unavailable"}',
        ),
    )
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    page.get_by_role("button", name="Achievements").click()

    expect(page.get_by_text("User data not loaded")).to_be_visible(timeout=15000)
    expect(page.get_by_text("Achievements backend unavailable")).to_be_visible(timeout=15000)


@pytest.mark.ui
def test_collections_tab_shows_error_when_endpoint_fails(page: Page, app_url: str, fixtures_dir):
    page.route(
        "**/api/stickerbook?**",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"error":"Collections backend unavailable"}',
        ),
    )
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    page.get_by_role("button", name="Collections").click()

    expect(page.get_by_text("User data not loaded")).to_be_visible(timeout=15000)
    expect(page.get_by_text("Collections backend unavailable")).to_be_visible(timeout=15000)


@pytest.mark.ui
def test_collections_tooltip_shows_bonus_lookup_error(page: Page, app_url: str, fixtures_dir):
    page.route(
        "**/api/set_bonus?**",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"error":"Set bonuses blocked"}',
        ),
    )
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    page.get_by_role("button", name="Collections").click()
    page.get_by_role("button", name=re.compile(r"Dungeons")).click()
    page.get_by_text("Mock Set").first.hover()

    expect(page.get_by_text("Set bonuses blocked")).to_be_visible(timeout=15000)


@pytest.mark.ui
def test_inventory_filters_and_character_detail(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)

    page.get_by_role("button", name="Inventory").click()
    page.get_by_placeholder("Search items…").fill("potion")
    expect(page.get_by_text("Mock Potion").first).to_be_visible()
    expect(page.get_by_text("Mock Sword").first).not_to_be_visible()
    page.get_by_role("button", name="Group by Set").click()
    page.get_by_placeholder("Search items…").fill("sword")
    expect(page.get_by_text("Mock Set").first).to_be_visible()

    page.get_by_role("button", name="Characters", exact=True).click()
    page.get_by_role("heading", name="Test Character One").click()
    detail = page.locator('div[x-show="selectedChar && !compareMode && !ssMode"]')
    expect(detail.get_by_text("Current Build")).to_be_visible()
    expect(detail.get_by_text("Character Inventory")).to_be_visible()
    expect(detail.get_by_text("WW Saved Builds")).to_be_visible()
    page.get_by_text("Mock Raid Build").click()
    expect(page.get_by_text("Mock Sword").first).to_be_visible()
    expect(page.get_by_text("Champion Points").first).to_be_visible()


@pytest.mark.ui
def test_share_code_joins_uploaded_workspace(page: Page, browser: Browser, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    page.get_by_role("button", name="Share").click()
    page.get_by_role("button", name="Create Share Code").click()
    expect(page.get_by_text("Share code created.")).to_be_visible(timeout=15000)
    code = next(
        text for text in page.locator("code").all_text_contents()
        if re.fullmatch(r"[A-Z0-9]{4}-[A-Z0-9]{4}", text.strip())
    ).strip()
    assert code

    other_context = browser.new_context()
    try:
        other = other_context.new_page()
        other.goto(app_url)
        expect(other.get_by_text("Load Your ESO Data")).to_be_visible(timeout=15000)
        other.get_by_role("button", name="Share").click()
        share_modal = other.locator('div[x-show="shareOpen"]')
        share_modal.get_by_placeholder("ABCD-EFGH").fill(code)
        share_modal.get_by_role("button", name="Join").click()
        expect(other.get_by_text("Joined shared workspace.")).to_be_visible(timeout=15000)
        expect(other.get_by_role("heading", name="Test Character One")).to_be_visible(timeout=15000)
        expect(other.get_by_text("@test_account · NA · 6 items")).to_be_visible()
    finally:
        other_context.close()
