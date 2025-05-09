import sys, avb
import avbutils, timecode, dataclasses, enum
from datetime import datetime, date, time

_marker_colors = {
	"RED"     : "Red",
	"GREEN"   : "Green",
	"BLUE"    : "Blue",
	"CYAN"    : "Cyan",
	"MAGENTA" : "Magenta",
	"YELLOW"  : "Yellow",
	"BLACK"   : "Black",
	"WHITE"   : "White",
}

_marker_colors_extended = {
	**_marker_colors,
	"PINK"   : "Pink",
	"FOREST" : "Forest",
	"DENIM"  : "Denim",
	"VIOLET" : "Violet",
	"PURPLE" : "Purple",
	"ORANGE" : "Orange",
	"GREY"   : "Grey",
	"GOLD"   : "Gold",
}

# NOTE: I... I guess I thought I could inherit the `MarkerColors` enum 
# to make `MarkerColorsExtended`.  But I cannot.  So I hate all of this.

MarkerColors = enum.Enum("MarkerColors", _marker_colors)
"""Standard Avid marker colors"""

MarkerColorsExtended = enum.Enum("ExtendedMarkerColors", _marker_colors_extended)
"""Additional marker colors available with Avid 2024.6"""

@dataclasses.dataclass()
class MarkerInfo:
	"""Avid marker info"""

	# TODO: Investigate spanned markers at some point

	frm_offset:int
	"""Marker offset from start (in frames)"""

	track_label:str
	"""Track label this marker belongs to"""

	user:str
	"""Marker creator"""

	comment:str
	"""Marker comment"""

	color:MarkerColors
	"""Marker color"""

	date_created:datetime
	"""Date the marker was first created"""

	date_modified:datetime
	"""Date the marker was last modified"""

	@classmethod
	def from_avb_marker(cls, offset:int, track_label:str, marker:avb.misc.Marker) -> "MarkerInfo":
		return cls(
			frm_offset = offset,
			track_label = track_label,
			user = marker.attributes.get("_ATN_CRM_USER",""),
			comment = marker.attributes.get("_ATN_CRM_COM",""),
			color = MarkerColors(marker.attributes.get("_ATN_CRM_COLOR","Red")),
			date_created = cls.get_creation_datetime_from_attributes(marker.attributes),
			date_modified = datetime.fromtimestamp(marker.attributes.get("_ATN_CRM_LONG_MOD_DATE",0))
		)
	
	@staticmethod
	def get_creation_datetime_from_attributes(marker_attributes:avb.attributes.Attributes) -> datetime:
		"""Get the marker creation datetime from whatever's there"""

		# NOTE: Prefer _ATN_CRM_LONG_CREATE_DATE, but that's not always present
		if "_ATN_CRM_LONG_CREATE_DATE" in marker_attributes:
			return datetime.fromtimestamp(marker_attributes["_ATN_CRM_LONG_CREATE_DATE"])
		
		elif "_ATN_CRM_DATE" in marker_attributes and "_ATN_CRM_TIME" in marker_attributes:
			m,d,y = (int(x) for x in str(marker_attributes["_ATN_CRM_DATE"]).split("/"))
			hh,mm = (int(x) for x in str(marker_attributes["_ATN_CRM_TIME"]).split(":"))
			return datetime.combine(date(year=int(y), month=int(m), day=int(d)), time(hour=int(hh), minute=int(mm)))
		else:
			return datetime.fromtimestamp(0)

# CREDIT! get_markers_from_track() and get_component_markers() were "borrowed" and adapted from pyavb's "dump markers" example

def get_markers_from_timeline(timeline:avb.trackgroups.Composition) -> list[MarkerInfo]:
	markers = []
	for track in timeline.tracks:
		markers.extend(get_markers_from_track(track))
	return markers

def get_markers_from_track(track:avb.trackgroups.Track, start:int=0):
	
	components = get_components_from_track_component(track.component)

	pos = start
	marker_list = []
	for item in components:

		if isinstance(item, avb.trackgroups.TransitionEffect):
			pos -= item.length

		markers = get_component_markers(item)

		for marker in markers:
			marker_list.append(MarkerInfo.from_avb_marker(offset=pos + marker.comp_offset, track_label=avbutils.format_track_label(track), marker=marker))
		if not isinstance(item, avb.trackgroups.TransitionEffect):
			pos += item.length

	return marker_list

def get_components_from_track_component(track_component:avb.components.Component) -> list[avb.components.Component]:

	# Most of the "main" tracks (V1, A1, etc) reference a Sequence component
	if isinstance(track_component, avb.components.Sequence):
		return track_component.components

	# Audio tracks with RTAS effects are TrackGroups though
	# The sub-tracks in this trackgroup consist of the usual Sequence as well as TrackEffects
	# RTAS is the only time I've encountered this but I'll bet ya there are others
	elif isinstance(track_component, avb.trackgroups.TrackGroup):
		components = []
		for sub_track in track_component.tracks:
			if "component" not in sub_track.property_data:
				continue
			components.extend(get_components_from_track_component(sub_track.component))
		return components

	# Typically Timecode, Edgecode... I would imagine DescriptiveMetadata
	else:
		return [track_component]

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