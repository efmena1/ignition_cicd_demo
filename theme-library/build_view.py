"""Build the editable Perspective view and its project script from local sources."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROJECT = HERE / 'project'
CATALOG = json.loads((HERE / 'catalog.json').read_text(encoding='utf-8'))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')


def resource(files):
    return {'scope': 'G', 'version': 1, 'restricted': False, 'overridable': True,
            'files': files, 'attributes': {}}


def binding(path, bidirectional=False):
    config = {'path': path}
    if bidirectional:
        config['bidirectional'] = True
    return {'binding': {'type': 'property', 'config': config}}


def event(script):
    return {'type': 'script', 'scope': 'G', 'config': {'script': script}}


def guarded(body):
    return 'try:\n' + '\n'.join('    ' + line for line in body.splitlines()) + '\nexcept Exception as e:\n    self.view.custom.status = "Error: " + str(e)\n'


def component(name, kind, props=None, position=None, bindings=None, events=None):
    c = {'type': kind, 'meta': {'name': name}, 'props': props or {},
         'position': position or {'basis': 'auto', 'shrink': 0}}
    if bindings:
        c['propConfig'] = bindings
    if events:
        c['events'] = events
    return c


def label(name, text='', style=None, path=None):
    return component(name, 'ia.display.label', {'text': text, 'style': style or {}},
                     bindings={'props.text': binding(path)} if path else None)


def flex(name, children, direction='row', style=None, position=None, wrap='nowrap'):
    c = component(name, 'ia.container.flex', {'direction': direction, 'wrap': wrap,
                  'style': dict({'gap': '12px'}, **(style or {}))}, position)
    c['children'] = children
    return c


def button(name, text, script, primary=False):
    style = {'padding': '8px 14px', 'borderRadius': '6px'}
    if primary:
        style.update({'backgroundColor': 'var(--callToAction)', 'color': 'var(--white)'})
    return component(name, 'ia.input.button', {'text': text, 'style': style},
                     events={'component': {'onActionPerformed': event(guarded(script))}})


def build():
    module = PROJECT / 'ignition/script-python/atsThemeLibrary'
    runtime = (HERE / 'library_runtime.py').read_text(encoding='utf-8')
    module.mkdir(parents=True, exist_ok=True)
    (module / 'code.py').write_text(runtime + '\n\nCATALOG = json.loads(r\'\'\'' +
                                  json.dumps(CATALOG, ensure_ascii=True, separators=(',', ':')) +
                                  "''' )\n", encoding='utf-8')
    script_resource = resource(['code.py'])
    script_resource['scope'] = 'A'
    write_json(module / 'resource.json', script_resource)
    spec = importlib.util.spec_from_file_location('library', module / 'code.py')
    lib = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lib)
    rows = lib.rows_for('light')

    base_selector = component('SourceTheme', 'ia.input.dropdown', {
        'placeholder': {'text': 'Tema de origen'}, 'search': {'enabled': True},
        'options': [{'label': 'Base / ' + t, 'value': t} for t in lib.BUILTINS]},
        {'basis': '230px', 'grow': 0, 'shrink': 0},
        {'props.value': binding('view.custom.sourceTheme', True),
         'props.options': binding('view.custom.themeOptions')})
    target = component('TargetName', 'ia.input.text-field', {'placeholder': 'ats-light', 'deferUpdates': False},
                       {'basis': '250px', 'grow': 1, 'shrink': 1},
                       {'props.text': binding('view.custom.targetName', True)})
    controls = flex('Controls', [label('SourceLabel', 'Origen'), base_selector,
        button('LoadBase', 'Cargar origen', 'atsThemeLibrary.load_into(self.view, self.view.custom.sourceTheme)'),
        button('RefreshThemes', 'Actualizar lista', 'self.view.custom.themeOptions = atsThemeLibrary.theme_options()\nself.view.custom.status = "Lista actualizada."'),
        label('NameLabel', 'Nombre nuevo'), target], wrap='wrap', style={'alignItems': 'center'})

    columns = []
    for field, title, width in [('sample', 'Color', 58), ('name', 'Variable', 235),
                               ('category', 'Grupo', 145), ('default', 'Original', 220),
                               ('value', 'Valor editable', 240), ('resolved', 'Valor resuelto', 220),
                               ('selector', 'Selector', 180), ('source', 'Archivo de origen', 210)]:
        columns.append({'field': field, 'visible': True, 'editable': field == 'value',
                        'render': 'auto', 'width': width, 'strictWidth': False,
                        'resizable': True, 'sortable': True, 'header': {'title': title},
                        'style': {'fontFamily': 'monospace' if field in ('name', 'value', 'default', 'resolved') else 'inherit'}})
    table = component('Variables', 'ia.display.table', {
        'columns': columns, 'data': [], 'enableHeader': True,
        'selection': {'mode': 'single', 'enableRowSelection': True, 'enableColumnSelection': False,
                      'selectedRow': None, 'selectedColumn': None},
        'cells': {'allowEditOn': 'double-click'},
        'filter': {'enabled': True}, 'pager': {'top': False, 'bottom': False},
        'rows': {'height': 36}, 'virtualized': True,
        'style': {'border': '1px solid var(--border)', 'borderRadius': '8px'}},
        {'basis': '0px', 'grow': 1, 'shrink': 1},
        {'props.data': binding('view.custom.rows')},
        {'component': {'onEditCellCommit': event(guarded(
            'if event.column == "value":\n    atsThemeLibrary.edit(self.view, int(event.row), event.value)'))}})

    sample_title = label('SampleTitle', 'Muestra de la paleta', {'fontSize': '17px', 'fontWeight': '600'})
    sample_title['propConfig'] = {'props.style.color': binding('view.custom.preview.text')}
    sample_text = label('SampleText', 'Texto y superficie', {'padding': '14px', 'borderRadius': '6px'})
    sample_text['propConfig'] = {'props.style.color': binding('view.custom.preview.text'),
                                 'props.style.backgroundColor': binding('view.custom.preview.surface')}
    sample_action = label('SampleAction', 'Accion principal', {'padding': '12px', 'color': '#FFFFFF', 'textAlign': 'center'})
    sample_action['propConfig'] = {'props.style.backgroundColor': binding('view.custom.preview.action'),
                                  'props.style.borderRadius': binding('view.custom.preview.radius')}
    sample_input = label('SampleInput', 'Entrada de datos', {'padding': '12px', 'borderWidth': '1px', 'borderStyle': 'solid'})
    sample_input['propConfig'] = {'props.style.backgroundColor': binding('view.custom.preview.input'),
                                'props.style.color': binding('view.custom.preview.text'),
                                'props.style.borderColor': binding('view.custom.preview.border')}
    sample_states = flex('SampleStates', [label('Success', 'Exito', {'padding': '8px'}), label('Error', 'Error', {'padding': '8px'})])
    sample_states['children'][0]['propConfig'] = {'props.style.color': binding('view.custom.preview.success')}
    sample_states['children'][1]['propConfig'] = {'props.style.color': binding('view.custom.preview.error')}
    sample = flex('Sample', [sample_title, sample_text, sample_action, sample_input, sample_states], 'column',
                  {'padding': '18px', 'borderRadius': '8px', 'border': '1px solid var(--border)'})
    sample['propConfig'] = {'props.style.backgroundColor': binding('view.custom.preview.background')}
    css_preview = component('CssPreview', 'ia.display.label', {
        'style': {'fontFamily': 'monospace', 'fontSize': '12px', 'whiteSpace': 'pre-wrap',
                  'overflow': 'auto', 'userSelect': 'text', 'padding': '12px',
                  'backgroundColor': 'var(--container)', 'borderRadius': '6px'}},
        {'basis': '180px', 'grow': 1, 'shrink': 0}, {'props.text': binding('view.custom.cssPreview')})
    side = flex('Preview', [sample, label('PreviewNote', 'Muestra orientativa. El CSS conserva el selector de cada variable.',
                {'fontSize': '12px', 'whiteSpace': 'normal'}), label('CssTitle', 'Overrides que se guardaran'), css_preview],
                'column', position={'basis': '310px', 'grow': 0, 'shrink': 0})
    body = flex('Workspace', [table, side], style={'minHeight': '430px'},
                position={'basis': '480px', 'grow': 1, 'shrink': 0})

    save = 'rows = atsThemeLibrary.plain(self.view.custom.rows)\npath = atsThemeLibrary.save_new(self.view.custom.targetName, self.view.custom.baseTheme, rows)\nself.view.custom.status = "Tema guardado: " + self.view.custom.targetName + ". " + atsThemeLibrary.request_theme_scan()\nself.view.custom.themeOptions = atsThemeLibrary.theme_options()'
    export_json = 'from java.lang import String\nrows = atsThemeLibrary.plain(self.view.custom.rows)\ndata = atsThemeLibrary.manifest_for(self.view.custom.targetName, self.view.custom.baseTheme, rows)\ncontent = system.util.jsonEncode(data, 2)\nsystem.perspective.download(self.view.custom.targetName + ".json", String(content).getBytes("UTF-8"), "application/json")'
    export_zip = 'rows = atsThemeLibrary.plain(self.view.custom.rows)\ncontent = atsThemeLibrary.export_zip(self.view.custom.targetName, self.view.custom.baseTheme, rows)\nsystem.perspective.download(self.view.custom.targetName + ".zip", bytearray(content), "application/zip")'
    reset = 'table = self.parent.parent.getChild("Workspace").getChild("Variables")\nindex = table.props.selection.selectedRow\nif index is None or int(index) < 0:\n    raise ValueError("Selecciona una fila de la tabla.")\natsThemeLibrary.edit(self.view, int(index), "")'
    actions = flex('Actions', [button('SaveAs', 'Guardar como tema nuevo', save, True),
        button('ExportJson', 'Exportar JSON', export_json), button('ExportZip', 'Exportar tema ZIP', export_zip),
        button('ResetVariable', 'Restablecer variable', reset)], wrap='wrap')
    upload = component('ImportJson', 'ia.input.fileupload', {'supportedFileTypes': ['json'], 'fileSizeLimit': 2, 'maxUploads': 1},
                       {'basis': '72px', 'grow': 0, 'shrink': 0}, events={'component': {'onFileReceived': event(guarded(
        'if not event.file.name.lower().endswith(".json"):\n    raise ValueError("Selecciona un archivo .json.")\ncontent = event.file.getString()\nif len(content) > 2000000:\n    raise ValueError("El JSON supera 2 MB.")\nbase, rows, name = atsThemeLibrary.decode_manifest(content)\nself.view.custom.baseTheme = base\nself.view.custom.sourceTheme = base\nself.view.custom.targetName = name\natsThemeLibrary.refresh(self.view, rows)\nself.view.custom.status = "Borrador importado. Revisa los cambios antes de guardar."'))}})
    root = flex('root', [
        label('Title', 'ATS / Biblioteca de temas', {'fontSize': '26px', 'fontWeight': '600'}),
        label('Subtitle', 'Edita variables de los seis temas originales y guarda una copia con nombre propio.', {'color': 'var(--label--disabled)'}),
        controls,
        label('Summary', path='view.custom.summary', style={'fontWeight': '600'}),
        label('Help', 'Doble clic en Valor editable y Enter para confirmar. Busca por nombre o grupo. Un valor vacio restaura el original.', {'fontSize': '12px'}),
        body, actions, label('ImportTitle', 'Importar borrador JSON', {'fontSize': '12px'}), upload,
        label('Status', path='view.custom.status', style={'whiteSpace': 'pre-wrap', 'padding': '12px',
            'backgroundColor': 'var(--container)', 'borderRadius': '6px', 'minHeight': '48px'}),
    ], 'column', {'padding': '24px', 'gap': '12px', 'backgroundColor': 'var(--containerRoot)',
                  'color': 'var(--label)', 'overflow': 'auto'})
    root['events'] = {'system': {'onStartup': event(guarded(
        'atsThemeLibrary.load_into(self.view, "light")\nself.view.custom.themeOptions = atsThemeLibrary.theme_options()'))}}
    preview = {r['name']: r['resolved'] for r in rows}
    view = {'custom': {'sourceTheme': 'light', 'baseTheme': 'light', 'targetName': 'ats-light',
        'themeOptions': [{'label': 'Base / ' + t, 'value': t} for t in lib.BUILTINS],
        'rows': rows, 'cssPreview': lib.css_for('light', rows),
        'summary': '120 variables | 0 cambios | base light | Perspective ' + CATALOG['perspectiveVersion'],
        'status': 'Carga un origen y edita la columna Valor editable. Guardar crea un tema nuevo.',
        'preview': {k: preview[v] for k, v in {'background': '--containerRoot', 'surface': '--container',
          'text': '--label', 'border': '--border', 'action': '--callToAction', 'input': '--input',
          'success': '--success', 'error': '--error', 'radius': '--borderRadius'}.items()}},
        'params': {}, 'props': {'defaultSize': {'width': 1460, 'height': 1030}}, 'root': root}
    # Draft edits are session state, not Designer-persisted installation status.
    view['propConfig'] = {'custom.' + key: {'persistent': False} for key in view['custom']}
    dest = PROJECT / 'com.inductiveautomation.perspective/views/ATS Global/Tools/Theme Library'
    write_json(dest / 'view.json', view)
    write_json(dest / 'resource.json', resource(['view.json']))
    print('Built view:', dest)
    print('Built project script:', module)


if __name__ == '__main__':
    build()
