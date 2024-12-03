import sys
import avb, avbutils
from PySide6 import QtCore, QtGui, QtWidgets

class MarkerViewer(QtWidgets.QWidget):

	def __init__(self):
		super().__init__()

		self.setLayout(QtWidgets.QVBoxLayout())

		self.cmb_timelines   = QtWidgets.QComboBox()
		self.view_markerlist = QtWidgets.QTreeView()

		self.layout().addWidget(self.cmb_timelines)
		self.layout().addWidget(self.view_markerlist)

class MarkerViewItem(QtCore.QObject):
	"""Marker view object for view model"""

	HEADERS = [
		"Timeline",
		"Color",
		"Timecode",
		"Track",
		"User",
		"Comment",
	]

class MarkerViewModel(QtCore.QAbstractItemModel):
	"""Marker view model"""

	def __init__(self):
		super().__init__()

		self._marker_data:list[MarkerViewItem]

	def columnCount(self, parent:QtCore.QModelIndex) -> int:
		if parent.isValid():
			return 0
		return len(MarkerViewItem.HEADERS)
	
	def rowCount(self, parent:QtCore.QModelIndex) -> int:
		if parent.isValid():
			return 0
		return len(self._marker_data)
	
	def parent(self, index:QtCore.QModelIndex) -> QtCore.QModelIndex:
		return QtCore.QModelIndex()
	
	def headerData(self, section:int, orientation:QtCore.Qt.Orientation, role:QtCore.Qt.ItemDataRole):
		if orientation is QtCore.Qt.Orientation.Horizontal:
			return None
		
		if role is QtCore.Qt.ItemDataRole.DisplayRole:
			return MarkerViewItem.HEADERS[section]
	
	def data(self, index:QtCore.QModelIndex):
		"""TODO"""


class AppController(QtCore.QObject):
	"""Application controller"""

	def __init__(self, initial_bin_path:str|None=None):
		super().__init__()

		self._viewmodel = MarkerViewModel()
		self._bin_path:str = None

		self._wnd_main = MarkerViewer()

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

		with avb.open(self._bin_path) as bin_handle:
			pass
	

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
	def _create_marker_icon(cls, color:avbutils.MarkerColors):

		marker_pixmap = QtGui.QPixmap(32,32)
		marker_pixmap.fill(QtGui.QColor(0,0,0,0))

		marker_painter = QtGui.QPainter(marker_pixmap)
		marker_painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
		
		brush = QtGui.QBrush(QtGui.QColor.fromString(color.value))
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

def load_markers_from_bin(bin_path:str, tree:QtWidgets.QTreeWidget):
	
	with avb.open(bin_path) as bin_handle:
		timelines = avbutils.get_timelines_from_bin(bin_handle.content)
		
		try:
			timeline = next(timelines)
		except StopIteration:
			raise ValueError(f"No timelines found in {bin_path}")

		tree.parent().setWindowFilePath(bin_path)
		tree.parent().setWindowTitle("Marker List - " + timeline.name)

		tc_timeline = avbutils.get_timecode_range_for_composition(timeline)

		for marker in avbutils.get_markers_from_timeline(timeline):
			print(marker)
			marker_item = QtWidgets.QTreeWidgetItem([
				marker.color.value,
				str(tc_timeline.start + marker.frm_offset),
				"",
				marker.user,
				marker.comment
			])
			marker_item.setIcon(0, MarkerIcons.get_marker_icon(marker.color))
			tree.addTopLevelItem(marker_item)
		
		[tree_markerlist.resizeColumnToContents(c) for c in range(tree_markerlist.columnCount())]

if __name__ == "__main__":

	app = QtWidgets.QApplication(sys.argv)

	app_controller = AppController()

	sys.exit(app.exec())