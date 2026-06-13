from pathlib import Path

from django.test import SimpleTestCase

from medicines.reference_parser.parser import extract_variants_from_page

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ExtractVariantsFromPageTests(SimpleTestCase):
    def setUp(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("Playwright is not installed")

        playwright_cm = sync_playwright()
        playwright = playwright_cm.__enter__()
        self.addCleanup(playwright_cm.__exit__, None, None, None)

        try:
            browser = playwright.chromium.launch()
        except Exception:
            self.skipTest("Chromium browser is not installed")
        self.addCleanup(browser.close)

        self.page = browser.new_page()

    def test_extracts_all_rows_from_the_form_selection_table(self):
        html = (FIXTURES / "reference_rls_filter_table.html").read_text()
        self.page.set_content(html)

        variants = extract_variants_from_page(self.page)

        self.assertEqual(
            variants,
            [
                {"form": "капсулы", "dosage": "50 мг"},
                {"form": "таблетки, покрытые пленочной оболочкой", "dosage": "100 мг"},
                {
                    "form": "раствор для внутривенного и внутримышечного введения",
                    "dosage": "50 мг/мл",
                },
                {"form": "крем для наружного применения", "dosage": "5%"},
                {"form": "гель для наружного применения", "dosage": "2.5%"},
                {"form": "суппозитории ректальные", "dosage": "100 мг"},
            ],
        )

    def test_extracts_form_rows_without_a_dosage_column(self):
        html = (FIXTURES / "reference_rls_filter_table_no_dosage.html").read_text()
        self.page.set_content(html)

        variants = extract_variants_from_page(self.page)

        self.assertEqual(
            variants,
            [
                {"form": "раствор для приема внутрь", "dosage": ""},
                {"form": "таблетки для рассасывания", "dosage": ""},
            ],
        )

    def test_extracts_a_variant_per_dosage_for_rows_with_several_dosages(self):
        html = (FIXTURES / "reference_rls_filter_table_multi_dosage.html").read_text()
        self.page.set_content(html)

        variants = extract_variants_from_page(self.page)

        self.assertIn({"form": "гель для наружного применения", "dosage": "1%"}, variants)
        self.assertIn({"form": "гель для наружного применения", "dosage": "5%"}, variants)
        self.assertIn({"form": "суппозитории ректальные", "dosage": "50 мг"}, variants)
        self.assertIn({"form": "суппозитории ректальные", "dosage": "100 мг"}, variants)
        self.assertIn({"form": "раствор для внутримышечного введения", "dosage": "25 мг/мл"}, variants)
        self.assertIn({"form": "раствор для внутримышечного введения", "dosage": "75 мг/3 мл"}, variants)
        self.assertEqual(len(variants), 13)
