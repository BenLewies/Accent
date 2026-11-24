import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bundle_notices', ROOT / 'scripts/bundle_notices.py')
notices = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notices)

# A small fixture with the same complete source-header form used by exif-rs.
HEADER = '''// Copyright (c) 2016 Example Author.
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
// 1. Redistributions of source code must retain the above copyright notice.
// 2. Binary redistributions must reproduce this notice and disclaimer.
// THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS AS IS.
// THE AUTHOR IS NOT LIABLE FOR SUCH DAMAGE.
'''


class SourceNoticeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'src').mkdir()
        (self.root / 'Cargo.toml').write_text('[package]\nname="example"\n')
        self.package = {'manifest_path': str(self.root / 'Cargo.toml'), 'name': 'example',
                        'version': '1.0', 'license': 'BSD-2-Clause'}

    def test_source_header_retains_attribution_and_complete_disclaimer(self):
        (self.root / 'src/lib.rs').write_text(HEADER + '\n//! API documentation\npub fn example() {}\n')
        result = notices.package_notices(self.package)
        self.assertIn(HEADER.strip(), result)
        self.assertIn('src/lib.rs (original licence header)', result)
        self.assertNotIn('API documentation', result)

    def test_duplicate_headers_are_deduplicated_but_different_years_retained(self):
        (self.root / 'src/lib.rs').write_text(HEADER + 'pub fn example() {}\n')
        (self.root / 'src/one.rs').write_text(HEADER + 'pub fn one() {}\n')
        (self.root / 'src/two.rs').write_text(HEADER.replace('2016', '2017') + 'pub fn two() {}\n')
        result = notices.source_license_headers(self.root)
        self.assertEqual(len(result), 2)
        self.assertTrue(any('2016' in text for _, text in result))
        self.assertTrue(any('2017' in text for _, text in result))

    def test_copyright_without_terms_is_not_accepted_as_a_complete_notice(self):
        (self.root / 'src/lib.rs').write_text('// Copyright Example Author\npub fn example() {}\n')
        self.assertEqual(notices.source_license_headers(self.root), [])
        with self.assertRaises(RuntimeError):
            notices.package_notices(self.package)


if __name__ == '__main__':
    unittest.main()
