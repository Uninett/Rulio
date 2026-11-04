import re

from django.template.loader import render_to_string


def address_row(**draft_info):
    return {
        "id": 7,
        "cells": ["web-server", "10.0.0.1/32", []],
        "can_write": True,
        "is_global": False,
        **draft_info,
    }


def render_row(row, object_type="addresses"):
    return render_to_string("partials/objects/_tableRow.html", {"row": row, "object_type": object_type, "headers": []})


def main_row_tag(html):
    start = html.index('<tr id="row-7"')
    return html[start : html.index(">", start)]


def main_row_classes(html):
    return re.search(r'class="([^"]*)"', main_row_tag(html)).group(1).split()


def cell_tags(html):
    return [html[start : html.index(">", start)] for start in _find_all(html, "<td class=")]


def _find_all(html, text):
    start = html.find(text)
    while start != -1:
        yield start
        start = html.find(text, start + 1)


def test_table_row_adds_diff_classes_to_the_row():
    html = render_row(address_row(diff_classes="row-diff-added"))

    assert "row-diff-added" in main_row_tag(html)


def test_table_row_marks_only_the_cells_with_a_was_value():
    html = render_row(address_row(diff_classes="row-diff-changed", was=[None, "Was: 10.0.0.2/32", None]))

    name_cell, address_cell, tags_cell, _actions_cell = cell_tags(html)
    assert "cell-diff-changed" in address_cell
    assert 'title="Was: 10.0.0.2/32"' in address_cell
    assert "cell-diff-changed" not in name_cell
    assert "cell-diff-changed" not in tags_cell
    assert 'title="10.0.0.1/32 (Was: 10.0.0.2/32)"' in html


def test_table_row_without_draft_info_has_no_diff_markup():
    html = render_row(address_row())

    assert "row-diff" not in html
    assert "cell-diff-changed" not in html
    assert "Was:" not in html
    assert main_row_classes(html) == ["main-row"]


def test_table_row_shows_a_removed_row_read_only():
    row = address_row(diff_classes="row-diff-removed", is_removed=True, inspect_url="/filters/7/rules/")
    html = render_row(row, object_type="filters")

    assert "readonly-row" in main_row_classes(html)
    assert "actions-btn-disabled" in html
    assert "Deleted in your unsaved changes" in html
    assert 'hx-get="' not in html
    assert "data-selector-url" not in html
    assert "ondblclick" not in main_row_tag(html)
    assert "navigateFromRow" not in html
    assert "expandRow('7')" in main_row_tag(html)


def test_table_row_keeps_navigation_on_a_live_filter_row():
    html = render_row(address_row(inspect_url="/filters/7/rules/"), object_type="filters")

    assert "navigateFromRow" in main_row_tag(html)


def test_table_row_does_not_let_a_removed_rule_be_dragged():
    html = render_row(address_row(diff_classes="row-diff-removed", is_removed=True), object_type="rules")

    assert 'draggable="true"' not in html
    assert "readonly-row" in main_row_classes(html)


def test_draft_actions_name_the_table_to_refresh():
    html = render_to_string(
        "partials/_draftActions.html",
        {
            "can_write_current_tenant": True,
            "draft_label": "rule changes",
            "draft_discard_handler": "discardDraftChanges",
            "draft_save_handler": "saveDraftChanges",
            "draft_table_id": "rules-table",
        },
    )

    discard = html[html.index("draft-discard-btn") : html.index("</button>", html.index("draft-discard-btn"))]
    save = html[html.index("draft-save-btn") : html.index("</button>", html.index("draft-save-btn"))]
    assert 'data-draft-table="rules-table"' in discard
    assert 'data-draft-label="rule changes"' in discard
    assert "discardDraftChanges(this)" in discard
    assert 'data-draft-table="rules-table"' in save
    assert "saveDraftChanges(this)" in save


def test_draft_actions_leave_out_the_table_when_not_given():
    html = render_to_string(
        "partials/_draftActions.html",
        {"can_write_current_tenant": True, "draft_label": "filter changes for eth0"},
    )

    assert "data-draft-table" not in html
