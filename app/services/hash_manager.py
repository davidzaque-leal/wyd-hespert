import hashlib
import json
from app.database import SessionLocal
from app.models import SyncHash

class HashManager:
    @staticmethod
    def _calc_hash(data):
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    @classmethod
    def check_and_update_hash(cls, name, data):
        session = SessionLocal()
        try:
            new_hash = cls._calc_hash(data)
            hash_row = session.query(SyncHash).filter_by(name=name).first()
            old_hash = hash_row.hash_value if hash_row else None
            if new_hash != old_hash:
                if hash_row:
                    hash_row.hash_value = new_hash
                else:
                    hash_row = SyncHash(name=name, hash_value=new_hash)
                    session.add(hash_row)
                session.commit()
                return True
            return False
        finally:
            session.close()
