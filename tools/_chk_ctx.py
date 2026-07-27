h = open('site/.vitepress/dist/ja/annihilation.html', encoding='utf-8').read()
for needle in ['<p class="title">日本語</p>', '<p class="trans-title">日本語</p>']:
    i = h.find(needle)
    print('====', needle, 'index', i)
    if i >= 0:
        print(h[max(0,i-400):i+len(needle)+200])
        print()
