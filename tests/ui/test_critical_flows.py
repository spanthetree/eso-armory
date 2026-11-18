from __future__ import annotations

import re

import pytest
from playwright.sync_api import Browser, Page, expect


def upload_all_fixtures(page: Page, fixtures_dir) -> None:
    page.get_by_role("button", name=re.compile(r"Select files")).click()
    page.locator("#up-iasync").set_input_files(str(fixtures_dir / "iasync.lua"))
    page.locator("#up-ww").set_input_files(str(fixtures_dir / "WizardsWardrobe.lua"))
    page.get_by_role("button", name="Load Files").click()
    expect(page.get_by_role("button", name=re.compile("Test Character One"))).to_be_visible(timeout=15000)


def open_tab(page: Page, name: str) -> None:
    page.get_by_role("tab", name=name.upper()).click()


def open_character(page: Page, name: str = "Test Character One") -> None:
    open_tab(page, "Characters")
    page.get_by_role("button", name=re.compile(name)).click()
    expect(page.get_by_role("heading", name=name)).to_be_visible()


def open_view(page: Page, view: str) -> None:
    page.get_by_role("group", name="Character view").get_by_role("button", name=view.upper()).click()


@pytest.mark.ui
def test_first_load_shows_upload_path_not_source(page: Page, app_url: str):
    page.goto(app_url)

    expect(page.get_by_text("Load Your ESO Data", exact=False)).to_be_visible(timeout=15000)
    expect(page.locator("body")).not_to_contain_text("iasync_data =")
    expect(page.locator("body")).not_to_contain_text("<!DOCTYPE html>")
    expect(page.locator("body")).not_to_contain_text("import {")
    expect(page.locator("body")).not_to_contain_text("$state(")


