#!/usr/bin/env python

import sys, pathlib
import avb, avbutils
from PySide6 import QtWidgets, QtCore, QtGui

THUMB_FRAME_MODE_RATE  = range(4, 14)
THUMB_SCRIPT_MODE_RATE = range(3, 8)

FONT_INDEX_OFFSET = 142+12+7
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
		self.setLayout(QtWidgets.QVBoxLayout())

		self.grp_display_modes = QtWidgets.QGroupBox(title="Bin Presentation")
		self.grp_display_modes.setLayout(QtWidgets.QFormLayout())

		display_modes = [(mode.value, mode.name.replace("_"," ").title()) for mode in avbutils.BinDisplayModes]

		self.display_modes_group = QtWidgets.QButtonGroup()
		self.display_modes_layout = QtWidgets.QHBoxLayout()
		for mode in display_modes:
			btn_mode = QtWidgets.QRadioButton(mode[1])
			btn_mode.setProperty("mode_index", mode[0])
			self.display_modes_group.addButton(btn_mode)
			self.display_modes_layout.addWidget(btn_mode)
		
		self.grp_display_modes.layout().addRow("Display Mode:", self.display_modes_layout)


		self.thumb_size_frame_slider = QtWidgets.QSlider(minimum=THUMB_FRAME_MODE_RATE.start, maximum=THUMB_FRAME_MODE_RATE.stop, orientation=QtCore.Qt.Orientation.Horizontal)
		self.grp_display_modes.layout().addRow("Thumbnail Size (Frame Mode):", self.thumb_size_frame_slider)

		self.thumb_size_script_slider = QtWidgets.QSlider(minimum=THUMB_SCRIPT_MODE_RATE.start, maximum=THUMB_SCRIPT_MODE_RATE.stop, orientation=QtCore.Qt.Orientation.Horizontal)
		self.grp_display_modes.layout().addRow("Thumbnail Size (Script Mode):", self.thumb_size_script_slider)

		self.layout().addWidget(self.grp_display_modes)

		self.grp_font = QtWidgets.QGroupBox(title="Bin Font Settings")
		self.grp_font.setLayout(QtWidgets.QFormLayout())

		self.font_layout = QtWidgets.QHBoxLayout()

		self.font_list = QtWidgets.QComboBox()
		self.font_list.addItems(QtGui.QFontDatabase.families())

		self.font_size = QtWidgets.QSpinBox(minimum=FONT_SIZE_RANGE.start, maximum=FONT_SIZE_RANGE.stop)

		self.font_layout.addWidget(self.font_list)
		self.font_layout.addWidget(self.font_size)
		self.grp_font.layout().addRow("Bin Font:", self.font_layout)


		self.btn_color_bg = QtWidgets.QPushButton()
		self.btn_color_bg.setProperty("color", QtGui.QColor())
		self.btn_color_bg.clicked.connect(lambda:self.choose_color(self.btn_color_bg))

		self.btn_color_fg = QtWidgets.QPushButton()
		self.btn_color_fg.setProperty("color", QtGui.QColor())
		self.btn_color_fg.clicked.connect(lambda:self.choose_color(self.btn_color_fg))

		self.grp_font.layout().addRow("Foreground Color:", self.btn_color_fg)
		self.grp_font.layout().addRow("Background Color:", self.btn_color_bg)

		self.layout().addWidget(self.grp_font)

		self.grp_position = QtWidgets.QGroupBox(title="Bin Position && Sizing")
		self.grp_position.setLayout(QtWidgets.QFormLayout())

		self.coord_layout = QtWidgets.QHBoxLayout()
		self.coord_x      = QtWidgets.QSpinBox()
		self.coord_x.setRange(-100000, 100000)
		self.coord_y      = QtWidgets.QSpinBox()
		self.coord_y.setRange(-100000, 100000)

		self.coord_layout.addWidget(QtWidgets.QLabel("X:", alignment=QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignCenter))
		self.coord_layout.addWidget(self.coord_x)

		self.coord_layout.addWidget(QtWidgets.QLabel("Y:", alignment=QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignCenter))
		self.coord_layout.addWidget(self.coord_y)

		self.grp_position.layout().addRow("Position On Screen:", self.coord_layout)

		self.sizing_layout = QtWidgets.QHBoxLayout()
		self.sizing_x      = QtWidgets.QSpinBox()
		self.sizing_x.setRange(-100000, 100000)
		self.sizing_y      = QtWidgets.QSpinBox()
		self.sizing_y.setRange(-100000, 100000)

		self.sizing_layout.addWidget(QtWidgets.QLabel("W:", alignment=QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignCenter))
		self.sizing_layout.addWidget(self.sizing_x)

		self.sizing_layout.addWidget(QtWidgets.QLabel("H:", alignment=QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignCenter))
		self.sizing_layout.addWidget(self.sizing_y)

		self.grp_position.layout().addRow("Size On Screen:", self.sizing_layout)

		self.layout().addWidget(self.grp_position)

		self.layout().addStretch()
		
		
		#for idx, font in enumerate(QtGui.QFontDatabase.families()):
		#	print(idx, font)
	
	def choose_color(self, color_button:QtWidgets.QPushButton):

		new_color = QtWidgets.QColorDialog.getColor(initial=color_button.property("color"))
		if new_color.isValid():
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
	

	def set_screen_position(self, rectangle=QtCore.QRect):		
		self.coord_x.setValue(rectangle.x())
		self.coord_y.setValue(rectangle.y())
	
	def set_screen_size(self, rectangle=QtCore.QRect):
		self.sizing_x.setValue(rectangle.width())
		self.sizing_y.setValue(rectangle.height())

