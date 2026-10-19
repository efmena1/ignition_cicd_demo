"""Read the installed Perspective theme bundle; build a reproducible catalog."""
import hashlib
import io
import json
import posixpath
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
THEMES = ('light', 'dark', 'light-cool', 'dark-cool', 'light-warm', 'dark-warm')
IMPORT = re.compile(r'@import\s+[\"\']([^\"\']+)[\"\']\s*;')
COMMENT = re.compile(r'/\*.*?\*/', re.S)
DECL = re.compile(r'(?:^|;)\s*(--[\w-]+)\s*:\s*([^;]+)', re.M)
RULE = re.compile(r'([^{}]+)\{([^{}]*)\}', re.S)


def category(name):
    groups = [
        ('neutral-', 'Neutrales'), ('red-', 'Rojos'), ('seq-', 'Datos / Secuencial'),
        ('div-', 'Datos / Divergente'), ('qual-', 'Datos / Cualitativa'),
        ('container', 'Contenedores'), ('input', 'Entradas'), ('icon', 'Iconos'),
        ('label', 'Texto'), ('borderRadius', 'Radios'), ('border', 'Bordes'),
        ('boxShadow', 'Sombras'), ('callToAction', 'Acciones'), ('opacity', 'Opacidad'),
        ('font-', 'Tipografia'), ('indicator', 'LED'), ('checkbox', 'Checkbox'),
        ('progress', 'Progreso'), ('toggle', 'Switch'), ('radio', 'Radio'),
        ('pipe', 'Tuberias'), ('context', 'Menu contextual'), ('symbol', 'Simbolos'),
        ('defaultSlider', 'Slider / Foco'),
    ]
    for prefix, label in groups:
        if name[2:].startswith(prefix):
            return label
    return 'Basicos' if name in ('--white', '--black') else 'Estados'


