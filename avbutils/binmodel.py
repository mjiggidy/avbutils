import typing, sys, pprint
import avb, avbutils, timecode
from PySide6 import QtCore, QtWidgets, QtGui

class FilterControls(QtWidgets.QGroupBox):

	filters_changed = QtCore.Signal(bool, bool)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self._setup_widgets()
	
	def _setup_widgets(self):
		self.setLayout(QtWidgets.QVBoxLayout())

		self.chk_show_user_placed = QtWidgets.QCheckBox("Show User Placed")
		self.chk_show_user_placed.setChecked(True)
		self.chk_show_user_placed.stateChanged.connect(self.filter_changed)
		self.chk_show_reference_clips = QtWidgets.QCheckBox("Show Reference Clips")
		self.chk_show_reference_clips.setChecked(True)
		self.chk_show_reference_clips.stateChanged.connect(self.filter_changed)

		self.layout().addWidget(self.chk_show_user_placed)
		self.layout().addWidget(self.chk_show_reference_clips)
	
	@QtCore.Slot()
	def filter_changed(self):
		self.filters_changed.emit(self.chk_show_user_placed.isChecked(), self.chk_show_reference_clips.isChecked())


class BinItemDisplayDelegate(QtWidgets.QStyledItemDelegate):

	max_8b = (1 << 8) - 1
	max_16b = (1 << 16) - 1
	padding_px = 5 # Pixels padding

	def paint(self, painter:QtGui.QPainter, option:QtWidgets.QStyleOptionViewItem, index:QtCore.QModelIndex|QtCore.QPersistentModelIndex) -> None:

		super().paint(painter, option, index)

		header = index.model().headerData(index.column(), QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.UserRole)
		
		
		if header["type"] == 51: #color

		
			mob = index.data(role=QtCore.Qt.ItemDataRole.UserRole)

			# Set box location
			color_box = QtCore.QRect(0,0, option.rect.height()-self.padding_px, option.rect.height()-self.padding_px)
			color_box.moveCenter(option.rect.center())
			
			# Set outline and fill
			pen = QtGui.QPen(QtGui.QColorConstants.Black)
			brush = QtGui.QBrush()
			#painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

			# Use clip color if available
			clip_color_attr = avbutils.composition_clip_color(mob)
			if clip_color_attr is None:
				brush.setStyle(QtCore.Qt.BrushStyle.NoBrush)
			else:
				clip_color = QtGui.QColor(*(c/self.max_16b * self.max_8b for c in clip_color_attr ))
				brush.setColor(clip_color)
				brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
			
			painter.setBrush(brush)
			painter.setPen(pen)
			painter.drawRect(color_box)

			# Box Shadow (TODO: 128 opactiy not working)
			color_box.moveCenter(color_box.center()+QtCore.QPoint(1,1))
			#color_box.setWidth(color_box.width() + 2)

			pen.setColor(QtGui.QColor(0,0,0,64))
			brush.setStyle(QtCore.Qt.BrushStyle.NoBrush)
			painter.setPen(pen)
			painter.setBrush(brush)
			painter.drawRect(color_box)
		
class BinModelProxy(QtCore.QSortFilterProxyModel):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.show_user_placed = True
		self.show_reference_clips = True

	def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex) -> bool:
		
		list_item = self.sourceModel().index(source_row, 0, source_parent)
		bin_item = list_item.data(QtCore.Qt.ItemDataRole.UserRole)

		if bin_item.is_user_placed:
			return self.show_user_placed
		else:
			return self.show_reference_clips
	
	def filterAcceptsColumn(self, source_column: int, source_parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex) -> bool:
		
		header = self.sourceModel().headerData(source_column, orientation=QtCore.Qt.Orientation.Horizontal, role=QtCore.Qt.ItemDataRole.UserRole)
		return not header["hidden"]

	
	@QtCore.Slot()
	def filters_changed(self, show_user_placed:bool, show_reference_clips:bool):

		self.show_user_placed = show_user_placed
		self.show_reference_clips = show_reference_clips
		
		self.invalidateFilter()

		
