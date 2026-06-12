from django.test import SimpleTestCase

from core.utils import default_renderer_classes


class DefaultRendererClassesTests(SimpleTestCase):
    def test_includes_browsable_api_renderer_when_debug(self):
        self.assertEqual(
            default_renderer_classes(debug=True),
            [
                "rest_framework.renderers.JSONRenderer",
                "rest_framework.renderers.BrowsableAPIRenderer",
            ],
        )

    def test_excludes_browsable_api_renderer_when_not_debug(self):
        self.assertEqual(
            default_renderer_classes(debug=False),
            ["rest_framework.renderers.JSONRenderer"],
        )


class SettingsRendererWiringTests(SimpleTestCase):
    def test_settings_renderer_classes_come_from_helper(self):
        from django.conf import settings

        configured = settings.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"]
        self.assertIn(
            configured,
            [default_renderer_classes(debug=True), default_renderer_classes(debug=False)],
        )
