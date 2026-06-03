import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.auth_helper import STORAGE_STATE_PATH

p = STORAGE_STATE_PATH
if not p.exists():
    print("storage_state.json: MISSING")
    raise SystemExit(1)

data = json.loads(p.read_text(encoding="utf-8"))
print(f"origins: {len(data.get('origins', []))}")
print(f"cookies: {len(data.get('cookies', []))}")
now = datetime.now(timezone.utc)
for c in data.get("cookies", []):
    exp = c.get("expires", -1)
    name = c.get("name", "?")
    domain = c.get("domain", "?")
    if exp and exp > 0:
        exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
        status = "EXPIRED" if exp_dt < now else "valid"
        print(f"  {name[:40]:40} {domain:25} expires={exp_dt.isoformat()} [{status}]")
    else:
        print(f"  {name[:40]:40} {domain:25} session cookie")

mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
print(f"file last saved: {mtime.isoformat()}")

for origin in data.get("origins", []):
    o = origin.get("origin", "")
    keys = [item.get("name") for item in origin.get("localStorage", [])]
    if keys:
        print(f"localStorage {o}: {keys[:10]}")
