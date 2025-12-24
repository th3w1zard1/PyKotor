"""Extract doorhook lines from actual game LYT files."""

from __future__ import annotations

from pykotor.extract.file import ResourceResult
from pykotor.extract.installation import Installation
from pykotor.resource.type import ResourceType

inst: Installation = Installation("C:/Program Files (x86)/Steam/steamapps/common/swkotor")
modules: list[str] = ["m01aa", "m03aa", "m04aa", "m12aa"]

print("=" * 80)
print("ACTUAL GAME LYT FILES - DOORHOOK FORMAT")
print("=" * 80)


def main():
    for m in modules:
        try:
            lyt_res: ResourceResult = inst.resource(m, ResourceType.LYT)
            raw: str = lyt_res.data.decode("utf-8", errors="ignore")
            lower_raw: str = raw.lower()

            if "doorhookcount" in lower_raw:
                section: str = lower_raw.split("doorhookcount")[1].split("donelayout")[0]
                lines: list[str] = [
                    raw_lwr.strip()
                    for raw_lwr in section.split("\n")
                    if raw_lwr.strip() and not raw_lwr.strip().isdigit() and "doorhookcount" not in raw_lwr.lower()
                ]

                print(f"\n=== {m.upper()} ===")
                print("Source: chitin.key (BIF archive)")
                for i, line in enumerate(lines[:3], 1):
                    tokens: list[str] = line.split()
                    print(f"\nDoorhook {i}:")
                    print(f"  Raw line: {repr(line)}")
                    print(f"  Token count: {len(tokens)}")
                    print(f"  Tokens: {tokens}")
                    if len(tokens) >= 10:
                        print("  Our interpretation:")
                        print(f"    room = tokens[0] = {tokens[0]}")
                        print(f"    door = tokens[1] = {tokens[1]}")
                        print(f"    token[2] = {tokens[2]} (the '0')")
                        print(f"    position = tokens[3-5] = ({tokens[3]}, {tokens[4]}, {tokens[5]})")
                        print(f"    quaternion = tokens[6-9] = ({tokens[6]}, {tokens[7]}, {tokens[8]}, {tokens[9]})")
                        print("  xoreos interpretation:")
                        print(f"    room = strings[0] = {tokens[0]}")
                        print(f"    name = strings[1] = {tokens[1]}")
                        print(f"    x = strings[2] = {tokens[2]} (would be '{tokens[2]}' - the '0'!)")
                        print(f"    y = strings[3] = {tokens[3]} (would be '{tokens[3]}' - actual x!)")
                        print(f"    z = strings[4] = {tokens[4]} (would be '{tokens[4]}' - actual y!)")
        except Exception as e:
            print(f"\n=== {m.upper()} ===")
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
