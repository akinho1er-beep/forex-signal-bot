"""Fix BOM dans scan_once.py"""
with open("scan_once.py", "r", encoding="utf-8-sig") as f:
    content = f.read()
with open("scan_once.py", "w", encoding="utf-8") as f:
    f.write(content)
print("BOM supprime de scan_once.py !")

# Verifier
with open("scan_once.py", "rb") as f:
    raw = f.read(3)
if raw[:3] == b'\xef\xbb\xbf':
    print("ERREUR: BOM encore present!")
else:
    print("OK: Pas de BOM")