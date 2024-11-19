from __future__ import print_function
from builtins import object

class ConfigParser:

	def __init__(self):
		self.__path = ""
		self.__dict = {}

	def add_section(self, section):
		self.__dict[section] = {}

	def set(self, section, key, value):
		self.__dict[section][key]=value

	def read(self, path):
		self.__path = path
		f = open(path, 'r')
		section = ""
		for line in f:
			line = line.replace('\n','')
			if not len(line):
				continue
			if (line[0]=='[') and (line[-1]==']'):
				section = line[1:-1]
				self.add_section(section)

			elif '=' in line:
				self.set(section, line.split('=')[0], line.split('=')[1])

	def get(self, section, key):
		return list(self.__dict[section].keys())

	def options(self, section):
		return self.__dict[section].keys()

	def remove_option(self, section, key):
		del self.__dict[section][key]

	def write(self, configFile):
		for section in list(self.__dict.keys()):
			configFile.write("["+section+"]")
			for key in list(section.keys()):
				configFile.write(key+"="+self.get(section, key))

if __name__ == "__main__":
	config = ConfigParser()
	config.read("C:\\Users\\phielerm\\.qgis2\\python\\plugins\\GeODinQGIS\\config.cfg")
	# fix_print_with_import
	print (config.options("Options"))
