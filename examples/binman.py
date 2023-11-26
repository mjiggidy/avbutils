#!/usr/bin/env python

import sys, pathlib
import avb, avbutils
from PySide6 import QtWidgets, QtCore, QtGui

THUMB_FRAME_MODE_RATE  = range(4, 14)
THUMB_SCRIPT_MODE_RATE = range(3, 8)

FONT_INDEX_OFFSET = 142+12
""" wat """

FONT_SIZE_RANGE = range(8,100)

class BinmanApp(QtWidgets.QApplication):
	"""Binman"""

	def __init__(self):
		super().__init__()

		self.setApplicationDisplayName("Binman")
	


class DisplayPropertiesPanel(QtWidgets.QWidget):
	"""Bin display properties"""

	def __init__(self):
		super().__init__()
		self.setLayout(QtWidgets.QFormLayout())

		display_modes = [(mode.value, mode.name.replace("_"," ").title()) for mode in avbutils.BinDisplayModes]

		self.display_modes_group = QtWidgets.QButtonGroup()
		self.display_modes_layout = QtWidgets.QHBoxLayout()
		for mode in display_modes:
			btn_mode = QtWidgets.QRadioButton(mode[1])
			btn_mode.setProperty("mode_index", mode[0])
			self.display_modes_group.addButton(btn_mode)
			self.display_modes_layout.addWidget(btn_mode)
		
		self.layout().addRow("Display Mode:", self.display_modes_layout)


		self.thumb_size_frame_slider = QtWidgets.QSlider(minimum=THUMB_FRAME_MODE_RATE.start, maximum=THUMB_FRAME_MODE_RATE.stop, orientation=QtCore.Qt.Orientation.Horizontal)
		self.layout().addRow("Thumbnail Size (Frame Mode):", self.thumb_size_frame_slider)

		self.thumb_size_script_slider = QtWidgets.QSlider(minimum=THUMB_SCRIPT_MODE_RATE.start, maximum=THUMB_SCRIPT_MODE_RATE.stop, orientation=QtCore.Qt.Orientation.Horizontal)
		self.layout().addRow("Thumbnail Size (Script Mode):", self.thumb_size_script_slider)

		self.font_layout = QtWidgets.QHBoxLayout()

		self.font_list = QtWidgets.QComboBox()
		self.font_list.addItems(QtGui.QFontDatabase.families())

		self.font_size = QtWidgets.QSpinBox(minimum=FONT_SIZE_RANGE.start, maximum=FONT_SIZE_RANGE.stop)

		self.font_layout.addWidget(self.font_list)
		self.font_layout.addWidget(self.font_size)
		self.layout().addRow("Bin Font:", self.font_layout)


		self.btn_color_bg = QtWidgets.QPushButton()
		self.btn_color_bg.setProperty("color", QtGui.QColor())
		self.btn_color_bg.clicked.connect(lambda:self.choose_color(self.btn_color_bg))

		self.btn_color_fg = QtWidgets.QPushButton()
		self.btn_color_fg.setProperty("color", QtGui.QColor())
		self.btn_color_fg.clicked.connect(lambda:self.choose_color(self.btn_color_fg))

		self.layout().addRow("Foreground Color:", self.btn_color_fg)
		self.layout().addRow("Background Color:", self.btn_color_bg)
		
		#for idx, font in enumerate(QtGui.QFontDatabase.families()):
		#	print(idx, font)
	
	def choose_color(self, color_button:QtWidgets.QPushButton):

		new_color = QtWidgets.QColorDialog.getColor(initial=color_button.property("color"))
		if new_color:
			self.set_color(color_button, new_color)
	
	def set_color(self, color_button:QtWidgets.QPushButton, color:QtGui.QColor):
		color_button.setProperty("color", color)
		color_button.setStyleSheet(f"background-color: {color.name()};")
	
	def set_bg_color(self, color:QtGui.QColor):
		self.set_color(self.btn_color_bg, color)

	def set_fg_color(self, color:QtGui.QColor):
		self.set_color(self.btn_color_fg, color)
			
	
	def set_mode(self, mode:avbutils.BinDisplayModes):
		"""Set the current mode"""

		for button in self.display_modes_group.buttons():
			if button.property("mode_index") == mode.value:
				button.setChecked(True)
				break
	
	def set_thumb_frame_size(self, size:int):
		"""Set the thumbnail size for Frame Mode"""

		self.thumb_size_frame_slider.setValue(size)

	def set_thumb_script_size(self, size:int):
		"""Set the thumbnail size for Frame Mode"""

		self.thumb_size_script_slider.setValue(size)
	
	def set_font_family_index(self, index:int):
		print(index, " + ", FONT_INDEX_OFFSET)
		self.font_list.setCurrentIndex(index - FONT_INDEX_OFFSET)

	def set_font_size(self, size:int):
		self.font_size.setValue(size)





class BinmanMain(QtWidgets.QWidget):
	"""Main window component"""

	def __init__(self):
		super().__init__()

		self.setLayout(QtWidgets.QVBoxLayout())

		self.panel_displayproperties = DisplayPropertiesPanel()
		self.panel_displayproperties.set_mode(avbutils.BinDisplayModes.FRAME)
		self.panel_displayproperties.set_thumb_frame_size(80)
		self.panel_displayproperties.set_thumb_script_size(80)

		self.layout().addWidget(self.panel_displayproperties)



if __name__ == "__main__":

	app = BinmanApp()

	wnd_main = QtWidgets.QMainWindow()
	wnd_main.setCentralWidget(BinmanMain())

	if len(sys.argv) > 1:
		with avb.open(sys.argv[1]) as bin_handle:
			bin = bin_handle.content

			wnd_main.setWindowTitle(pathlib.Path(sys.argv[1]).name)

			wnd_main.centralWidget().panel_displayproperties.set_mode(avbutils.BinDisplayModes.get_mode_from_bin(bin))
			wnd_main.centralWidget().panel_displayproperties.set_thumb_frame_size(bin.mac_image_scale)
			wnd_main.centralWidget().panel_displayproperties.set_thumb_script_size(bin.ql_image_scale)

			wnd_main.centralWidget().panel_displayproperties.set_font_family_index(bin.mac_font)
			wnd_main.centralWidget().panel_displayproperties.set_font_size(bin.mac_font_size)
			
			wnd_main.centralWidget().panel_displayproperties.set_bg_color(QtGui.QColor(QtGui.QRgba64.fromRgba64(*bin.background_color, 1)))
			wnd_main.centralWidget().panel_displayproperties.set_fg_color(QtGui.QColor(QtGui.QRgba64.fromRgba64(*bin.forground_color, 1)))

			


	wnd_main.show()
	BinmanApp.exec()