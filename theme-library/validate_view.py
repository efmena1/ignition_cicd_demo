"""Check explicit component props against installed Perspective descriptors.

Omitted properties receive Perspective's defaults. This checks declared fields,
types, and enums; it does not claim to replace an actual browser render.
"""
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
with zipfile.ZipFile(next((HERE.parent / 'jar-cache/com.inductiveautomation.perspective').glob('*perspective-common-*.jar'))) as z:
    descriptors = {c['id']: c for c in json.loads(z.read('ia.components.json'))['components']}
    schemas = {n: json.loads(z.read(n)) for n in z.namelist() if n.startswith('schemas/') and n.endswith('.json')}

checks = 0


def validate(value, schema, path):
    global checks
    if '$ref' in schema:
        ref = schema['$ref'].replace('urn:ignition-schema:', '')
        if ref in schemas:
            schema = schemas[ref]
    types = schema.get('type', [])
    types = [types] if isinstance(types, str) else types
    valid = {'object': isinstance(value, dict), 'array': isinstance(value, list),
             'string': isinstance(value, str), 'number': isinstance(value, (int, float)) and not isinstance(value, bool),
             'integer': isinstance(value, int) and not isinstance(value, bool),
             'boolean': isinstance(value, bool), 'null': value is None}
    if types:
        assert any(valid[t] for t in types), (path, 'wrong type', value, types)
    if 'enum' in schema:
        assert value in schema['enum'], (path, 'wrong enum', value)
    checks += 1
    if isinstance(value, dict):
        for k, v in value.items():
            props = schema.get('properties', {})
            if k in props:
                validate(v, props[k], path + '.' + k)
            elif schema.get('additionalProperties') is False:
                raise AssertionError((path, 'unknown property', k))
    elif isinstance(value, list) and isinstance(schema.get('items'), dict):
        for i, v in enumerate(value):
            validate(v, schema['items'], path + '[%s]' % i)


def visit(node, parent=None):
    name = node['meta']['name']
    desc = descriptors[node['type']]
    # Explicit root properties must exist even if a schema allows extensions.
    assert set(node['props']) <= set(desc['schema']['properties']), name
    validate(node['props'], desc['schema'], name + '.props')
    if parent:
        validate(node.get('position', {}), parent['childPositionSchema'], name + '.position')
    supported_events = {e['name'] for e in desc.get('events', [])}
    for event in node.get('events', {}).get('component', {}):
        assert event in supported_events, (name, event)
    for child in node.get('children', []):
        visit(child, desc)


view = json.loads((HERE / 'project/com.inductiveautomation.perspective/views/ATS Global/Tools/Theme Library/view.json').read_text())
visit(view['root'])
print('Installed component descriptor checks:', checks, 'OK')
