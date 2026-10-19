# -*- coding: utf-8 -*-
"""Jython 2.7 / Python 3 compatible services for the Perspective Theme Library.

The build appends CATALOG from the installed, unmodified theme bundle.
"""
import io
import json
import os
import re
import shutil
import tempfile
import zipfile
from collections import OrderedDict

try:
    text_type = unicode
except NameError:
    text_type = str

BUILTINS = ('light', 'dark', 'light-cool', 'dark-cool', 'light-warm', 'dark-warm')
MANIFEST = 'ats-editor.json'
REF = re.compile(r'var\(')


def plain(value):
    """Detach Perspective property wrappers before editing them."""
    return json.loads(system.util.jsonEncode(value))


def data_dir():
    from java.lang import System
    path = text_type(System.getProperty('data.dir', 'data'))
    if not os.path.isabs(path):
        path = os.path.join(text_type(System.getProperty('user.dir')), path)
    path = os.path.realpath(path)
    if not os.path.isdir(os.path.join(path, 'config', 'resources', 'core')):
        raise ValueError('No se encontro la carpeta de recursos de Ignition 8.3.')
    return path


def themes_dir():
    path = os.path.join(data_dir(), 'config', 'resources', 'core',
                        'com.inductiveautomation.perspective', 'themes')
    if not os.path.isdir(path):
        raise ValueError('No se encontro la carpeta de temas de Perspective 8.3.')
    return path


def validate_name(name):
    name = text_type(name).strip()
    if not re.match(r'^[a-z][a-z0-9-]{2,63}$', name):
        raise ValueError('Nombre: 3 a 64 caracteres, minusculas, numeros y guiones; empieza con una letra.')
    if name in BUILTINS or name in ('con', 'prn', 'aux', 'nul') or re.match(r'^(com|lpt)[0-9]$', name):
        raise ValueError('Ese nombre esta reservado. Elige un nombre propio, por ejemplo ats-light.')
    return name


def validate_value(value):
    value = text_type(value).strip()
    if not value or len(value) > 2000:
        raise ValueError('El valor no puede estar vacio ni superar 2000 caracteres.')
    if any(c in value for c in (';', '{', '}', '\n', '\r', '<', '>', '\\', '/*', '*/', '@', '!')):
        raise ValueError('Introduce solo un valor CSS, sin reglas, comentarios ni !important.')
    if re.search(r'(?i)(url|expression)\s*\(', value):
        raise ValueError('Las variables de esta biblioteca no aceptan URL ni expression().')
    quote = None
    depth = 0
    for char in value:
        if quote:
            if char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            if depth < 0:
                raise ValueError('Parentesis CSS sin pareja.')
    if quote or depth:
        raise ValueError('Comillas o parentesis CSS sin cerrar.')
    return value


def rows_for(base, overrides=None):
    if base not in BUILTINS:
        raise ValueError('Tema base desconocido.')
    overrides = overrides or {}
    rows = json.loads(json.dumps(CATALOG['themes'][base]))
    known = set(row['id'] for row in rows)
    if set(overrides) - known:
        raise ValueError('El archivo contiene variables ajenas a esta version del catalogo.')
    for row in rows:
        row['value'] = validate_value(overrides.get(row['id'], row['default']))
    return decorate(rows)


