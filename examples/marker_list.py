import sys
import avb, avbutils
from PySide6 import QtCore, QtGui, QtWidgets

class MarkerViewer(QtWidgets.QWidget):

	def __init__(self):
		super().__init__()

		self.setLayout(QtWidgets.QVBoxLayout())

		self.cmb_timelines   = QtWidgets.QComboBox()
		self.view_markerlist = QtWidgets.QTreeView()
		self.view_markerlist.setSortingEnabled(True)
		self.view_markerlist.setUniformRowHeights(True)
		self.view_markerlist.setAlternatingRowColors(True)
		self.view_markerlist.setIndentation(0)

		self.layout().addWidget(self.cmb_timelines)
		self.layout().addWidget(self.view_markerlist)

class MarkerViewItem(QtCore.QObject):
	"""Marker view object for view model"""

	HEADERS = [
		"Timeline",
		"Timeline Start",
		"Color",
		"Timecode",
		"Track",
		"Date Created",
		"Date Modified",
		"User",
		"Comment",
	]

	def __init__(self, data:dict):
		super().__init__()
		self._data = {}
		for header in self.HEADERS:
			self._data.update(
				{header: data.get(header) or ""}
			)
	
	def data(self, column:str, role:QtCore.Qt.ItemDataRole):

		if column == "Color" and role == QtCore.Qt.ItemDataRole.DecorationRole:
			return MarkerIcons.get_marker_icon(self._data.get("Color"))

		if role == QtCore.Qt.ItemDataRole.DisplayRole:
			return self._data.get(column,"?")
		else:
			return None

class MarkerViewProxy(QtCore.QSortFilterProxyModel):

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)
		self._filter:str = None
		self._hidden_columns = []
	
	def filterAcceptsRow(self, source_row, parent:QtCore.QModelIndex):
		if not self._filter:
			return True
		
		val = self.sourceModel().data(self.sourceModel().index(source_row, 0, parent), QtCore.Qt.ItemDataRole.DisplayRole)
		return val == self._filter
	
	def filterAcceptsColumn(self, source_column, parent:QtCore.QModelIndex):
		col = MarkerViewItem.HEADERS[source_column]

		return col not in self._hidden_columns
	
	@QtCore.Slot(str)
	def setFilter(self, filter:str):
		self._filter = filter
		self.invalidateRowsFilter()

	def setHiddenColumns(self, columns:list[str]):
		self._hidden_columns = columns
		self.invalidateColumnsFilter()

class MarkerViewModel(QtCore.QAbstractItemModel):
	"""Marker view model"""

	def __init__(self):
		super().__init__()

		self._marker_data:list[MarkerViewItem] = []

	def columnCount(self, parent:QtCore.QModelIndex) -> int:
		return len(MarkerViewItem.HEADERS)
	
	def rowCount(self, parent:QtCore.QModelIndex) -> int:
		if parent.isValid():
			return 0
		return len(self._marker_data)
	
	def parent(self, index:QtCore.QModelIndex) -> QtCore.QModelIndex:
		return QtCore.QModelIndex()
	
	def headerData(self, section:int, orientation:QtCore.Qt.Orientation, role:QtCore.Qt.ItemDataRole):
		if orientation == QtCore.Qt.Orientation.Vertical:
			return None
		
		if role == QtCore.Qt.ItemDataRole.DisplayRole:
			return MarkerViewItem.HEADERS[section]
		
	def index(self, row:int, col:int, parent:QtCore.QModelIndex) -> QtCore.QModelIndex:
		return self.createIndex(row, col, None)
	
	def data(self, index:QtCore.QModelIndex, role:QtCore.Qt.ItemDataRole):
		"""TODO"""

		if not index.isValid():
			return None\
		
		row = index.row()
		col = MarkerViewItem.HEADERS[index.column()]

		return self._marker_data[row].data(col, role)
	
	def addMarker(self, marker:MarkerViewItem):
		"""Add a marker to the list"""
		self.beginInsertRows(QtCore.QModelIndex(), 0,0)
		self._marker_data.insert(0,marker)
		self.endInsertRows()

class TimelineProxyModel(QtCore.QSortFilterProxyModel):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self._shown = set()

	def filterAcceptsRow(self, source_row:int, parent:QtCore.QModelIndex):
		if parent.isValid():
			return False
		
		val = self.sourceModel().data(self.sourceModel().index(source_row, 0, parent), QtCore.Qt.ItemDataRole.DisplayRole)

		if val not in self._shown:
			self._shown.add(val)
			return True
		
		return False