def build():
    jars = list((ROOT / 'jar-cache/com.inductiveautomation.perspective').glob('*perspective-themes-*.jar'))
    if len(jars) != 1:
        raise RuntimeError('Expected one installed theme bundle, found: %s' % jars)
    jarpath = jars[0]
    files = {}
    with zipfile.ZipFile(jarpath) as jar:
        for theme in THEMES:
            with zipfile.ZipFile(io.BytesIO(jar.read(theme + '.zip'))) as bundle:
                for path in bundle.namelist():
                    if path.endswith('.css'):
                        content = bundle.read(path).decode('utf-8')
                        files[theme + '/' + path] = content
                        dest = OUT / 'sources' / theme / path
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_text(content, encoding='utf-8', newline='\n')

    def walk(path, stack=()):
        if path in stack:
            raise ValueError('Import cycle: ' + path)
        source = files[path]
        clean = COMMENT.sub(lambda m: '\n' * m.group().count('\n'), source)
        for imp in IMPORT.finditer(clean):
            target = posixpath.normpath(posixpath.join(posixpath.dirname(path), imp[1]))
            yield from walk(target, stack + (path,))
        # Shipped files contain plain rules, not nested custom-property declarations.
        # Verify coverage independently below so unknown constructs cannot disappear.
        clean = IMPORT.sub('', clean)
        for rule in RULE.finditer(clean):
            selector = rule[1].strip()
            for dec in DECL.finditer(rule[2]):
                name, value = dec[1], dec[2].strip()
                original = re.search(r'(?m)^\s*' + re.escape(name) + r'\s*:', source)
                yield {'id': selector + '|' + name, 'name': name, 'selector': selector,
                       'default': value, 'source': path,
                       'line': source[:original.start()].count('\n') + 1 if original else 0,
                       'category': category(name)}

    catalogs = {}
    loaded = set()
    for theme in THEMES:
        effective = {}
        for row in walk(theme + '/index.css'):
            effective[row['id']] = row
            loaded.add((row['source'], row['name']))
        catalogs[theme] = sorted(effective.values(), key=lambda x: (x['category'], x['name']))

    declared = set()
    uses = {}
    for path, source in files.items():
        clean = COMMENT.sub('', source)
        for match in re.finditer(r'(?:^|[;{])\s*(--[\w-]+)\s*:', clean, re.M):
            declared.add((path, match[1]))
        for name in re.findall(r'var\(\s*(--[\w-]+)', clean):
            uses.setdefault(name, set()).add(path)
    assert declared == loaded, ('Uncataloged declarations', declared - loaded)
    names = sorted({row['name'] for rows in catalogs.values() for row in rows})
    result = {
        'schemaVersion': 1, 'bundle': jarpath.name,
        'bundleSha256': hashlib.sha256(jarpath.read_bytes()).hexdigest(),
        'perspectiveVersion': '3.3.9.2026082511',
        'themes': catalogs, 'uniqueVariableCount': len(names),
        'cssFileCount': len(files), 'declarationCount': len(declared),
        'referencesWithoutThemeDeclaration': sorted(set(uses) - set(names)),
        'uses': {k: sorted(v) for k, v in sorted(uses.items())},
    }
    (OUT / 'catalog.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    for theme, rows in catalogs.items():
        groups = {}
        for row in rows:
            groups.setdefault(row['selector'], []).append(row)
        css = ['/* Editable complete baseline: %s. Perspective %s. */' % (theme, result['perspectiveVersion'])]
        for selector, entries in groups.items():
            css.append(selector + ' {')
            css.extend('    %s: %s;' % (r['name'], r['default']) for r in entries)
            css.append('}\n')
        dest = OUT / 'baselines' / (theme + '.css')
        dest.parent.mkdir(exist_ok=True)
        dest.write_text('\n'.join(css), encoding='utf-8')

    md = ['# Variables de los temas Perspective instalados', '',
          'Fuente: `%s`, SHA-256 `%s`.' % (jarpath.name, result['bundleSha256']), '',
          '%s archivos CSS; %s declaraciones; %s nombres distintos. Cada tema carga %s variables: 118 globales y 2 del slider.' %
          (len(files), len(declared), len(names), len(catalogs['light'])), '',
          'Se conserva la herencia por imports, el selector y los valores var(...). No se convierten las referencias en colores fijos.', '',
          '`--red-90` solo existe en la familia light; `--red-10` solo en dark. Las variantes cool/warm redefinen diez neutrales.', '',
          '| Variable | Categoria | Light | Dark | Selector |', '|---|---|---|---|---|']
    by_theme = {t: {r['name']: r for r in rows} for t, rows in catalogs.items()}
    for name in names:
        row = by_theme['light'].get(name) or by_theme['dark'][name]
        values = [by_theme[t].get(name, {}).get('default', 'No definida') for t in ('light', 'dark')]
        md.append('| `%s` | %s | `%s` | `%s` | `%s` |' % (name, row['category'], values[0], values[1], row['selector']))
    md.extend(['', '## Neutrales de las variantes', '', '| Variable | Light cool | Dark cool | Light warm | Dark warm |', '|---|---|---|---|---|'])
    for i in range(10, 101, 10):
        name = '--neutral-' + str(i)
        md.append('| `%s` | %s |' % (name, ' | '.join('`%s`' % by_theme[t][name]['default'] for t in THEMES[2:])))
    md.extend(['', '## Referencias sin declaracion en los temas', '',
               'Estas referencias aparecen en CSS pero no tienen un valor por defecto declarado en el bundle; no se inventa una base editable para ellas.', '',
               ', '.join('`%s`' % name for name in result['referencesWithoutThemeDeclaration']) or 'Ninguna.', '',
               '## Fuentes oficiales', '',
               '- https://docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/perspective-built-in-themes',
               '- https://docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/creating-and-using-custom-perspective-themes', ''])
    (OUT / 'VARIABLES.md').write_text('\n'.join(md), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('uniqueVariableCount', 'cssFileCount', 'declarationCount', 'referencesWithoutThemeDeclaration')}, indent=2))
    return result


if __name__ == '__main__':
    build()
