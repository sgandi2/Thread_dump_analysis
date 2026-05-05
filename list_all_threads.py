import json
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

dump_dir = Path("data/thread_dumps")
latest = sorted(dump_dir.glob("jstack_dump_*.json"), reverse=True)[0]

with open(latest) as f:
    data = json.load(f)

print(f"Dump: {latest.name}")
print(f"Total: {data['thread_count']} threads\n")
print("=" * 80)

for i, thread in enumerate(data['threads'], 1):
    state_icon = {
        'RUNNABLE': '🟢',
        'WAITING': '🟡', 
        'BLOCKED': '🔴',
        'IN': '⚪'
    }.get(thread['state'], '⚫')
    
    print(f"{i:2d}. {state_icon} {thread['name'][:60]:<60} {thread['state']}")

print("=" * 80)
print(f"\nLooking for infinite loop service...")
print("If your service is running, it should appear in the list above.")
print("\nRUNNABLE threads are most likely to be infinite loops.")

# Made with Bob
