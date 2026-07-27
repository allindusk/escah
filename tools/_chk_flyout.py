import re
h = open('site/.vitepress/dist/ja/annihilation.html', encoding='utf-8').read()
m = re.search(r'<div class="VPFlyout VPNavBarTranslations translations".*?(?=<div class="VPNavBarSocial|</header>|VPSocial)', h, re.S)
if not m:
    m = re.search(r'<div class="VPFlyout VPNavBarTranslations translations".*?</div>\s*</div>\s*</div>', h, re.S)
block = m.group(0) if m else 'NOT FOUND'
print(block[:2500])
