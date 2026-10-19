def recordInspection(operationName, operationEquipmentPath, materialNameIn1, lotNoIn1, quantityIn1, uomIn1, materialNameOut1, lotNoOut1, quantityOut1, destinationEquipmentPathOut1):
	"""One input, one output - e.g. quality inspection, re-labeling, movement between locations."""
	materialIn1 = system.mes.trace.configureMaterial(
		name="Input 1",
		lotNo=lotNoIn1,
		materialName=materialNameIn1,
		quantity=quantityIn1,
		UOM=uomIn1)

	materialOut1 = system.mes.trace.configureMaterial(
		name="Output 1",
		lotNo=lotNoOut1,
		materialName=materialNameOut1,
		quantity=quantityOut1,
		equipmentPath=destinationEquipmentPathOut1,
		autoCreateLot=True)

	system.mes.trace.recordOperation(
		name=operationName,
		equipmentPath=operationEquipmentPath,
		materialIn=[materialIn1],
		materialOut=[materialOut1])


def recordSplit(operationName, operationEquipmentPath, materialNameIn1, lotNoIn1, quantityIn1, uomIn1, materialNameOut1, lotNoOut1, quantityOut1, destinationEquipmentPathOut1, materialNameOut2, lotNoOut2, quantityOut2, destinationEquipmentPathOut2):
	"""One input, multiple outputs - e.g. splitting a bulk lot into smaller lots, cutting stock into pieces."""
	materialIn1 = system.mes.trace.configureMaterial(
		name="Input 1",
		lotNo=lotNoIn1,
		materialName=materialNameIn1,
		quantity=quantityIn1,
		UOM=uomIn1)

	materialOut1 = system.mes.trace.configureMaterial(
		name="Output 1",
		lotNo=lotNoOut1,
		materialName=materialNameOut1,
		quantity=quantityOut1,
		equipmentPath=destinationEquipmentPathOut1,
		autoCreateLot=True)

	materialOut2 = system.mes.trace.configureMaterial(
		name="Output 2",
		lotNo=lotNoOut2,
		materialName=materialNameOut2,
		quantity=quantityOut2,
		equipmentPath=destinationEquipmentPathOut2,
		autoCreateLot=True)

	system.mes.trace.recordOperation(
		name=operationName,
		equipmentPath=operationEquipmentPath,
		materialIn=[materialIn1],
		materialOut=[materialOut1, materialOut2])


def recordBlend(operationName, operationEquipmentPath, materialNameIn1, lotNoIn1, quantityIn1, uomIn1, materialNameIn2, lotNoIn2, quantityIn2, uomIn2, materialNameOut1, lotNoOut1, quantityOut1, destinationEquipmentPathOut1):
	"""Multiple inputs, one output - e.g. blending raw materials into a batch, assembly of components, kitting."""
	materialIn1 = system.mes.trace.configureMaterial(
		name="Input 1",
		lotNo=lotNoIn1,
		materialName=materialNameIn1,
		quantity=quantityIn1,
		UOM=uomIn1)

	materialIn2 = system.mes.trace.configureMaterial(
		name="Input 2",
		lotNo=lotNoIn2,
		materialName=materialNameIn2,
		quantity=quantityIn2,
		UOM=uomIn2)

	materialOut1 = system.mes.trace.configureMaterial(
		name="Output 1",
		lotNo=lotNoOut1,
		materialName=materialNameOut1,
		quantity=quantityOut1,
		equipmentPath=destinationEquipmentPathOut1,
		autoCreateLot=True)

	system.mes.trace.recordOperation(
		name=operationName,
		equipmentPath=operationEquipmentPath,
		materialIn=[materialIn1, materialIn2],
		materialOut=[materialOut1])


def recordRework(operationName, operationEquipmentPath, materialNameIn1, lotNoIn1, quantityIn1, uomIn1, materialNameIn2, lotNoIn2, quantityIn2, uomIn2, materialNameOut1, lotNoOut1, quantityOut1, destinationEquipmentPathOut1, materialNameOut2, lotNoOut2, quantityOut2, destinationEquipmentPathOut2):
	"""Multiple inputs, multiple outputs - e.g. rework producing reworked and scrap lots, disassembly and re-kitting."""
	materialIn1 = system.mes.trace.configureMaterial(
		name="Input 1",
		lotNo=lotNoIn1,
		materialName=materialNameIn1,
		quantity=quantityIn1,
		UOM=uomIn1)

	materialIn2 = system.mes.trace.configureMaterial(
		name="Input 2",
		lotNo=lotNoIn2,
		materialName=materialNameIn2,
		quantity=quantityIn2,
		UOM=uomIn2)

	materialOut1 = system.mes.trace.configureMaterial(
		name="Output 1",
		lotNo=lotNoOut1,
		materialName=materialNameOut1,
		quantity=quantityOut1,
		equipmentPath=destinationEquipmentPathOut1,
		autoCreateLot=True)

	materialOut2 = system.mes.trace.configureMaterial(
		name="Output 2",
		lotNo=lotNoOut2,
		materialName=materialNameOut2,
		quantity=quantityOut2,
		equipmentPath=destinationEquipmentPathOut2,
		autoCreateLot=True)

	system.mes.trace.recordOperation(
		name=operationName,
		equipmentPath=operationEquipmentPath,
		materialIn=[materialIn1, materialIn2],
		materialOut=[materialOut1, materialOut2])


def recordReceive(operationName, operationEquipmentPath, materialNameOut1, lotNoOut1, quantityOut1, destinationEquipmentPathOut1):
	"""No tracked input, one output - e.g. receiving raw material or finished goods into the system for the first time."""
	if not lotNoOut1:
		#no lot number given, so generate one from the current time
		lotNoOut1 = "lot-" + str(system.date.toMillis(system.date.now()))

	materialOut1 = system.mes.trace.configureMaterial(
		name="Output 1",
		lotNo=lotNoOut1,
		materialName=materialNameOut1,
		quantity=quantityOut1,
		equipmentPath=destinationEquipmentPathOut1,
		autoCreateLot=True)

	system.mes.trace.recordOperation(
		name=operationName,
		equipmentPath=operationEquipmentPath,
		materialIn=[],
		materialOut=[materialOut1])


def recordScrap(operationName, operationEquipmentPath, materialNameIn1, lotNoIn1, quantityIn1, uomIn1):
	"""One input, no tracked output - e.g. scrapping a failed lot, consuming tooling or consumables."""
	materialIn1 = system.mes.trace.configureMaterial(
		name="Input 1",
		lotNo=lotNoIn1,
		materialName=materialNameIn1,
		quantity=quantityIn1,
		UOM=uomIn1)

	system.mes.trace.recordOperation(
		name=operationName,
		equipmentPath=operationEquipmentPath,
		materialIn=[materialIn1],
		materialOut=[])
