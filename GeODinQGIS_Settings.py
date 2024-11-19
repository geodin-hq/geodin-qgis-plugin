from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from .pythonmodules.helpFunction import *


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib, shutil, configparser, win32api

from .ui_Files.ui_GeODinQGIS_Settings import Ui_Settings

class Settings(QDialog, Ui_Settings):

	def __init__(self, main):
		# setup UI and connect the buttons
		QDialog.__init__(self)

		self.setupUi(self)
		
		self.main = main

		# connect buttons to their functions
		self.btn_del_tmp.clicked.connect(self.deleteTmp)
		self.btn_mail.clicked.connect(self.sendMail)
		self.btn_dir.clicked.connect(self.Tmp_Dir)
		self.btn_geodin.clicked.connect(self.GeODin_Dir)
		self.btn_defdir.clicked.connect(self.Def_Dir)
		self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.okClick)
		self.btn_info.clicked.connect(self.openInfo)

		# manage button icons
		self.btn_info.setIcon(QIcon(":\plugins\GeODinQGIS\icons\info.png"))
		self.btn_del_tmp.setIcon(QIcon(":\plugins\GeODinQGIS\icons\i_102F.png"))
		self.btn_del_tmp.setIconSize(QSize(24, 24))

		# path of tmp folder in home directory
		self.tmpDirectory = main.tmpDirectory
		# path of geodin folder
		self.geodinDirectory = main.geodin_dir

		self.dict = main.dictionary
		self.lang = main.lang
		self.errorLog = main.logDirectory+"\\error.log"
		
		self.setWindowTitle(self.dict.getWord(self.lang,"Settings"))
		self.lbl_del.setText(self.dict.getWord(self.lang,"Delete temporary files"))
		self.lbl_surpress.setText(self.dict.getWord(self.lang,"Suppress attribute form pop-up after feature creation"))
		self.btn_mail.setText(self.dict.getWord(self.lang,"Send Email"))
		self.lbl_dir.setText(self.dict.getWord(self.lang,"Directory to save vector layers"))
		self.lbl_lyr.setText(self.dict.getWord(self.lang,"Save Layer as"))
		self.btn_defdir.setText(self.dict.getWord(self.lang,"Restore Default"))
		self.lbl_geodin.setText(self.dict.getWord(self.lang,"GeODin installation path"))
		
		self.logFile()
		
		self.configFile = main.configFile
		self.config = main.config
		self.readConfigFile()

		self.exec_()
		
	def Tmp_Dir(self):
		# enter custom directory for temporary files
		self.tmpDirectory = QFileDialog.getExistingDirectory(self)
		if self.tmpDirectory:
			self.le_dir.setText(self.tmpDirectory)
			
	def GeODin_Dir(self):
		#self.geodinDirectory = QFileDialog.getExistingDirectory(self)
		gdir = self.geodinDirectory
		if os.path.isdir(gdir):
			gdir, __ = QFileDialog.getOpenFileName(self, 'GeODin', gdir, 'geodin.exe')
		else:
			gdir, __ = QFileDialog.getOpenFileName(self, 'GeODin', 'C:/Program Files (x86)/', 'geodin.exe')
		if gdir:
			self.geodinDirectory = os.path.dirname(os.path.dirname(gdir))
			self.le_geodin.setText(self.geodinDirectory)
			
	def Def_Dir(self):
		# restore default directory for temporary files
		self.le_dir.setText(self.main.def_tmp_dir)
		self.le_geodin.setText('C:/Program Files (x86)/GeODin')
		
	def readConfigFile(self):
		self.le_dir.setText(self.config.get('Options', 'tmpdirectory'))
		self.le_geodin.setText(self.config.get('Options', 'geodinrootdir'))
		
		if self.config.get("Options", "suppressattribute") == "True":
			self.checkBox.setChecked(True)
		else:
			self.checkBox.setChecked(False)
			
		if self.config.get("Options", "savelayer") == "True":
			self.rbtn_sql.setChecked(True)
#			self.rbtn_sql.setChecked(False)
		else:
			self.rbtn_shp.setChecked(True)
#			self.rbtn_shp.setChecked(False)

		
	def okClick(self):
		self.main.tmpDirectory = self.le_dir.text()
		self.main.geodin_dir = self.le_geodin.text()
		
		if self.checkBox.isChecked():
			self.config.set('Options', "suppressattribute", "True")
			QSettings().setValue( '/qgis/digitizing/disable_enter_attribute_values_dialog', True )
		else:
			self.config.set('Options', "suppressattribute", "False")
			QSettings().setValue( '/qgis/digitizing/disable_enter_attribute_values_dialog', False )
			
		if self.rbtn_sql.isChecked():
			self.config.set('Options', "savelayer", "True")
		else:
			self.config.set('Options', "savelayer", "False")
		
		self.config.set('Options', 'tmpdirectory', self.le_dir.text())
		self.config.set('Options', 'geodinrootdir', self.le_geodin.text())
			
		self.saveConfig()			
			
	def saveConfig(self):
		print ('option 1')
		with open(self.configFile, 'w') as configFile:
			self.config.write(configFile)
			
	def deleteTmp(self):
		# delete files in tmp-directory
		try:
			for subFile in os.listdir(self.tmpDirectory):
				subFilePath = os.path.join(self.tmpDirectory, subFile)
				if os.path.isfile(subFilePath):
					try:
						os.unlink(subFilePath)
					except:
						pass
				elif os.path.isdir(subFilePath): 
					try:
						shutil.rmtree(subFilePath)
					except:
						pass
			QMessageBox.information(None,self.dict.getWord(self.lang,"Deletion"),self.dict.getWord(self.lang,"Temporary files deleted successfully"))
		except Exception as e:
            # fix_print_with_import
			print(str(e))
			return
			
	def logFile(self):
		# print size of error log file in kb
		size = str(round(float(os.path.getsize(self.errorLog))/1000)) + " kb"
		self.lbl_size.setText(size)
		
	def sendMail(self):
		# send email to GeODin support team
		# email browser is automatically openend
		# error log file must be attached manually
		# text from error message is appreciated
		email = "mailto:"
		receiver = "support@geodin.com"
		cc = [""]
		bcc = [""]
		subject = "Fehlermeldung GeODin QGIS"
		body = "Es ist ein Fehler bei der Arbeit mit GeODinQGIS aufgetreten.\n\nDas Fehlerprotokoll befindet sich im Anhang."
		
		body = body.replace(' ', '%20').replace('\n', '%0D%0A').replace('=',':').replace('"',"'")
		email += receiver +'&SUBJECT='+subject+'&BODY='+body+'&attachment='+r'file://C:/Users/phielerm/.qgis2/python/plugins/GeODinQGIS/logs/error.log'
		print(email)
		win32api.ShellExecute(0, 'open', email, None, None, 0)

	def attrsDialog(self):
		# get user defined current setting
		disableDialog = QSettings().value( '/qgis/digitizing/disable_enter_attribute_values_dialog')
		# override setting
		QSettings().setValue( '/qgis/digitizing/disable_enter_attribute_values_dialog', True )
		# restore setting
		QSettings().setValue( '/qgis/digitizing/disable_enter_attribute_values_dialog', disableDialog )
		
	def openInfo(self):
#		print "Info"
		info = Info()