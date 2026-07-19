import urllib.request
import re

req = urllib.request.Request('https://docs.pierre.finance/api-reference/introduction', headers={'User-Agent': 'Mozilla/5.0'})
response = urllib.request.urlopen(req)
html = response.read().decode('utf-8')

links = re.findall(r'href="(/api-reference/[^"]+)"', html)
unique_links = []
for l in links:
    if l not in unique_links:
        unique_links.append(l)

print('Links found:', len(unique_links))
for l in unique_links:
    print(l)