def decorate(rows):
    roots = dict((r['name'], r['value']) for r in rows if r['selector'] == ':root')
    scoped = dict(((r['selector'], r['name']), r['value']) for r in rows)

    def resolve(value, selector, trail=()):
        def replace(name, fallback):
            if name in trail:
                raise ValueError('Referencia circular: ' + ' -> '.join(trail + (name,)))
            # Resolve a :root alias in :root scope, not in the descendant's scope.
            scope = selector if (selector, name) in scoped else ':root'
            target = scoped.get((scope, name), roots.get(name))
            if target is None:
                if fallback is not None:
                    return resolve(fallback, selector, trail)
                raise ValueError('Variable no definida: ' + name)
            return resolve(target, scope, trail + (name,))
        result = []
        offset = 0
        while True:
            match = REF.search(value, offset)
            if match is None:
                result.append(value[offset:])
                break
            result.append(value[offset:match.start()])
            start = match.end()
            end = start
            depth = 1
            while end < len(value) and depth:
                if value[end] == '(':
                    depth += 1
                elif value[end] == ')':
                    depth -= 1
                end += 1
            if depth:
                raise ValueError('Referencia var() sin cerrar.')
            args = value[start:end - 1].split(',', 1)
            name = args[0].strip()
            if not re.match(r'^--[\w-]+$', name):
                raise ValueError('Nombre de variable CSS no valido: ' + name)
            fallback = args[1].strip() if len(args) > 1 else None
            result.append(replace(name, fallback))
            offset = end
        return ''.join(result)

    for row in rows:
        row['changed'] = row['value'] != row['default']
        row['resolved'] = resolve(row['value'], row['selector'], (row['name'],))
        color = row['resolved']
        is_color = bool(re.match(r'^(#[0-9a-fA-F]{3,8}|rgba?\(.+\)|hsla?\(.+\)|transparent)$', color))
        row['sample'] = {'value': '', 'style': {'backgroundColor': color if is_color else 'transparent'}}
    return rows


def overrides_for(base, rows):
    originals = dict((r['id'], r) for r in CATALOG['themes'][base])
    result = {}
    seen = set()
    for row in rows:
        key = row['id']
        if key not in originals or key in seen:
            raise ValueError('Variable duplicada o desconocida.')
        seen.add(key)
        value = validate_value(row['value'])
        if value != originals[key]['default']:
            result[key] = value
    if seen != set(originals):
        raise ValueError('El catalogo esta incompleto; vuelve a cargar la base.')
    rows_for(base, result)  # Check variable references and cycles before persistence.
    return result


def css_for(base, rows):
    changes = overrides_for(base, rows)
    groups = OrderedDict()
    for row in CATALOG['themes'][base]:
        if row['id'] in changes:
            groups.setdefault(row['selector'], []).append((row['name'], changes[row['id']]))
    lines = ['/* ATS Theme Library. Base: %s. Only explicit overrides. */' % base]
    for selector, declarations in groups.items():
        lines.append(selector + ' {')
        lines.extend('    %s: %s;' % pair for pair in declarations)
        lines.append('}')
    if not groups:
        lines.append('/* Sin cambios: se hereda el tema base completo. */')
    return '\n'.join(lines) + '\n'


def manifest_for(name, base, rows):
    return {'schemaVersion': 1, 'generator': 'ats-theme-library',
            'name': validate_name(name), 'baseTheme': base,
            'catalogSha256': CATALOG['bundleSha256'],
            'perspectiveVersion': CATALOG['perspectiveVersion'],
            'overrides': overrides_for(base, rows)}


def files_for(name, base, rows):
    manifest = manifest_for(name, base, rows)
    files = {
        'index.css': '@import "../%s/index.css";\n@import "./overrides.css";\n' % base,
        'overrides.css': css_for(base, rows),
        'config.json': json.dumps({'entrypoint': 'index.css', 'isPrivate': False}, indent=2),
        MANIFEST: json.dumps(manifest, ensure_ascii=False, indent=2),
    }
    files['resource.json'] = json.dumps({
        'scope': 'G', 'version': 1, 'restricted': False, 'overridable': True,
        'files': sorted(files), 'attributes': {},
        'description': 'ATS custom theme derived from ' + base,
    }, indent=2)
    return files


def save_new(name, base, rows):
    """Stage completely before publishing. Existing directories are never replaced."""
    name = validate_name(name)
    payload = files_for(name, base, rows)
    destination = os.path.join(themes_dir(), name)
    if os.path.lexists(destination):
        raise ValueError('Ya existe %s. Usa otro nombre para guardar una nueva version.' % name)
    staging_root = os.path.join(data_dir(), 'var')
    if not os.path.isdir(staging_root):
        os.makedirs(staging_root)
    staging = tempfile.mkdtemp(prefix='ats-theme-', dir=staging_root)
    try:
        for filename, content in payload.items():
            with io.open(os.path.join(staging, filename), 'w', encoding='utf-8') as handle:
                handle.write(text_type(content))
        # rename is same-volume and publishes a complete resource; no overwrite on Windows.
        if os.path.lexists(destination):
            raise ValueError('El nombre fue creado por otra sesion. Usa otro nombre.')
        os.rename(staging, destination)
    finally:
        if os.path.isdir(staging):
            shutil.rmtree(staging)
    return destination


