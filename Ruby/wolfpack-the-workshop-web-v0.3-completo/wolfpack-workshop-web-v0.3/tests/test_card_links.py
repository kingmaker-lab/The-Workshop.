"""Security and navigation regression checks for the static WolfPack v0.3 source.

The *live* Worker is v0.4.0. Run only as source verification:
do not deploy this old HTML over the newer live Worker.
"""
from html.parser import HTMLParser
from pathlib import Path
from unittest import TestCase, main

INDEX = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")

EXPECTED = {
    "https://workshop-labs.pages.dev/projects/ares/": "Abrir o laboratório ARES Protocol",
    "https://cerberus.wolfpackworkshop.workers.dev/": "Abrir o laboratório CERBERUS de Arquitetura de Software",
}


class CardLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards = []
        self.links_depth = 0
        self.nested_anchors = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            if self.links_depth:
                self.nested_anchors = True
            self.links_depth += 1
            if "app-card" in attrs.get("class", "").split():
                self.cards.append(attrs)

    def handle_endtag(self, tag):
        if tag == "a":
            self.links_depth -= 1


class TestWolfPackLinks(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = CardLinks()
        cls.page.feed(INDEX)

    def test_two_external_cards_have_known_https_destinations(self):
        selected = [x for x in self.page.cards if x.get("href") in EXPECTED]
        self.assertEqual(len(selected), 2)
        for attrs in selected:
            self.assertEqual(attrs["aria-label"], EXPECTED[attrs["href"]])
            self.assertEqual(attrs.get("referrerpolicy"), "no-referrer")
            self.assertEqual(set(attrs.get("rel", "").split()), {"noopener", "noreferrer"})

    def test_no_nested_anchors(self):
        self.assertFalse(self.page.nested_anchors, "interactive links cannot nest")

    def test_cerberus_identity_matches_software_architecture(self):
        self.assertIn("ENGENHARIA / ARQUITETURA DE SOFTWARE", INDEX)
        self.assertNotIn("ORQUESTRAÇÃO</span>", INDEX)

    def test_other_applications_remain(self):
        for token in [
            "Ruby Protocol",
            "VULPES-77",
            "ARGUS",
            "RAVEN",
            "HTTP Auditor",
            "Crypto Lab",
        ]:
            self.assertIn(token, INDEX)


if __name__ == "__main__":
    main()
