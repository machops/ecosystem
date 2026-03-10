import unittest

class TestMachineFirstCompliance(unittest.TestCase):
    def test_urn_consistency(self):
        with open('URN', 'r') as f:
            urn = f.read().strip()
        self.assertTrue(urn.startswith('urn:codevantaos:'))

    def test_metadata_integrity(self):
        import yaml
        with open('METADATA.yaml', 'r') as f:
            meta = yaml.safe_load(f)
        self.assertIn('id', meta)
        self.assertIn('urn', meta)

if __name__ == '__main__':
    unittest.main()