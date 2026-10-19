"""Package only the new view and its library for Designer File > Import."""
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE / 'project'
manifest = {'title': 'ATS Theme Library',
            'description': 'Editable built-in Perspective variables, extracted from Perspective 3.3.9.',
            'enabled': True, 'inheritable': False, 'parent': ''}
(PROJECT / 'project.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
target = HERE / 'ATS-Theme-Library-Perspective-8.3.zip'
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(PROJECT.rglob('*')):
        if path.is_file() and path.name in ('project.json', 'resource.json', 'view.json', 'code.py'):
            archive.write(path, path.relative_to(PROJECT).as_posix())
print(target)