class BinModelItem(QtCore.QObject):
	"""Bin items as objects provided by `BinModel`"""

	def __init__(self, bin_item:avb.bin.BinItem, *args, **kwargs):
		"""Create a bin model item for a given pyavb BinItem"""

		super().__init__(*args, **kwargs)

		self._item = bin_item
		self._mob  = bin_item.mob
		self._attributes = bin_item.mob.attributes

		#print(self.is_user_placed)
	
	@property
	def item(self) -> avb.bin.BinItem:
		return self._item
	
	@property
	def mob(self) -> avb.trackgroups.Composition:
		return self._mob
	
	@property
	def attributes(self) -> avb.attributes.Attributes:
		return self._attributes
	
	@property
	def is_user_placed(self) -> bool:
		return self._item.user_placed


class BinModel(QtCore.QAbstractItemModel):
	"""An Avid bin!"""

	def __init__(self, bin:avb.bin.Bin|None=None, *args, **kwargs):

		super().__init__(*args, **kwargs)

		if bin is None:
			bin = avb.file.AVBFile().content
		
		self.setBin(bin)
	
	def setBin(self, bin:avb.bin.Bin):
		self._bin = bin
		self._update_cache()
	
	def _update_cache(self):
		"""Update the item cache"""
		self._item_cache = [BinModelItem(x) for x in self._bin.items]
		
		self._header_cache = []
		for header in self._bin.view_setting.columns:
			self._header_cache.append({x:y for x,y in header.items()})
		
		self.modelReset.emit()

	def index(self, row:int, column:int, parent:typing.Optional[QtCore.QModelIndex]=None) -> QtCore.QModelIndex:
		"""Returns the index of the item in the model specified by the given row, column and parent index."""

		if not isinstance(parent, QtCore.QModelIndex) or not parent.isValid():
			return self.createIndex(row, column, self._item_cache[row])
		
		else:
			return QtCore.QModelIndex()
	
	def parent(self, child:QtCore.QModelIndex) -> QtCore.QModelIndex:
		"""Returns the parent of the model item with the given index. If the item has no parent, an invalid QModelIndex is returned."""
		
		# NOTE: For now, single-level model, so parent should just point to an invalid index
		return QtCore.QModelIndex()

	def rowCount(self, parent:typing.Optional[QtCore.QModelIndex]=None) -> int:
		"""Returns the number of rows under the given parent. When the parent is valid it means that is returning the number of children of parent."""

		if not isinstance(parent, QtCore.QModelIndex) or not parent.isValid():
			return len(self._item_cache)
		
		return 0
	
	def columnCount(self, parent:typing.Optional[QtCore.QModelIndex]=None) -> int:
		"""Returns the number of columns for the children of the given parent."""

		# NOTE: For now, based on the active BinViewSetting in the file to get us started
		if isinstance(parent, QtCore.QModelIndex) and parent.isValid():
			return 0
		return len(self._bin.view_setting.columns)
		

	def data(self, index:QtCore.QModelIndex, role:typing.Optional[QtCore.Qt.ItemDataRole]=QtCore.Qt.ItemDataRole.DisplayRole) -> typing.Any:
		"""Returns the data stored under the given role for the item referred to by the index."""

		if not isinstance(index, QtCore.QModelIndex) or not index.isValid():
			return None
		
		mob = index.internalPointer().mob

		if role == QtCore.Qt.ItemDataRole.DisplayRole:
			header_data = self.headerData(index.column(),QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.UserRole)
			if header_data.get("type") == 4:
				return str(timecode.Timecode(mob.length)).lstrip("00:")
			elif header_data.get("type") == 3:
				try:
					return str(avbutils.get_timecode_range_for_composition(mob).end)
				except:
					return "-"
			elif header_data.get("type") == 2:
				try:
					return str(avbutils.get_timecode_range_for_composition(mob).start)
				except:
					return "-"
			elif header_data.get("type") == 201:
				return f"{mob.name} [{avbutils.MobTypes.from_composition(mob)} / {avbutils.MobUsage.from_composition(mob)}]"
			elif header_data.get("type") in range(40,50):
				if "_USER" in mob.attributes:
					return mob.attributes.get("_USER").get(header_data.get("title"),"-")
			elif "PreservedBinData" in mob.attributes:
				if header_data.get("title") in mob.attributes["PreservedBinData"]:
					return mob.attributes["PreservedBinData"][header_data.get("title")]
				elif f"_COLUMN_{header_data.get('title').upper().replace(' ','_')}" in  mob.attributes["PreservedBinData"]:
					col = mob.attributes["PreservedBinData"][f"_COLUMN_{header_data.get('title').upper().replace(' ','_')}"].decode("latin-1")
					return col
				else:
					pass
		
		elif role == QtCore.Qt.ItemDataRole.UserRole:
			return index.internalPointer()

		return None
		

	def headerData(self, section:int, orientation:QtCore.Qt.Orientation, role:typing.Optional[int]=QtCore.Qt.DisplayRole) -> typing.Any:
		"""Returns the data for the given role and section in the header with the specified orientation."""
		
		if role == QtCore.Qt.DisplayRole:
			return self._header_cache[section].get("title") + " (" + str(self._header_cache[section].get("type")) + ")"
		elif role == QtCore.Qt.UserRole:
			return self._header_cache[section]

