# -*- coding: CP1250 -*-

from __future__ import print_function
from builtins import str
from builtins import range
from builtins import object
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *
import sys, os, decimal, random, string, time
	
class ShapeFromPoint(object):

	def __init__(self, main, queryObject):
		self.main = main
		self.shapeName = queryObject.name
		self.objects = queryObject.objects
		self.project = queryObject.parent
		self.database = queryObject.parent.parent
		
		# reference to the map canvas
		self.canvas = self.main.iface.mapCanvas()
		
		if not self.database:
			self.database = self.project
		
		if len(self.objects):
			self.buildLayer()

	def buildLayer(self):
		
		displayName = self.database.name+'_'+self.project.name+'_'+self.shapeName.replace('/','')
		vectorLayer = QgsVectorLayer("Point", displayName, "memory")

		provider = vectorLayer.dataProvider()
		vectorLayer.startEditing()

		# create field names for vector layer
		attributeList = [QgsField("INVID", QVariant.String),
								QgsField("SHORTNAME", QVariant.String),
								QgsField("LONGNAME",  QVariant.String),
								QgsField("XCOORD", QVariant.Double),
								QgsField("YCOORD", QVariant.Double),
								QgsField("DBTYPE", QVariant.String),
								QgsField("DATABASE", QVariant.String),
								QgsField("PRJNAME", QVariant.String),
								QgsField("PRJID", QVariant.String),
								QgsField("OBJECTTYPE", QVariant.String),
								QgsField("EPSG", QVariant.Int)]
		
		for key in list(self.objects[0].data.keys()):
			try:
				value = float(self.objects[0].data[key])
				field = QgsField(key, QVariant.Double)
				attributeList.append(field)
			except:
				pass
			try:
				value = str(self.objects[0].data[key])
				field = QgsField(key, QVariant.String)
				attributeList.append(field)
			except:
				pass
		
		# add fields to attribute table
		provider.addAttributes(attributeList)
		epsg = 4326

		for object in self.objects:
			epsg = object.epsg
			# add feature
			feat = QgsFeature()
			if object.coordinates[0] == None or object.coordinates[1] == None:
				continue
			#print object.coordinates[0], float(object.coordinates[0]), object.coordinates[1], float(object.coordinates[1])
			feat.setGeometry( QgsGeometry.fromPointXY(QgsPointXY(object.coordinates[0], object.coordinates[1])) )
			attribute = [object.invid, 
							object.shortname, 
							object.name, 
							float(object.coordinates[0]), 
							float(object.coordinates[1]), 
							self.database.options["connection"], 
							self.database.filepath, 
							object.parent.name, 
							object.parent.id, 
							object.locname,
							object.epsg]

			for key in list(object.data.keys()):
				if isinstance(object.data[key], decimal.Decimal):
					attribute.append(float(object.data[key]))
				else:
					attribute.append(object.data[key])
			feat.setAttributes(attribute)
			provider.addFeatures([feat])

			# Commit changes
			vectorLayer.commitChanges()
		epsgString = 'EPSG:'+str(epsg)
		#http://qgis.org/api/2.18/classQgsVectorFileWriter.html#ab566ed2016352c37d9a4a6900614eac2
		error = ""
		#fileName = displayName.replace('\\','').replace(':','').replace('*','').replace('?','').replace('"','').replace('<','').replace('>','').replace('|','').replace('/','').strip().replace(' ','_')
		#generating random string for filename
		fileName = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
		layer = None
		CoordinateReferenceSystem = QgsCoordinateReferenceSystem(epsgString)
			
		if self.main.config.get("Options", "savelayer") == "True":
			fileName = os.path.join(self.main.tmpDirectory, fileName+'.sqlite').replace('\\', '/')
			#layer = QgsVectorLayer(fileName, displayName, "ogr")
			#layer.setCrs(CoordinateReferenceSystem)

			#writeAsVectorFormat is depricated since Qgis 3.0 and writeAsVectorFormatV2 is depricated since Qgis 3.20
			#original line: error = QgsVectorFileWriter.writeAsVectorFormat(vectorLayer, fileName, 'CP1250', CoordinateReferenceSystem, 'SpatiaLite', False, None,['SPATIALITE=YES'])
			save_options = QgsVectorFileWriter.SaveVectorOptions()
			transform_context = QgsProject.instance().transformContext()
			save_options.fileEncoding = 'CP1250'
			save_options.datasourceOptions = ['SPATIALITE=YES']
			save_options.driverName = 'SpatiaLite'

			if Qgis.QGIS_VERSION_INT >= 32000:
				error = QgsVectorFileWriter.writeAsVectorFormatV3(vectorLayer, fileName, transform_context, save_options)
			else :
				error = QgsVectorFileWriter.writeAsVectorFormatV2(vectorLayer, fileName, transform_context, save_options)
			layer = QgsVectorLayer(fileName, displayName, "ogr")
			layer.setCrs(CoordinateReferenceSystem)

		else:
			fileName = os.path.join(self.main.tmpDirectory, fileName+'.shp')

			#layer = QgsVectorLayer(fileName, displayName, "ogr")
			#layer.setCrs(CoordinateReferenceSystem)

			#error = QgsVectorFileWriter.writeAsVectorFormat(vectorLayer, fileName, 'utf-8', CoordinateReferenceSystem, 'ESRI Shapefile')
			#original line: error = QgsVectorFileWriter.writeAsVectorFormat(vectorLayer, fileName, 'CP1250', CoordinateReferenceSystem, 'ESRI Shapefile')
			save_options = QgsVectorFileWriter.SaveVectorOptions()
			transform_context = QgsProject.instance().transformContext()
			save_options.fileEncoding = 'CP1250'
			save_options.driverName = 'ESRI Shapefile'

			if Qgis.QGIS_VERSION_INT >= 32000:
				error = QgsVectorFileWriter.writeAsVectorFormatV3(vectorLayer, fileName, transform_context, save_options)
			else :
				error = QgsVectorFileWriter.writeAsVectorFormatV2(vectorLayer, fileName, transform_context, save_options)
			layer = QgsVectorLayer(fileName, displayName, "ogr")
			layer.setCrs(CoordinateReferenceSystem)

		print(error)
		if error[0] == 0:
			# fix_print_with_import
			print("NoError")
			#time.sleep(10)
			#fileName = r"C:\Users\d.bohrmann\.qgis2\python\plugins\GeODinQGIS\tmp\8FNWNWS6KQW5J1BXCAQX.sqlite"
			#displayName = "testlayer"
			#layer = QgsVectorLayer(fileName, displayName, "ogr")
			#layer.setCrs(CoordinateReferenceSystem)
			QgsProject.instance().addMapLayer(layer)
		elif error == QgsVectorFileWriter.ErrDriverNotFound :
			# fix_print_with_import
			print("ErrDriverNotFound ")
		elif error == QgsVectorFileWriter.ErrCreateDataSource :
			QApplication.restoreOverrideCursor()
			QMessageBox.critical(QWidget(), "Error", "ErrCreateDataSource")
			# fix_print_with_import
			print("ErrCreateDataSource ")
		elif error == QgsVectorFileWriter.ErrCreateLayer :
			# fix_print_with_import
			print("ErrCreateLayer ")
		elif error == QgsVectorFileWriter.ErrAttributeTypeUnsupported :
			# fix_print_with_import
			print("ErrAttributeTypeUnsupported ")
		elif error == QgsVectorFileWriter.ErrAttributeCreationFailed :
			# fix_print_with_import
			print("ErrAttributeCreationFailed ")
		elif error == QgsVectorFileWriter.ErrProjection :
			# fix_print_with_import
			print("ErrProjection ")
		elif error == QgsVectorFileWriter.ErrFeatureWriteFailed :
			# fix_print_with_import
			print("ErrFeatureWriteFailed ")
		elif error == QgsVectorFileWriter.ErrInvalidLayer :
			# fix_print_with_import
			print("ErrInvalidLayer ")
		elif error == QgsVectorFileWriter.Canceled :
			QApplication.restoreOverrideCursor()
			QMessageBox.critical(QWidget(), "Error", "Writing was interrupted tby manual cancelation.")
			# fix_print_with_import
			print("Canceled ")
		
		