class BinViewPanel(QtWidgets.QWidget):

	def __init__(self):
		super().__init__()

		self.setLayout(QtWidgets.QVBoxLayout())


		self.grp_preset = QtWidgets.QGroupBox("Preset")
		self.grp_preset.setLayout(QtWidgets.QHBoxLayout())

		self.cmb_preset = QtWidgets.QComboBox()
		self.cmb_preset.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Maximum))
		self.cmb_preset.addItem("Default")

		self.btn_save_preset = QtWidgets.QPushButton("+")

		self.grp_preset.layout().addWidget(self.cmb_preset)
		self.grp_preset.layout().addWidget(self.btn_save_preset)

		self.layout().addWidget(self.grp_preset)


		self.tree_columns = QtWidgets.QTreeWidget()
		self.tree_columns.setHeaderLabels(("#", "Name", "Display Format", "Data Type","Hidden"))
		self.tree_columns.setAlternatingRowColors(True)
		self.tree_columns.setIndentation(0)
		self.tree_columns.resizeColumnToContents(0)
		self.tree_columns.setSortingEnabled(True)
		self.tree_columns.setSelectionMode(QtWidgets.QTreeWidget.SelectionMode.ExtendedSelection)
		self.tree_columns.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
		
		self.layout().addWidget(self.tree_columns)

	def set_bin_columns_list(self, columns:list):
		self.tree_columns.clear()
		self.tree_columns.addTopLevelItems([BinViewItem(x) for x in columns])
		[self.tree_columns.resizeColumnToContents(x) for x in range(self.tree_columns.columnCount())]
	
	def set_bin_view_name(self, name:str):
		self.cmb_preset.clear()
		self.cmb_preset.addItem(name)

class BinViewItem(QtWidgets.QTreeWidgetItem):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
	
	def __lt__(self, other:QtWidgets.QTreeWidgetItem):
		sort_column = self.treeWidget().sortColumn()
		return avbutils.human_sort(self.text(sort_column)) < avbutils.human_sort(other.text(sort_column))
	
	@classmethod
	def get_column_data(cls, mob:avb.misc.MobRef):

		
		return [mob.name, str(mob.class_id.decode("utf-8")), str(mob)]



