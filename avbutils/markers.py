import sys, avb
import avbutils, timecode, dataclasses, enum
from datetime import datetime

class MarkerColor(enum.Enum):
	"""Valid Avid marker colors"""
	RED = "Red"
	GREEN = "Green"
	BLUE = "Blue"
	CYAN = "Cyan"
	MAGENTA = "Magenta"
	YELLOW = "Yellow"
	BLACK = "Black"
	WHITE = "White"

@dataclasses.dataclass()
class MarkerInfo:
	"""Avid marker info"""

	# TODO: Investigate spanned markers at some point

	frm_offset:int
	user:str
	comment:str
	color:MarkerColor
	date_created:datetime
	date_modified:datetime

	@classmethod
	def from_avb_marker(cls, offset:int, marker:avb.misc.Marker) -> "MarkerInfo":
		return cls(
			frm_offset = offset,
			user = marker.attributes.get("_ATN_CRM_USER",""),
			comment = marker.attributes.get("_ATN_CRM_COM",""),
			color = MarkerColor(marker.attributes.get("_ATN_CRM_COLOR")),
			date_created = datetime.fromtimestamp(marker.attributes.get("_ATN_CRM_LONG_CREATE_DATE")),
			date_modified = datetime.fromtimestamp(marker.attributes.get("_ATN_CRM_LONG_MOD_DATE"))
		)


# CREDIT! get_markers_from_track() and get_component_markers() were "borrowed" and adapted from pyavb's "dump markers" example

def get_markers_from_track(track:avb.trackgroups.Track, start:int=0):
	components = []
	if isinstance(track.component, avb.components.Sequence):
		components = track.component.components
	else:
		components = [track.component]

	pos = start
	marker_list = []
	for item in components:

		if isinstance(item, avb.trackgroups.TransitionEffect):
			pos -= item.length

		markers = get_component_markers(item)

		for marker in markers:
			marker_list.append(MarkerInfo.from_avb_marker(offset=pos + marker.comp_offset, marker=marker))
		if not isinstance(item, avb.trackgroups.TransitionEffect):
			pos += item.length

	return marker_list

def get_component_markers(c):
	if 'attributes' not in c.property_data:
		return []

	attributes = c.attributes or {}
	markers = attributes.get('_TMP_CRM',  [])
	if isinstance(c, avb.components.Sequence):
		for item in c.components:
			more_markers = get_component_markers(item)
			markers.extend(more_markers)

	elif isinstance(c, avb.trackgroups.TrackGroup):
		for track in c.tracks:
			if 'component' not in track.property_data:
				continue

			more_markers = get_component_markers(track.component)
			markers.extend(more_markers)

	return markers