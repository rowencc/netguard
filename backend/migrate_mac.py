import sys
sys.path.insert(0, '/Users/rowen/IdeaProjects/mimoProject/netguard/backend')

from app.database import SessionLocal
from app.models.device import Device

def normalize_mac(mac: str) -> str:
    parts = mac.replace("-", ":").split(":")
    return ":".join(p.zfill(2).upper() for p in parts)

def migrate():
    db = SessionLocal()
    try:
        devices = db.query(Device).all()
        updated = 0
        for d in devices:
            normalized = normalize_mac(d.mac_address)
            if normalized != d.mac_address:
                conflict = db.query(Device).filter(
                    Device.mac_address == normalized,
                    Device.id != d.id
                ).first()
                if conflict:
                    db.delete(d)
                else:
                    d.mac_address = normalized
                    d.mac_prefix = normalized[:8]
                    updated += 1
        db.commit()
        print(f"Updated {updated} MAC addresses")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
