import unittest

from scripts.resolve_paper_title import MetadataParser, ResolutionError, metadata_url, normalize_paper_url, normalize_title


class ResolvePaperTitleTests(unittest.TestCase):
    def test_prefers_citation_title(self) -> None:
        parser = MetadataParser()
        parser.feed('<html><head><title>Fallback</title><meta name="citation_title" content="Actual Paper"></head></html>')
        self.assertEqual(parser.best_title(), "Actual Paper")

    def test_normalizes_arxiv_pdf_for_metadata(self) -> None:
        self.assertEqual(metadata_url("https://arxiv.org/pdf/2501.12345v2.pdf"), "https://arxiv.org/abs/2501.12345")

    def test_normalizes_hugging_face_paper(self) -> None:
        self.assertEqual(metadata_url("https://huggingface.co/papers/2501.12345"), "https://arxiv.org/abs/2501.12345")

    def test_rejects_non_http_url(self) -> None:
        with self.assertRaises(ResolutionError):
            normalize_paper_url("file:///tmp/paper.pdf")

    def test_cleans_title_whitespace_and_entities(self) -> None:
        self.assertEqual(normalize_title("  A &amp; B\n Paper  "), "A & B Paper")


if __name__ == "__main__":
    unittest.main()
