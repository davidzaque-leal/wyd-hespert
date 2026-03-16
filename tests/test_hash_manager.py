import unittest
import os
import shutil
from app.services.hash_manager import HashManager

class TestHashManager(unittest.TestCase):
    def setUp(self):
        # Limpa a pasta de hashes antes de cada teste
        self.hash_dir = HashManager.HASH_DIR
        if os.path.exists(self.hash_dir):
            shutil.rmtree(self.hash_dir)
        os.makedirs(self.hash_dir, exist_ok=True)

    def test_calc_hash_consistency(self):
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}  # Ordem diferente
        hash1 = HashManager._calc_hash(data1)
        hash2 = HashManager._calc_hash(data2)
        self.assertEqual(hash1, hash2)

    def test_check_and_update_hash(self):
        data = {"x": 10}
        # Primeira vez, deve retornar True (hash novo)
        changed = HashManager.check_and_update_hash("test", data)
        self.assertTrue(changed)
        # Segunda vez, sem alteração, deve retornar False
        changed = HashManager.check_and_update_hash("test", data)
        self.assertFalse(changed)
        # Alterando os dados, deve retornar True
        changed = HashManager.check_and_update_hash("test", {"x": 11})
        self.assertTrue(changed)

    def test_load_and_save_hash(self):
        hash_val = "abc123"
        HashManager._save_hash("loadsave", hash_val)
        loaded = HashManager._load_hash("loadsave")
        self.assertEqual(hash_val, loaded)

    def tearDown(self):
        # Limpa a pasta de hashes após cada teste
        if os.path.exists(self.hash_dir):
            shutil.rmtree(self.hash_dir)

if __name__ == '__main__':
    unittest.main()