def decode_manifest(content):
    data = json.loads(content)
    if data.get('generator') != 'ats-theme-library' or data.get('schemaVersion') != 1:
        raise ValueError('Selecciona un JSON exportado por ATS Theme Library.')
    if data.get('catalogSha256') != CATALOG['bundleSha256']:
        raise ValueError('El JSON usa otra version de Perspective. Revisa o migra el catalogo antes de importarlo.')
    base = data['baseTheme']
    rows = rows_for(base, data.get('overrides', {}))
    return base, rows, validate_name(data['name'])


def load_theme(name):
    if name in BUILTINS:
        return name, rows_for(name), 'ats-' + name
    name = validate_name(name)
    path = os.path.join(themes_dir(), name, MANIFEST)
    with io.open(path, 'r', encoding='utf-8') as handle:
        return decode_manifest(handle.read())


def theme_options():
    options = [{'label': 'Base / ' + t, 'value': t} for t in BUILTINS]
    for name in sorted(os.listdir(themes_dir())):
        if name not in BUILTINS and os.path.isfile(os.path.join(themes_dir(), name, MANIFEST)):
            options.append({'label': 'Guardado / ' + name, 'value': name})
    return options


def request_theme_scan():
    """Configuration resources have a separate scanner from project resources."""
    try:
        from com.inductiveautomation.ignition.gateway import IgnitionGateway
        IgnitionGateway.get().getConfigurationManager().requestScan()
        return 'Se solicito la recarga de recursos. Cuando aparezca, selecciona el tema en session.props.theme.'
    except Exception:
        return 'Ejecuta Scan filesystem de configuracion en el Gateway (no el de proyectos); despues selecciona el tema en session.props.theme.'


def export_zip(name, base, rows):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for filename, content in files_for(name, base, rows).items():
            archive.writestr(name + '/' + filename, content.encode('utf-8'))
    return output.getvalue()


def refresh(view, rows):
    rows = decorate(rows)
    view.custom.rows = rows
    view.custom.cssPreview = css_for(text_type(view.custom.baseTheme), rows)
    changes = sum(1 for r in rows if r['changed'])
    view.custom.summary = '%s variables | %s cambios | base %s | Perspective %s' % (
        len(rows), changes, view.custom.baseTheme, CATALOG['perspectiveVersion'])
    roots = dict((r['name'], r['resolved']) for r in rows if r['selector'] == ':root')
    view.custom.preview = {
        'background': roots['--containerRoot'], 'surface': roots['--container'],
        'text': roots['--label'], 'border': roots['--border'], 'action': roots['--callToAction'],
        'input': roots['--input'], 'success': roots['--success'], 'error': roots['--error'],
        'radius': roots['--borderRadius'],
    }


def load_into(view, name):
    base, rows, target = load_theme(text_type(name))
    view.custom.baseTheme = base
    view.custom.targetName = target if name in BUILTINS else target + '-copy'
    refresh(view, rows)
    view.custom.status = 'Base cargada. Edita la columna Valor y pulsa Enter para confirmar cada celda.'


def edit(view, index, value):
    rows = plain(view.custom.rows)
    if not 0 <= index < len(rows):
        raise ValueError('Fila no valida.')
    rows[index]['value'] = validate_value(value) if text_type(value).strip() else rows[index]['default']
    # Validate and calculate before assigning any property: a bad edit leaves the draft intact.
    checked = rows_for(text_type(view.custom.baseTheme), overrides_for(text_type(view.custom.baseTheme), rows))
    refresh(view, checked)
    view.custom.status = 'Cambio en borrador. Aun no se ha guardado en el Gateway.'
