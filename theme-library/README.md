# ATS Theme Library para Perspective 8.3

Vista editable: `ATS Global/Tools/Theme Library`.

Este paquete contiene una vista y el modulo de scripts `atsThemeLibrary`. El inventario se extrajo del bundle local `perspective-themes-3.3.9.jar`, correspondiente a Perspective `3.3.9.2026082511`. No contiene cambios en los temas originales ni en CSS Installer.

## Instalacion en el Designer

1. Abre el proyecto **base**.
2. Selecciona **File > Import** y abre `ATS-Theme-Library-Perspective-8.3.zip`.
3. Importa la vista `ATS Global/Tools/Theme Library` y el script `atsThemeLibrary`. Guarda el proyecto.
4. Abre la vista en modo Preview, o insertala como Embedded View en tu pagina de herramientas. El proyecto `demo` hereda de `base` y puede utilizarla despues de guardar. No se agrega una ruta publica automaticamente.

El intento de escribir directamente en `projects/base` fue denegado por Windows. Por eso se entrega el paquete de importacion; no se ha instalado ni probado visualmente en una sesion activa.

## Uso

1. Selecciona **Origen** y pulsa **Cargar origen**. Esta accion reemplaza el borrador abierto; exporta su JSON primero si deseas conservarlo.
2. Busca una variable o grupo en el filtro de la tabla.
3. Haz doble clic en **Valor editable**, escribe un valor y pulsa **Enter**. Puedes usar colores hexadecimales, rgb/hsl, valores de dimensiones o referencias `var(--otra-variable)`. Un valor vacio restaura el original.
4. **Original** muestra el valor del tema base. **Valor resuelto** y la muestra de color siguen las referencias entre variables. Las columnas **Selector** y **Archivo de origen** explican donde se declara cada variable; desplaza horizontalmente la tabla si hace falta.
5. Pon un nombre nuevo, por ejemplo `ats-light` o `ats-dark`, y pulsa **Guardar como tema nuevo**.

El guardado se ejecuta en el Gateway y crea:

```text
data/config/resources/core/com.inductiveautomation.perspective/themes/<nombre>/
    config.json
    resource.json
    index.css
    overrides.css
    ats-editor.json
```

El indice importa el tema base completo y despues `overrides.css`. Solo se escriben las variables modificadas; las referencias permanecen como `var(...)`. Se mantiene el selector del slider para sus dos variables locales.

Se solicita al ConfigurationManager de Ignition un escaneo de recursos. Si no se puede solicitar, la vista indica ejecutar manualmente **Scan filesystem de configuracion** en el Gateway; el escaneo de proyectos es distinto. El mensaje confirma el guardado y la solicitud, no la finalizacion del escaneo.

Cuando el nuevo tema este disponible, seleccionalo en `session.props.theme`. La vista no cambia automaticamente el tema de ninguna sesion. La cuenta del servicio de Ignition necesita permiso de escritura en su carpeta de recursos.

**Guardar como** no reemplaza ningun tema existente. Para hacer otra version, carga un tema guardado, editalo y usa un nombre nuevo; se propone el sufijo `-copy`. El boton **Actualizar lista** incluye los temas guardados por esta herramienta.

## Exportacion e importacion

- **Exportar JSON:** guarda un borrador portable, con base, version del catalogo y overrides. Puedes cargarlo usando **Importar borrador JSON**.
- **Exportar tema ZIP:** descarga la carpeta completa de un tema para instalarla en la carpeta de temas de otro Gateway compatible. Este ZIP de tema no es un export de proyecto y no se importa con File > Import del Designer.
- El ZIP principal `ATS-Theme-Library-Perspective-8.3.zip` si es el paquete para importar la vista y sus scripts en el Designer.
- Los borradores se mantienen en la instancia de la vista. Para conservarlos al cerrar, exporta JSON o guarda un tema.

## Alcance del inventario

Se revisaron **93 archivos CSS**, con **278 declaraciones** y **121 nombres distintos** entre los seis temas incluidos. Cada tema resuelve **120 variables**: 118 en `:root` y 2 en `.ia_slider__handle:focus`.

- `light` tiene `--red-90`; `dark` tiene `--red-10` en su lugar.
- `light-cool`, `dark-cool`, `light-warm` y `dark-warm` redefinen diez neutrales cada uno.
- Hay colores, sombras, bordes, radios, tipografia y variables de componentes. No se limita a una paleta de colores.
- `--arrow-color`, `--sliderFocusColor` y `--tooltip-background-color` aparecen como referencias, pero no tienen una declaracion de valor por defecto en estos archivos. No se les inventa un valor en el editor.
- El inventario corresponde a los temas distribuidos con esta version del modulo. No pretende cubrir variables introducidas por otros modulos, hojas de estilo de proyectos, el navegador o versiones futuras de Perspective.
- Los componentes con colores literales o estilos de mayor prioridad pueden no cambiar al modificar una variable.
- La previsualizacion es una muestra de colores y valores, no una simulacion completa de todos los componentes de Perspective. El editor comprueba referencias, ciclos y estructura basica de valores; no sustituye la validacion de propiedades CSS por el navegador.

## Archivos de consulta

- `VARIABLES.md`: tabla completa de valores light/dark y neutrales cool/warm.
- `catalog.json`: catalogo con fuente, selector, linea, valores, usos y hash SHA-256.
- `baselines/*.css`: seis bases completas editables, con referencias y selectores conservados.
- `sources/`: copia de los 93 CSS originales leidos del modulo.
- `project/`: los recursos nuevos listos para empaquetar.

## Verificacion realizada

- 12 pruebas funcionales en CPython y en Jython 2.7.4 incluido en la instalacion.
- Verificacion de propiedades, tipos y enums contra los descriptores de componentes del modulo instalado.
- Lectura del ZIP con `ProjectFileUtil.importFromZip` de Ignition: reconoce la vista y la biblioteca de scripts.
- Las pruebas de guardado usan una carpeta temporal aislada; no crean temas en el Gateway real.
- Pendiente: importacion en el proyecto y verificacion visual/funcional en una sesion de Perspective. No habia un navegador conectado disponible para esa comprobacion.

## Reproducir el inventario y el paquete

Desde `Ignition/data`, con Python 3:

```text
python theme-library/build_catalog.py
python theme-library/build_view.py
python theme-library/test_library.py
python theme-library/validate_view.py
python theme-library/package_project.py
```

Los generadores escriben dentro de `theme-library`, no instalan cambios en el proyecto ni modifican los temas. Si actualizas Perspective, revisa la version registrada en el generador y las diferencias del bundle antes de regenerar el catalogo. Los JSON exportados de otro hash de catalogo se rechazan para evitar mezclar bases de versiones distintas.

## Referencias oficiales

- [Temas incluidos](https://docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/perspective-built-in-themes)
- [Temas personalizados](https://docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/creating-and-using-custom-perspective-themes)
- [Importacion de recursos de proyecto](https://docs.inductiveautomation.com/docs/8.3/platform/projects/project-export-and-import)
- [Escaneo de recursos de configuracion, respuesta de Inductive Automation](https://forum.inductiveautomation.com/t/scan-file-system/111455)
