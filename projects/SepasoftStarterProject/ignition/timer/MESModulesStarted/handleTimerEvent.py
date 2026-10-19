def handleTimerEvent():
	started = False
	try:
		started = system.mes.isProductionStarted()

	except:
		pass

	tags = [{
		'name': 'MESModuleStarted',
		'tagType': 'AtomicTag',
		'valueSource': 'memory',
		'dataType': 'Boolean',
		'value': started
	}]
	system.tag.configure('[default]', tags, 'o')