class AppController(QtCore.QObject):
	"""Application controller"""

	def __init__(self, initial_bin_path:str|None=None):
		super().__init__()

		self._viewmodel = MarkerViewModel()
		self._bin_path:str = None

		self._wnd_main = MarkerViewer()
		self._wnd_main.setMinimumWidth(500)

		self._wnd_main.cmb_timelines.setModel(TimelineProxyModel())
		self._wnd_main.cmb_timelines.model().setSourceModel(self._viewmodel)
		self._wnd_main.view_markerlist.setModel(MarkerViewProxy())
		self._wnd_main.view_markerlist.model().setSourceModel(self._viewmodel)

		self._wnd_main.cmb_timelines.currentTextChanged.connect(self._wnd_main.view_markerlist.model().setFilter)
		self._wnd_main.view_markerlist.model().setHiddenColumns(["Timeline", "Timeline Start"])

		if not initial_bin_path or not QtCore.QFileInfo(initial_bin_path).isFile():
			self.promptForBin()
		else:
			self.setCurrentBin(initial_bin_path)

		self._wnd_main.show()
	
	def promptForBin(self):
		"""Prompt the user for a bin"""
		bin_path, _ = QtWidgets.QFileDialog.getOpenFileName(self._wnd_main, "Choose An Avid Bin...", self._bin_path, "Avid Bins (*.avb);;All Files (*)")
		if bin_path:
			self.setCurrentBin(bin_path)


	def setCurrentBin(self, bin_path:str):
		"""Set the current Avid bin"""
		self._bin_path = bin_path

		self.loadBin()
	
	def loadBin(self):
		has_timelines:bool = False
		with avb.open(self._bin_path) as bin_handle:
			for timeline in avbutils.get_timelines_from_bin(bin_handle.content):
				has_timelines = True
				timeline_name = timeline.name
				timeline_tc_range = avbutils.get_timecode_range_for_composition(timeline)
				for marker_info in avbutils.get_markers_from_timeline(timeline):
					self._viewmodel.addMarker(MarkerViewItem(data={
						"Timeline": timeline_name,
						"Timeline Start": str(timeline_tc_range.start),
						"Track": marker_info.track_label,
						"Color": marker_info.color.value,
						"Timecode": str(timeline_tc_range.start + marker_info.frm_offset),
						"Date Created": str(marker_info.date_created),
						"Date Modified": str(marker_info.date_modified),
						"User": marker_info.user,
						"Comment": marker_info.comment,
					}))
		if not has_timelines:
			QtWidgets.QMessageBox.critical(self._wnd_main, "No Timelines In Bin", "No timelines were found in this bin.\nThis marker list utility is currently designed for timelines only.")
		
		else:
			self._wnd_main.setWindowFilePath(self._bin_path)
			for col in range(self._wnd_main.view_markerlist.model().columnCount()):
				self._wnd_main.view_markerlist.resizeColumnToContents(col)

	

class MarkerIcons:

	ICON_MARGIN:int = 6
	ICONS:dict[avbutils.MarkerColors,QtGui.QIcon] = {}

	@classmethod
	def get_marker_icon(cls, color:avbutils.MarkerColors) -> QtGui.QIcon:
		
		if color not in cls.ICONS:
			print("Creating marker icon for ", color)
			cls._create_marker_icon(color)

		return cls.ICONS[color]
	
	@classmethod
	def _create_marker_icon(cls, color:str):

		marker_pixmap = QtGui.QPixmap(32,32)
		marker_pixmap.fill(QtGui.QColor(0,0,0,0))

		marker_painter = QtGui.QPainter(marker_pixmap)
		marker_painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
		
		brush = QtGui.QBrush(QtGui.QColor.fromString(color))
		brush.setStyle(QtGui.Qt.BrushStyle.SolidPattern)

		pen = QtGui.QPen(brush.color().darker(300))
		pen.setWidth(1)

		marker_painter.setBrush(brush)
		marker_painter.setPen(pen)
		marker_painter.drawEllipse(marker_pixmap.rect().adjusted(cls.ICON_MARGIN*1.5, cls.ICON_MARGIN, -cls.ICON_MARGIN*1.5, -cls.ICON_MARGIN))
		marker_painter.end()

		#marker_pixmap.fill(QtGui.QColor.fromString(color.value))
		
		marker_icon = QtGui.QIcon(marker_pixmap)
		cls.ICONS[color] = marker_icon

if __name__ == "__main__":

	app = QtWidgets.QApplication(sys.argv)
	app.setApplicationDisplayName("Mister Marker Lister")

	bin_path = sys.argv[1] if len(sys.argv) > 1 else ""
	app_controller = AppController(bin_path)

	sys.exit(app.exec())