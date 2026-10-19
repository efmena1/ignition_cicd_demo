# -*- coding: utf-8 -*-
"""Read the generated ZIP using Ignition's actual importer, without a Gateway write."""
import os
from java.io import File
from com.inductiveautomation.ignition.common.project import ProjectFileUtil

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ATS-Theme-Library-Perspective-8.3.zip')
result = ProjectFileUtil.importFromZip(File(path), 'ats-theme-library')
print('Ignition ProjectFileUtil import: OK')
print(result)
print([str(m) for m in result.getClass().getMethods() if m.getName() in ('getResources', 'getProject', 'getManifest')])