@pytest.mark.ui
def test_upload_fixture_renders_armory(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    expect(page.get_by_text("@test_account · NA · 6 items")).to_be_visible()
    open_tab(page, "Inventory")
    expect(page.get_by_text("Mock Potion").first).to_be_visible()
    open_tab(page, "Collections")
    page.get_by_role("navigation").get_by_role("button", name=re.compile(r"Dungeons")).click()
    expect(page.get_by_text("Mock Set").first).to_be_visible()


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
    page.get_by_role("button", name=re.compile(r"Select files")).click()
    page.locator("#up-iasync").set_input_files(str(fixtures_dir / "iasync.lua"))
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
    page.get_by_role("button", name=re.compile(r"Select files")).click()
    page.locator("#up-iasync").set_input_files(str(fixtures_dir / "iasync.lua"))
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
    open_tab(page, "Achievements")

    expect(page.get_by_text("User data not loaded")).to_be_visible(timeout=15000)
    expect(page.get_by_text("Achievements backend unavailable")).to_be_visible(timeout=15000)


@pytest.mark.ui
def test_achievements_tab_renders_summary_and_category(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    open_tab(page, "Achievements")

    expect(page.get_by_text("Achievement Points Earned")).to_be_visible(timeout=15000)
    nav = page.get_by_role("navigation", name="Achievement categories")
    nav.get_by_role("button", name="General").click()
    expect(page.get_by_role("listitem").filter(has_text="Mock Account Achievement")).to_be_visible()
    expect(page.get_by_label("Filter achievements")).to_be_visible()


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
    open_tab(page, "Collections")

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
    open_tab(page, "Collections")
    page.get_by_role("navigation").get_by_role("button", name=re.compile(r"Dungeons")).click()
    page.get_by_text("Mock Set", exact=True).first.hover()

    expect(page.get_by_text("Set bonuses blocked")).to_be_visible(timeout=15000)


@pytest.mark.ui
def test_inventory_filters_and_character_views(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)

    open_tab(page, "Inventory")
    page.get_by_placeholder("Search items…").fill("potion")
    expect(page.get_by_text("Mock Potion").first).to_be_visible()
    expect(page.get_by_text("Mock Sword")).to_have_count(0)
    page.get_by_role("button", name="Group by set").click()
    page.get_by_placeholder("Search items…").fill("sword")
    expect(page.get_by_text("Mock Set").first).to_be_visible()

    open_character(page)
    # Equipped panel: 7 apparel + 4 accessories (costume, neck, 2 rings) + 6 weapon/poison slots
    expect(page.locator(".slot")).to_have_count(17)
    expect(page.get_by_text("Front bar")).to_be_visible()
    expect(page).to_have_url(re.compile(r"#/characters/char-a$"))

    open_view(page, "Bags")
    expect(page).to_have_url(re.compile(r"#/characters/char-a/bags$"))
    expect(page.get_by_text("Mock Potion").first).to_be_visible()

    open_view(page, "Wardrobe")
    page.get_by_role("option", name=re.compile("Mock Raid Build")).click()
    expect(page.get_by_role("heading", name="CHAMPION POINTS")).to_be_visible()
    page.go_back()
    expect(page).to_have_url(re.compile(r"/bags$"))


@pytest.mark.ui
def test_compare_exports_and_imports_build(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    open_character(page)
    open_view(page, "Compare")
    expect(page.get_by_role("heading", name="CURRENT BUILD")).to_be_visible()
    expect(page.get_by_role("heading", name="IMPORTED BUILD")).to_be_visible()

    page.get_by_role("button", name="Export build code").click()
    code_el = page.locator("code", has_text=re.compile(r"^[A-Z0-9]{4}-[A-Z0-9]{4}$")).first
    expect(code_el).to_be_visible(timeout=15000)
    code = code_el.text_content().strip()

    page.get_by_label("Build code to import").fill(code)
    page.get_by_role("button", name="Import by code").click()
    expect(page.get_by_role("button", name="Delete imported build")).to_be_visible(timeout=15000)
    expect(page.get_by_role("heading", name=re.compile(r"^IMPORTED · "))).to_be_visible()
    expect(page.get_by_text("You own every piece of this build.")).to_be_visible()

    page.get_by_role("button", name="Delete imported build").click()
    expect(page.get_by_role("heading", name="IMPORTED BUILD")).to_be_visible(timeout=15000)


@pytest.mark.ui
def test_superstar_view_asks_for_screenshot(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    open_character(page)
    open_view(page, "SuperStar")
    expect(page.get_by_text("to paste a screenshot", exact=False)).to_be_visible()


@pytest.mark.ui
def test_share_code_joins_uploaded_workspace(page: Page, browser: Browser, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    page.get_by_role("button", name="Share", exact=True).click()
    page.get_by_role("button", name="Create share code").click()
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
        expect(other.get_by_text("Load Your ESO Data", exact=False)).to_be_visible(timeout=15000)
        other.get_by_role("button", name="Share", exact=True).click()
        dialog = other.get_by_role("dialog", name="Share Workspace")
        dialog.get_by_placeholder("ABCD-EFGH").fill(code)
        dialog.get_by_role("button", name="Join").click()
        expect(other.get_by_text("Joined shared workspace.")).to_be_visible(timeout=15000)
        expect(other.get_by_role("button", name=re.compile("Test Character One"))).to_be_visible(timeout=15000)
        expect(other.get_by_text("@test_account · NA · 6 items")).to_be_visible()
    finally:
        other_context.close()


@pytest.mark.ui
def test_inventory_strip_and_saved_filter_chip(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    open_tab(page, "Inventory")

    page.get_by_label("Item types and locations").get_by_role("button", name=re.compile("Consumables")).click()
    expect(page.get_by_text("Mock Potion").first).to_be_visible()
    expect(page.get_by_text("Mock Sword")).to_have_count(0)

    page.get_by_role("button", name="+ Save filter").click()
    page.get_by_label("Saved filter name").fill("Potions only")
    page.get_by_role("button", name="Save", exact=True).click()
    page.get_by_role("button", name="Clear").click()
    expect(page.get_by_text("Mock Sword").first).to_be_visible()

    expect(page.get_by_role("button", name="Potions only", exact=True)).to_be_visible()
    page.reload()  # saved chips persist; the URL keeps the Inventory tab open
    page.get_by_role("button", name="Potions only", exact=True).click(timeout=15000)
    expect(page.get_by_text("Mock Sword")).to_have_count(0)
    expect(page.get_by_text("Mock Potion").first).to_be_visible()


@pytest.mark.ui
def test_achievements_search_spans_categories(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    open_tab(page, "Achievements")

    expect(page.get_by_text("RECENT ACHIEVEMENTS")).to_be_visible(timeout=15000)
    page.get_by_label("Search achievements").fill("mock")
    # Like the game, the search narrows the tree and lists the matches of the first matching category.
    expect(page.get_by_role("navigation", name="Achievement categories").get_by_role("button", name="Summary")).to_have_count(0)
    expect(page.get_by_text("Mock Account Achievement")).to_be_visible()


@pytest.mark.ui
def test_collections_piece_grid_filters(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    open_tab(page, "Collections")
    page.get_by_role("navigation").get_by_role("button", name=re.compile(r"Dungeons")).click()

    pieces = page.get_by_role("list").get_by_role("listitem")
    expect(pieces).to_have_count(2)
    expect(page.get_by_label("Mock Cuirass (not collected)")).to_be_visible()

    page.get_by_label("Show Locked").uncheck()
    expect(pieces).to_have_count(1)
    expect(page.get_by_label("Mock Sword", exact=True)).to_be_visible()


@pytest.mark.ui
def test_ui_style_switch_is_remembered(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    open_tab(page, "Achievements")
    expect(page.get_by_text("Achievement Points Earned")).to_be_visible(timeout=15000)

    page.get_by_label("UI style").select_option("simple")
    expect(page.get_by_role("heading", name="SUMMARY")).to_be_visible()
    page.reload()
    open_tab(page, "Achievements")
    expect(page.get_by_role("heading", name="SUMMARY")).to_be_visible(timeout=15000)
    expect(page.locator("html")).to_have_attribute("data-ui", "simple")


def test_collections_book_switcher(page: Page, app_url: str, fixtures_dir):
    page.goto(app_url)
    upload_all_fixtures(page, fixtures_dir)
    open_tab(page, "Collections")
    expect(page).to_have_url(re.compile(r"#/collections$"))  # no collectibles in the fixture: Set Items
    expect(page.get_by_label("Mock Cuirass (not collected)").or_(page.get_by_text("Set Items Collected"))).to_be_visible()

    page.get_by_role("group", name="Collections book").get_by_role("button", name="Collectibles").click()
    expect(page).to_have_url(re.compile(r"#/collections/collectibles$"))
    expect(page.get_by_text("Collectibles need iasync 1.9.0")).to_be_visible()
