from scripts.backlinks import Vendor, link_vendors

SNAP = (Vendor("SnapTrade", "https://snaptrade.com/", r"\bSnapTrade\b"),)


def test_links_first_prose_mention_only():
    text = "Sync pulls SnapTrade data.\nSnapTrade again."
    assert link_vendors(text, SNAP) == (
        "Sync pulls [SnapTrade](https://snaptrade.com/) data.\nSnapTrade again."
    )


def test_skips_front_matter_headings_code_and_html():
    text = "\n".join(
        [
            "---",
            "description: SnapTrade sync",
            "---",
            "## SnapTrade",
            "<img alt='SnapTrade'>",
            '<div align="center">',
            "",
            "_Hero tagline naming SnapTrade._",
            "",
            "</div>",
            "```bash",
            "echo SnapTrade",
            "```",
            "Use `SnapTrade` via SnapTrade.",
        ]
    )
    assert link_vendors(text, SNAP).splitlines()[-1] == (
        "Use `SnapTrade` via [SnapTrade](https://snaptrade.com/)."
    )
    assert link_vendors(text, SNAP).splitlines()[:-1] == text.splitlines()[:-1]


def test_existing_link_earlier_in_file_wins_and_result_is_idempotent():
    text = "Brokerage through [SnapTrade](https://snaptrade.com/).\nSnapTrade later."
    assert link_vendors(text, SNAP) == text
    linked = link_vendors("SnapTrade first.\nSnapTrade later.", SNAP)
    assert link_vendors(linked, SNAP) == linked


def test_nested_fence_and_any_html_block_stay_protected():
    text = "\n".join(
        [
            "````md",
            "```bash",
            "echo SnapTrade",
            "```",
            "SnapTrade inside the outer fence.",
            "````",
            "```",
            "```python inside a fence is content, not a closer",
            "SnapTrade still fenced.",
            "```",
            "<Section>",
            "SnapTrade inside a section.",
            "</Section>",
            "<ul><li>SnapTrade inside a list</li></ul>",
            "<img alt='void tags do not open a block'>",
            "SnapTrade in prose.",
        ]
    )
    assert link_vendors(text, SNAP).splitlines()[-1] == (
        "[SnapTrade](https://snaptrade.com/) in prose."
    )
    assert link_vendors(text, SNAP).splitlines()[:-1] == text.splitlines()[:-1]


def test_image_alt_text_is_protected_but_is_not_a_vendor_link():
    text = "![SnapTrade logo](logo.png)\nSync pulls SnapTrade data."
    assert link_vendors(text, SNAP) == (
        "![SnapTrade logo](logo.png)\nSync pulls [SnapTrade](https://snaptrade.com/) data."
    )


def test_doc_link_with_other_text_does_not_count_as_vendor_link():
    text = "See [live sync](docs/live-sync.md) for SnapTrade."
    assert link_vendors(text, SNAP) == (
        "See [live sync](docs/live-sync.md) for [SnapTrade](https://snaptrade.com/)."
    )
