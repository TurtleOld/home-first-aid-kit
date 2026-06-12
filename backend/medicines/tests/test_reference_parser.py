from pathlib import Path

from django.test import SimpleTestCase

from medicines.reference_parser.parser import parse_detail_html, parse_variants_html


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ReferenceParserTests(SimpleTestCase):
    def test_parse_variants_from_fixture(self):
        html = (FIXTURES / "reference_page.html").read_text()

        result = parse_variants_html(html, source_url="https://example.test/drug")

        self.assertEqual(result["trade_name"], "Тестовое средство")
        self.assertFalse(result["single_variant"])
        self.assertIn({"form": "таблетки, покрытые оболочкой", "dosage": "200 мг"}, result["variants"])
        self.assertIn({"form": "капсулы", "dosage": "300 мг"}, result["variants"])
        self.assertIn({"form": "гель", "dosage": "2%"}, result["variants"])

    def test_pharmacy_price_rows_are_not_treated_as_variants(self):
        html = (FIXTURES / "reference_page.html").read_text()

        result = parse_variants_html(html, source_url="https://example.test/drug")

        for variant in result["variants"]:
            self.assertNotIn("Производитель", variant["form"])

    def test_single_variant_never_returns_empty_variants(self):
        html = (FIXTURES / "reference_single_page.html").read_text()

        result = parse_variants_html(html)

        self.assertTrue(result["single_variant"])
        self.assertEqual(len(result["variants"]), 1)
        self.assertEqual(result["variants"][0]["form"], "сироп")
        self.assertEqual(result["variants"][0]["dosage"], "5 мл")

    def test_parse_detail_from_fixture(self):
        html = (FIXTURES / "reference_page.html").read_text()

        result = parse_detail_html(
            html,
            source_url="https://example.test/drug",
            form="капсулы",
            dosage="300 мг",
        )

        self.assertTrue(result["selected_matches_description"]["overall"])
        self.assertEqual(result["fields"]["trade_name"], "Тестовое средство")
        self.assertEqual(result["fields"]["active_ingredient"], "тестолол")
        self.assertIn("storage_conditions", result["reference_data"])
        self.assertIn("Условия хранения", result["reference_data"]["sections"])
