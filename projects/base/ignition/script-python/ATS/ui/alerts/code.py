"""
ats.ui.alerts
Wrapper para el componente Global/Components/AlertDialog.

Uso:
    from ats.ui import alerts
    alerts.success("The form was saved.", title="Form saved")
    alerts.danger("Could not save.", details="```\\n%s\\n```" % str(e))
"""

VIEW_PATH = "ATS/Components/Alerts/AlertDialog"

LEVELS = ("info", "success", "warning", "danger", "laboratory")

WIDTHS = {"compact": 380, "standard": 460, "wide": 560}

AUTO_CLOSE = {
	"success": 4000,
	"info": 6000,
	"warning": 0,
	"danger": 0,
	"laboratory": 0
}

DISMISSABLE = {
	"success": True,
	"info": True,
	"warning": True,
	"danger": False,
	"laboratory": True
}

DEFAULT_PRIMARY = "Accept"


def show(level="info", message="", title="", details="",
         primaryText=None, secondaryText="", popupId=None,
         size=None, autoCloseMs=None, width=None):
	"""
	Abre el AlertDialog.

	level         info | success | warning | danger | laboratory
	message       texto principal, obligatorio en la práctica
	title         encabezado; si va vacío la vista aplica su fallback
	details       markdown opcional; para trazas usa bloque de código
	primaryText   etiqueta del botón principal
	secondaryText etiqueta del botón secundario; vacío lo oculta
	popupId       identificador; por defecto uno por nivel
	size          compact | standard | wide
	autoCloseMs   ms hasta el cierre automático; 0 lo desactiva
	width         ancho explícito en px, tiene prioridad sobre size
	"""

	level = (level or "info").strip().lower()
	if level not in LEVELS:
		level = "info"

	pid = popupId or ("alert-" + level)

	if size is None:
		size = "wide" if details else "standard"

	popupWidth = width or WIDTHS.get(size, 460)

	if autoCloseMs is None:
		autoCloseMs = AUTO_CLOSE.get(level, 0)

	primary = primaryText if primaryText is not None else DEFAULT_PRIMARY
	if not primary:
		primary = DEFAULT_PRIMARY

	system.perspective.openPopup(
		id=pid,
		view=VIEW_PATH,
		params={
			"level": level,
			"title": title or "",
			"message": message or "",
			"details": details or "",
			"primaryText": primary,
			"secondaryText": secondaryText or "",
			"showSecondary": bool(secondaryText),
			"popupId": pid,
			"autoCloseMs": autoCloseMs
		},
		showCloseIcon=False,
		draggable=False,
		modal=True,
		resizable=False,
		overlayDismiss=DISMISSABLE.get(level, True),
		position={"width": popupWidth},
		viewportBound=True
	)

	return pid


def success(message, **kwargs):
	return show("success", message, **kwargs)


def info(message, **kwargs):
	return show("info", message, **kwargs)


def warning(message, **kwargs):
	return show("warning", message, **kwargs)


def danger(message, **kwargs):
	return show("danger", message, **kwargs)


def confirm(message, title="", onConfirmText="Confirm", onCancelText="Cancel",
            level="warning", details=""):
	"""
	Diálogo de confirmación. El resultado llega por mensaje 'alert-result'
	con payload {"popupId": ..., "action": "primary"|"secondary"}.
	"""
	return show(
		level=level,
		message=message,
		title=title,
		details=details,
		primaryText=onConfirmText,
		secondaryText=onCancelText,
		popupId="alert-confirm",
		autoCloseMs=0
	)


def fromException(e, message=None, title=None, mapping=None):
	"""
	Convierte una excepción en un popup.

	mapping  dict opcional {fragmento_en_el_error: (level, title, message)}
	         para traducir errores conocidos a lenguaje de negocio.
	"""
	errorText = str(e)

	if mapping:
		for needle, (lvl, ttl, msg) in mapping.items():
			if needle in errorText:
				return show(level=lvl, message=msg, title=ttl)

	return show(
		level="danger",
		message=message or "The operation could not be completed.",
		title=title or "Operation failed",
		details="```\n%s\n```" % errorText,
		size="wide"
	)