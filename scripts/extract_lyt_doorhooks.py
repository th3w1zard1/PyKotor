"""Extract doorhook lines from actual game LYT files."""
from pykotor.extract.installation import Installation
from pykotor.resource.type import ResourceType

inst = Installation('C:/Program Files (x86)/Steam/steamapps/common/swkotor')
modules = ['m01aa', 'm03aa', 'm04aa', 'm12aa']

print("=" * 80)
print("ACTUAL GAME LYT FILES - DOORHOOK FORMAT")
print("=" * 80)

for m in modules:
    try:
        lyt_res = inst.resource(m, ResourceType.LYT)
        raw = lyt_res.data.decode('utf-8', errors='ignore')
        
        if 'doorhookcount' in raw:
            section = raw.split('doorhookcount')[1].split('donelayout')[0]
            lines = [l.strip() for l in section.split('\n') 
                    if l.strip() and not l.strip().isdigit() 
                    and 'doorhookcount' not in l.lower()]
            
            print(f"\n=== {m.upper()} ===")
            print(f"Source: chitin.key (BIF archive)")
            for i, line in enumerate(lines[:3], 1):
                tokens = line.split()
                print(f"\nDoorhook {i}:")
                print(f"  Raw line: {repr(line)}")
                print(f"  Token count: {len(tokens)}")
                print(f"  Tokens: {tokens}")
                if len(tokens) >= 10:
                    print(f"  Our interpretation:")
                    print(f"    room = tokens[0] = {tokens[0]}")
                    print(f"    door = tokens[1] = {tokens[1]}")
                    print(f"    token[2] = {tokens[2]} (the '0')")
                    print(f"    position = tokens[3-5] = ({tokens[3]}, {tokens[4]}, {tokens[5]})")
                    print(f"    quaternion = tokens[6-9] = ({tokens[6]}, {tokens[7]}, {tokens[8]}, {tokens[9]})")
                    print(f"  xoreos interpretation:")
                    print(f"    room = strings[0] = {tokens[0]}")
                    print(f"    name = strings[1] = {tokens[1]}")
                    print(f"    x = strings[2] = {tokens[2]} (would be '{tokens[2]}' - the '0'!)")
                    print(f"    y = strings[3] = {tokens[3]} (would be '{tokens[3]}' - actual x!)")
                    print(f"    z = strings[4] = {tokens[4]} (would be '{tokens[4]}' - actual y!)")
    except Exception as e:
        print(f"\n=== {m.upper()} ===")
        print(f"Error: {e}")

