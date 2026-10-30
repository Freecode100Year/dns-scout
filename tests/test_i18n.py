import json
import string
import tempfile
import unittest
from pathlib import Path

from scout.i18n import (
    REGIONS,
    MESSAGES,
    format_message,
    load_language,
    localize_error,
    region_labels,
    resolve_language,
    save_language,
)


class LocalizationTests(unittest.TestCase):
    def test_catalogs_have_matching_keys_and_format_fields(self):
        self.assertEqual(set(MESSAGES['zh-CN']), set(MESSAGES['en']))
        formatter = string.Formatter()
        for key in MESSAGES['zh-CN']:
            zh_fields = {field for _, field, _, _ in formatter.parse(MESSAGES['zh-CN'][key]) if field}
            en_fields = {field for _, field, _, _ in formatter.parse(MESSAGES['en'][key]) if field}
            self.assertEqual(zh_fields, en_fields, key)

    def test_saved_language_overrides_system_language(self):
        self.assertEqual(resolve_language('en', 'zh_CN'), 'en')

    def test_system_language_selects_english_and_unknown_defaults_to_chinese(self):
        self.assertEqual(resolve_language(None, 'en_US'), 'en')
        self.assertEqual(resolve_language(None, 'fr_FR'), 'zh-CN')

    def test_invalid_saved_language_falls_back_to_supported_system_language(self):
        self.assertEqual(resolve_language('fr', 'en_GB'), 'en')

    def test_language_preference_round_trips(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'settings.json'
            save_language(path, 'en')
            self.assertEqual(load_language(path, 'zh_CN'), 'en')

    def test_corrupt_or_unsupported_preference_uses_system_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'settings.json'
            path.write_text('{bad', encoding='utf-8')
            self.assertEqual(load_language(path, 'en_US'), 'en')
            path.write_text(json.dumps({'language': 'fr'}), encoding='utf-8')
            self.assertEqual(load_language(path, 'ja_JP'), 'zh-CN')

    def test_every_region_has_two_labels_and_preserves_source_key(self):
        expected = {
            'global': '全球', 'fastest': '网站最快列表', 'china': '中国',
            'hongkong': '香港', 'taiwan': '台湾', 'japan': '日本',
            'singapore': '新加坡', 'unitedstates': '美国', 'germany': '德国',
        }
        self.assertEqual({key: value['source_key'] for key, value in REGIONS.items()}, expected)
        chinese = region_labels('zh-CN')
        english = region_labels('en')
        self.assertEqual(set(chinese), set(expected))
        self.assertEqual(set(english), set(expected))
        self.assertEqual(chinese['china'], '中国')
        self.assertEqual(english['china'], 'China')

    def test_messages_format_counts_and_validation_values_in_both_languages(self):
        self.assertEqual(format_message('zh-CN', 'candidate_count', count=3), '3 个候选')
        self.assertEqual(format_message('en', 'candidate_count', count=3), '3 candidates')
        self.assertEqual(format_message('en', 'invalid_rounds', value='0'), 'Rounds must be 1–5 (got 0).')

    def test_application_owned_errors_are_localized_but_unknown_diagnostics_survive(self):
        self.assertEqual(localize_error('en', '响应没有有效 A 记录'), 'The DNS response did not contain a valid A record')
        self.assertEqual(localize_error('en', '已取消'), 'Cancelled')
        self.assertEqual(localize_error('en', 'upstream timeout'), 'upstream timeout')


if __name__ == '__main__':
    unittest.main()
