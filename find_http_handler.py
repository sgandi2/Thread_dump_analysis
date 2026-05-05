import json
from pathlib import Path

dump_dir = Path("data/thread_dumps")
latest = sorted(dump_dir.glob("jstack_dump_*.json"), reverse=True)[0]

with open(latest) as f:
    data = json.load(f)

print(f"Checking: {latest.name}")
print(f"Total threads: {data['thread_count']}\n")

# Find HTTP Handler thread
found = False
for thread in data['threads']:
    if 'HTTP' in thread['name'] or 'Handler' in thread['name']:
        print(f"Found: {thread['name']}")
        print(f"  State: {thread['state']}")
        print(f"  CPU Time: {thread['cpu_time']}s")
        print(f"  Stack trace:")
        for line in thread.get('stack_trace', [])[:5]:
            print(f"    {line}")
        print()
        found = True

if not found:
    print("❌ No HTTP Handler thread found")
    print("\nRUNNABLE threads:")
    for thread in data['threads']:
        if thread['state'] == 'RUNNABLE':
            print(f"  - {thread['name']}")

# Made with Bob
