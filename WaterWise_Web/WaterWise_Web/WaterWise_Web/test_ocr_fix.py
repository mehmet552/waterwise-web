
import re

text = """
ODENECER TU
715,00 TL 18:1272025
"""

def test(pattern):
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        print(f"MATCH: {match.group(1)}")
    else:
        print("NO MATCH")

print("--- Try 1: Lenient 'Tutar' ---")
# Allow 'Tu' start, ignore rest of word
test(r'(?:[OÖoö]denece[kr]|[Tt]oplam|[Gg]enel).*?Tu.*?(\d+[.,]\d+)')

print("\n--- Try 2: Very Lenient (Just Keywords) ---")
# Just look for Odenecek/Toplam near a number
test(r'(?:[OÖoö]denece[kr]|[Tt]oplam|[Gg]enel).*?(\d+[.,]\d+)')

print("\n--- Try 3: Specific OCR Error 'ODENECER' ---")
test(r'(?:[OÖoö]denece[kr]|[Tt]oplam|[Gg]enel|ODENECER).*?(\d+[.,]\d+)')
