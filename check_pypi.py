import requests

r = requests.get('https://pypi.org/pypi/holocrontoolset/json', timeout=10)
data = r.json()
versions = list(data.get('releases', {}).keys())
beta_versions = [v for v in versions if 'b' in v]

print('Beta versions on PyPI:')
for v in sorted(beta_versions):
    print(f'  {v}')

print(f'\n4.0.0b11 available: {"4.0.0b11" in versions}')