class BinmanMain(QtWidgets.QWidget):
	"""Main window component"""

	def __init__(self):
		super().__init__()

		self.setLayout(QtWidgets.QHBoxLayout())

		self.binpreview = BinPreviewTree()
		self.binpreview.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding))
		self.layout().addWidget(self.binpreview)

		self.tabs = QtWidgets.QTabWidget()
		self.tabs.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.MinimumExpanding))
		

		self.panel_displayproperties = DisplayPropertiesPanel()
		self.panel_displayproperties.set_mode(avbutils.BinDisplayModes.FRAME)
		self.panel_displayproperties.set_thumb_frame_size(80)
		self.panel_displayproperties.set_thumb_script_size(80)

		self.panel_binview = BinViewPanel()

		self.tabs.addTab(self.panel_displayproperties, "Appearance")
		self.tabs.addTab(self.panel_binview, "Bin View")

		self.tabs.addTab(QtWidgets.QWidget(), "Sift && Sort")
		self.tabs.addTab(QtWidgets.QWidget(), "Automation")

		self.layout().addWidget(self.tabs)
	
	@QtCore.Slot()
	def new_bin_loaded(self, bin:avb.bin.Bin):

			self.panel_displayproperties.set_mode(avbutils.BinDisplayModes.get_mode_from_bin(bin))
			self.panel_displayproperties.set_thumb_frame_size(bin.mac_image_scale)
			self.panel_displayproperties.set_thumb_script_size(bin.ql_image_scale)

			self.panel_displayproperties.set_font_family_index(bin.mac_font)
			self.panel_displayproperties.set_font_size(bin.mac_font_size)
			
			self.panel_displayproperties.set_bg_color(QtGui.QColor(QtGui.QRgba64.fromRgba64(*bin.background_color, 1)))
			self.panel_displayproperties.set_fg_color(QtGui.QColor(QtGui.QRgba64.fromRgba64(*bin.forground_color, 1)))


			y1,x1, y2,x2 = bin.home_rect
			bin_rect = QtCore.QRect(QtCore.QPoint(x1,y1),QtCore.QPoint(x2,y2))

			self.panel_displayproperties.set_screen_position(bin_rect)
			self.panel_displayproperties.set_screen_size(bin_rect)

			self.panel_binview.set_bin_view_name(bin.view_setting.name)
			self.panel_binview.set_bin_columns_list(
				[[str(idx+1), col.get("title"),avbutils.BinColumnFormat(col.get("format")).name.replace("_"," ").title(), str(col.get("type")), str(int(col.get("hidden")))] for idx, col in enumerate(bin.view_setting.columns)]
			)

			self.binpreview.clear()
			self.binpreview.setHeaderLabels(col.get("title") for col in bin.view_setting.columns)
			self.binpreview.addTopLevelItems(
				#[BinViewItem(BinViewItem.get_column_data(x.mob)) for x in bin.items if x.user_placed and x.mob in bin.compositionmobs()]
				[BinViewItem(BinViewItem.get_column_data(x)) for x in bin.mobs]
			)

			for item in self.binpreview.findItems("True", QtCore.Qt.MatchFlag.MatchExactly, column=1):
				item.setHidden(True)

			self.binpreview.resizeColumnToContents(0)
	
	@QtCore.Slot()
	def load_bin(self, bin_path:QtCore.QFileInfo):
		print("Opening ", bin_path.absoluteFilePath())
		with avb.open(bin_path.absoluteFilePath()) as bin_handle:
			bin = bin_handle.content
			wnd_main.setWindowTitle(bin_path.fileName())
			self.new_bin_loaded(bin)


class BinPreviewTree(QtWidgets.QTreeWidget):
	"""The bin preview"""

	def __init__(self):

		super().__init__()
		self.setIndentation(0)
		self.setAlternatingRowColors(True)
		self.setSortingEnabled(True)
		self.clear()


class BinmanMenuBar(QtWidgets.QMenuBar):

	sig_bin_chosen = QtCore.Signal(QtCore.QFileInfo)

	def __init__(self):
		super().__init__()

		self.mnu_file  = QtWidgets.QMenu("&File")
		self.addMenu(self.mnu_file)
		self.mnu_tools = QtWidgets.QMenu("&Tools")
		self.addMenu(self.mnu_tools)
		self.mnu_help = QtWidgets.QMenu("&Help")
		self.addMenu(self.mnu_help)
		
		self.mnu_file.addAction("&New Bin")
		self.act_open = self.mnu_file.addAction("&Open Bin...")
		self.act_open.triggered.connect(self.choose_new_bin)
		self.mnu_file.addSeparator()
		self.act_save = self.mnu_file.addAction("&Save Bin As...")
		self.act_save.triggered.connect(self.choose_save_bin)
		self.mnu_file.addSeparator()
		self.mnu_file.addAction("&Quit")
	
	def choose_new_bin(self):

		bin_path, file_mask = QtWidgets.QFileDialog.getOpenFileName(self, "Choose an Avid bin...", filter="*.avb")
		if not bin_path:
			return

		bin_path = QtCore.QFileInfo(bin_path)
		if not bin_path.isFile():
			print("No", file=sys.stderr)
			return
		
		self.sig_bin_chosen.emit(bin_path)
	
	def choose_save_bin(self):

		bin_path, file_mask = QtWidgets.QFileDialog.getSaveFileName(self, "Save a copy of this bin as...", filter="*.avb")
		




		
		



if __name__ == "__main__":

	app = BinmanApp()

	wnd_main = QtWidgets.QMainWindow()
	wnd_main.setCentralWidget(BinmanMain())
	wnd_main.setMenuBar(BinmanMenuBar())
	wnd_main.menuBar().sig_bin_chosen.connect(wnd_main.centralWidget().load_bin)

	if len(sys.argv) > 1:
		bin_path = QtCore.QFileInfo(sys.argv[1])
		wnd_main.centralWidget().load_bin(bin_path)
			


	wnd_main.show()
	BinmanApp.exec()