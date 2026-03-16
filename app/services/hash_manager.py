import hashlib
import json
import os

class HashManager:
    HASH_DIR = os.path.join(os.path.dirname(__file__), 'hashes')
    os.makedirs(HASH_DIR, exist_ok=True)

    @classmethod
    def _get_hash_filename(cls, name):
        return os.path.join(cls.HASH_DIR, f'{name}_hash.txt')

    @staticmethod
    def _calc_hash(data):
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    @classmethod
    def _load_hash(cls, name):
        try:
            with open(cls._get_hash_filename(name), 'r') as f:
                return f.read().strip()
        except Exception:
            return None

    @classmethod
    def _save_hash(cls, name, hash_value):
        with open(cls._get_hash_filename(name), 'w') as f:
            f.write(hash_value)

    @classmethod
    def check_and_update_hash(cls, name, data):
        new_hash = cls._calc_hash(data)
        old_hash = cls._load_hash(name)
        if new_hash != old_hash:
            cls._save_hash(name, new_hash)
            return True
        return False
