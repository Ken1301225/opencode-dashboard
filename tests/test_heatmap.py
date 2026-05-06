import re
import unittest
from datetime import date
from unittest.mock import patch

import opencode_dashboard


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class FixedDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 5, 6)


def terminal_width(text, mahjong_width):
    width = 0
    for ch in ANSI_RE.sub("", text):
        code = ord(ch)
        if 0x1F000 <= code <= 0x1F02F:
            width += mahjong_width
        else:
            width += 1
    return width


class HeatmapRenderTests(unittest.TestCase):
    def render_lines(self, trends, mahjong_width="1"):
        with patch.object(opencode_dashboard, "date", FixedDate), \
                patch.object(opencode_dashboard, "_wcwidth", None), \
                patch.dict("os.environ", {"DASHBOARD_MAHJONG_WIDTH": mahjong_width}, clear=False):
            output = opencode_dashboard.render(trends, [], "test")
        return output.splitlines()

    def test_zero_activity_days_render_with_mahjong_blank_tile(self):
        trends = [
            {"day": "2026-04-24", "cnt": 1, "total": 10, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-04-25", "cnt": 1, "total": 0, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-04-26", "cnt": 1, "total": 20, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
        ]

        week_line = next(line for line in self.render_lines(trends) if "Apr 20" in line)

        self.assertIn("🀆", week_line)
        self.assertNotIn("·", week_line)

    def test_heatmap_week_rows_keep_constant_terminal_width_with_single_width_mahjong(self):
        self.assert_week_rows_keep_constant_terminal_width("1", 1)

    def test_heatmap_week_rows_keep_constant_terminal_width_with_double_width_mahjong(self):
        self.assert_week_rows_keep_constant_terminal_width("2", 2)

    def assert_week_rows_keep_constant_terminal_width(self, env_width, terminal_mahjong_width):
        trends = [
            {"day": "2026-04-23", "cnt": 1, "total": 0, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-04-24", "cnt": 1, "total": 10, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-04-25", "cnt": 1, "total": 0, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-04-26", "cnt": 1, "total": 20, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-04-27", "cnt": 1, "total": 30, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-04-28", "cnt": 1, "total": 0, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-04-29", "cnt": 1, "total": 40, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-04-30", "cnt": 1, "total": 0, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-05-01", "cnt": 1, "total": 50, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-05-02", "cnt": 1, "total": 0, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-05-03", "cnt": 1, "total": 60, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-05-04", "cnt": 1, "total": 0, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-05-05", "cnt": 1, "total": 70, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
            {"day": "2026-05-06", "cnt": 1, "total": 0, "input_t": 0, "output_t": 0, "cache_read": 0, "cost": 0},
        ]

        week_lines = [
            line for line in self.render_lines(trends, env_width)
            if line.startswith("  │  Apr ") or line.startswith("  │  May ")
        ]

        self.assertGreaterEqual(len(week_lines), 3)
        self.assertEqual({terminal_width(line, terminal_mahjong_width) for line in week_lines}, {78})


class ModelFilterTests(unittest.TestCase):
    def test_filters_placeholder_and_zero_token_models(self):
        visible = opencode_dashboard.is_visible_model_name

        self.assertFalse(visible("<synthetic>", 100))
        self.assertFalse(visible("unknown", 100))
        self.assertFalse(visible("openai/?", 100))
        self.assertFalse(visible("openai/gpt-5.4", 0))
        self.assertTrue(visible("deepseek-v4-pro", 100))
        self.assertTrue(visible("custom/gpt-5.3-codex", 100))


if __name__ == "__main__":
    unittest.main()
