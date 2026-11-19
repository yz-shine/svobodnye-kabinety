# -*- coding: utf-8 -*-
"""Читает сохранённые HTML-страницы кабинетов из папки source/ и создаёт data.js для сайта.
Запуск: python build_data.py   (нужен пакет beautifulsoup4: pip install beautifulsoup4)"""
import glob, json, re, os
from bs4 import BeautifulSoup

DAYS = {'Duşanba': 0, 'Seşanba': 1, 'Çorşanba': 2, 'Payşanba': 3, 'Juma': 4}
PAIRS = ['08:00', '09:30', '11:00', '13:00', '14:30', '16:00']

def clean(t):
    return re.sub(r'\s+', ' ', t).strip()

def fix_latin(t):
    # в сохранённых страницах мягкие знаки заменены особыми буквами
    for a, b in {'ş': 'sh', 'Ş': 'Sh', 'ç': 'ch', 'Ç': 'Ch', 'ñ': 'ng', 'ğ': 'g‘', 'ö': 'o‘', 'Ö': 'O‘'}.items():
        t = t.replace(a, b)
    return t

rooms = []
for f in sorted(glob.glob('source/*.html'), key=lambda x: int(re.search(r'(\d+)-xona', x).group(1))):
    soup = BeautifulSoup(open(f, encoding='utf-8').read(), 'html.parser')
    number = re.search(r'(\d+)-xona', soup.find('h1').get_text()).group(1)
    small = soup.select_one('.hero small')
    tags = [t.get_text(strip=True) for t in soup.select('.tag')]
    seats = re.search(r'\d+', tags[1]).group(0) if len(tags) > 1 else ''
    room = {'room': number, 'building': clean(small.get_text()) if small else '',
            'type': tags[0] if tags else '', 'seats': int(seats) if seats else None,
            'lessons': []}
    for d in soup.select('details.day'):
        name = clean(d.summary.contents[0]) if d.summary.contents else ''
        day = DAYS[name]
        for s in d.select('.slot'):
            pair = PAIRS.index(s.select_one('.time').get_text(strip=True)) + 1
            for c in s.select('.class'):
                wk = c.select_one('.week')
                week = 'all' if not wk else ('even' if 'Juft' in wk.get_text() else 'odd')
                smalls = [clean(x.get_text()) for x in c.select('small')]
                kind, teacher = (smalls[0].split(' · ', 1) + [''])[:2] if smalls else ('', '')
                group = smalls[1].replace('Oqim:', '').strip() if len(smalls) > 1 else ''
                room['lessons'].append({'day': day, 'pair': pair, 'week': week,
                    'subject': c.select_one('b').get_text(strip=True),
                    'kind': kind.strip(), 'teacher': teacher.strip(), 'group': group})
    rooms.append(room)

with open('data.js', 'w', encoding='utf-8') as out:
    out.write('// Создано файлом build_data.py из сохранённых страниц кабинетов\n')
    out.write('window.SCHEDULE = ' + json.dumps({'rooms': rooms}, ensure_ascii=False, indent=1) + ';\n')
print(len(rooms), 'кабинетов,', sum(len(r['lessons']) for r in rooms), 'занятий')