def show_details(selected:QtCore.QItemSelection, deselected:QtCore.QItemSelection):

	global txt

	try:
		idx = selected.data().indexes()[0]
	except:
		#print("Empty selection")
		return False
	
	mob = idx.model().data(idx, QtCore.Qt.ItemDataRole.UserRole)
	#pprint.pprint(mob.attributes)

	txt.setPlainText(pprint.pformat(mob.attributes))

def get_changes(prx_model:BinModelProxy, status_bar:QtWidgets.QStatusBar):
	
	num_visible = prx_model.rowCount()
	num_total = prx_model.sourceModel().rowCount()
	status_bar.showMessage(f"{num_visible} Visible | {num_total-num_visible} Hidden | {num_total} Total")


if __name__ == "__main__":

	app = QtWidgets.QApplication()
	app.setApplicationName("Lil' Binboy")

	wnd_main = QtWidgets.QMainWindow()

	splitter = QtWidgets.QSplitter()

	tree = QtWidgets.QTreeView()
	tree.setAlternatingRowColors(True)
	tree.setIndentation(0)

	txt = QtWidgets.QPlainTextEdit()
	txt.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
	txt.setEnabled(False)

	filter_controls = FilterControls()

	sidebar = QtWidgets.QWidget()
	sidebar.setLayout(QtWidgets.QVBoxLayout())

	sidebar.layout().addWidget(txt)
	sidebar.layout().addWidget(filter_controls)

	splitter.addWidget(tree)
	splitter.addWidget(sidebar)

	wnd_main.setStatusBar(QtWidgets.QStatusBar())
	wnd_main.setCentralWidget(splitter)

	wnd_main.show()

	with avb.open(sys.argv[1]) as file_bin:
		wnd_main.setWindowFilePath(sys.argv[1])

		prx = BinModelProxy()
		prx.setSourceModel(BinModel(file_bin.content))
		tree.setModel(prx)

		filter_controls.filters_changed.connect(prx.filters_changed)
		filter_controls.filters_changed.connect(lambda: get_changes(prx, wnd_main.statusBar()))


		tree.selectionModel().selectionChanged.connect(show_details)
		tree.setItemDelegateForColumn(0, BinItemDisplayDelegate())
		tree.setSortingEnabled(True)

		for col in range(tree.model().columnCount()):
			header_data = tree.model().headerData(col, QtCore.Qt.Orientation.Horizontal, role=QtCore.Qt.UserRole)
			tree.setColumnHidden(col, header_data.get("hidden", False))

		


		app.exec()