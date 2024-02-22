import typing, sys, pprint
import avb, avbutils, timecode
from PySide6 import QtCore, QtWidgets, QtGui

class BinItemDisplayDelegate(QtWidgets.QStyledItemDelegate):

	max_8b = (1 << 8) - 1
	max_16b = (1 << 16) - 1

	def paint(self, painter:QtGui.QPainter, option:QtWidgets.QStyleOptionViewItem, index:QtCore.QModelIndex|QtCore.QPersistentModelIndex) -> None:

		super().paint(painter, option, index)
		
		mob = index.data(role=QtCore.Qt.ItemDataRole.UserRole)

		if avbutils.composition_clip_color(mob) is not None:
			
			clip_color = QtGui.QColor(*(c/self.max_16b * self.max_8b for c in avbutils.composition_clip_color(mob)))
			color_box = QtCore.QRect((option.rect.width()/2) - (option.rect.height()*(16/9)/2), option.rect.top(), option.rect.height()*(16/9), option.rect.height())


			
			brush = QtGui.QBrush()
			brush.setColor(clip_color)
			brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)

			painter.fillRect(color_box, brush)
			brush.setColor(QtGui.QColorConstants.Black)
			brush.setStyle(QtCore.Qt.BrushStyle.NoBrush)
			painter.drawRect(color_box)
			return


class BinModel(QtCore.QAbstractItemModel):
	"""An Avid bin!"""

	def __init__(self, bin:avb.bin.Bin, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self._bin = bin
		self._item_cache = []
		self._header_cache = []

		self._update_cache()
	
	def _update_cache(self):
		"""Update the item cache"""
		self._item_cache = [x for x in self._bin.items]
		
		for header in self._bin.view_setting.columns:
			self._header_cache.append({x:y for x,y in header.items()})
		#self.dataChanged.emit()

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
			elif header_data.get("type") == 201:
				return f"{mob.name} [{avbutils.MobTypes.from_composition(mob)} / {avbutils.MobUsage.from_composition(mob)}]"
			elif header_data.get("type") in range(40,50):
				if "_USER" in mob.attributes:
					return mob.attributes.get("_USER").get(header_data.get("title"),"-")
			elif "PreservedBinData" in mob.attributes:
				if header_data.get("title") in mob.attributes["PreservedBinData"]:
					return mob.attributes["PreservedBinData"][header_data.get("title")]
				elif f"_COLUMN_{header_data.get('title').upper().replace(' ','_')}" in  mob.attributes["PreservedBinData"]:
					col = mob.attributes["PreservedBinData"][f"_COLUMN_{header_data.get('title').upper().replace(' ','_')}"].decode("utf-8")
					print(f"_COLUMN_{header_data.get('title').upper().replace(' ','_')} IS ", str(col) )
					return col
				else:
					print(f"_COLUMN_{header_data.get('title').upper().replace(' ','_')}")
		
		elif role == QtCore.Qt.ItemDataRole.UserRole:
			return mob

		return None
		

	def headerData(self, section:int, orientation:QtCore.Qt.Orientation, role:typing.Optional[int]=QtCore.Qt.DisplayRole) -> typing.Any:
		"""Returns the data for the given role and section in the header with the specified orientation."""
		
		if role == QtCore.Qt.DisplayRole:
			return self._header_cache[section].get("title") + " (" + str(self._header_cache[section].get("type")) + ")"
		elif role == QtCore.Qt.UserRole:
			return self._header_cache[section]

def show_details(selected:QtCore.QItemSelection, deselected:QtCore.QItemSelection):
	try:
		idx = selected.data().indexes()[0]
	except:
		print("Empty selection")
		return False
	
	mob = idx.model().data(idx, QtCore.Qt.ItemDataRole.UserRole)
	#pprint.pprint(mob.attributes)

	pprint.pprint(mob.attributes)
	


if __name__ == "__main__":

	app = QtWidgets.QApplication()
	wdg = QtWidgets.QTreeView()
	wdg.setAlternatingRowColors(True)
	wdg.setIndentation(0)

	with avb.open(sys.argv[1]) as file_bin:
		wdg.setWindowTitle(sys.argv[1])

		prx = QtCore.QSortFilterProxyModel()
		prx.setSourceModel(BinModel(file_bin.content))
		wdg.setModel(prx)

		wdg.selectionModel().selectionChanged.connect(show_details)
		wdg.setItemDelegateForColumn(0, BinItemDisplayDelegate())
		wdg.setSortingEnabled(True)

		for col in range(wdg.model().columnCount()):
			header_data = wdg.model().headerData(col, QtCore.Qt.Orientation.Horizontal, role=QtCore.Qt.UserRole)
			wdg.setColumnHidden(col, header_data.get("hidden", False))
		wdg.show()
		app.exec()