import sys
import avb, avbutils
from PySide6 import QtCore, QtGui, QtWidgets

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

	wnd_main = QtWidgets.QWidget()

	wnd_main.setLayout(QtWidgets.QVBoxLayout())
	wnd_main.setWindowTitle("Marker List")
	wnd_main.setMinimumWidth(600)

	tree_markerlist = QtWidgets.QTreeWidget()
	tree_markerlist.setHeaderLabels([
		"Color",
		"Timecode",
		"Track",
		"Author",
		"Comment"
	])
	tree_markerlist.setAlternatingRowColors(True)
	tree_markerlist.setSortingEnabled(True)
	tree_markerlist.setUniformRowHeights(True)
	tree_markerlist.setIndentation(0)
	wnd_main.layout().addWidget(tree_markerlist)

	wnd_main.show()

	if len(sys.argv) > 1:
		markers = load_markers_from_bin(sys.argv[1], tree_markerlist)
		print(markers)

	sys.exit(app.exec())