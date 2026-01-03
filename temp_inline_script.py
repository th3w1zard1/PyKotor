import pathlib

files = ['capsule.mod', 'capsule.rim']
base_path = pathlib.Path('Libraries/PyKotor/tests/test_files')

for filename in files:
    path = base_path / filename
    data = path.read_bytes()
    var_name = filename.replace('.', '_').upper() + '_DATA'
    print(f'{var_name} = {repr(data)}')
    print()
