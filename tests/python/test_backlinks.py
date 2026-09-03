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


def test_doc_link_with_other_text_does_not_count_as_vendor_link():
    text = "See [live sync](docs/live-sync.md) for SnapTrade."
    assert link_vendors(text, SNAP) == (
        "See [live sync](docs/live-sync.md) for [SnapTrade](https://snaptrade.com/)."
    )
