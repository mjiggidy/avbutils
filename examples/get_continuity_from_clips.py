import sys, pathlib, dataclasses, re, warnings
import avb, avbutils, numbers_parser
from timecode import Timecode, TimecodeRange

USAGE = f"Usage: {__file__} path/to/bins"

pat_reelname = re.compile(r"FH REEL (?P<reel_number>\d+) v(?P<reel_version>[\d\.]+)", re.I)
pat_sequential = re.compile(r"(?P<base>.*)(?P<digits>\d+)")

@dataclasses.dataclass
class ContinuitySceneInfo:
	"""Continuity info for an individual scene"""

	scene_number:str
	"""The scene numbeer (eg `Sc 032`)"""

	duration:Timecode
	"""Duration of the scene"""

	description:str
	"""Description of the scene"""

	location:str
	"""Location in which the scene takes place"""

	time_of_day:str

@dataclasses.dataclass
class ReelInfo:
	"""Continuity info per reel"""

	reel_name:str
	"""Source timeline name.  Ex: FH REEL 6 v15.3.2 - Continuity"""

	reel_number:int
	"""Example: 6"""

	reel_version:str
	"""No 'v'.  Example: 15.3.2"""

	reel_timecode_range:TimecodeRange
	"""The start/end Timecode range of this timeline"""

	scenes:list[ContinuitySceneInfo]
	"""The continuity info per scene in this reel"""

	@property
	def reel_trt(self) -> Timecode:
		"""The TRT of this reel, based on total scene durations"""

		return sum(scene.duration for scene in self.scenes)
	
	@property
	def reel_name_short(self) -> str:
		return f"R{self.reel_number} v{self.reel_version}"


def timecode_as_duration(timecode:Timecode) -> str:
	"""Format the timecode as a string without leading zeroes"""

	return "-" if timecode.is_negative else "" + str(timecode).lstrip("0:")

def is_continuity_sequence(comp:avb.trackgroups.Composition) -> bool:
	"""Determine if we're interested in this or not"""

	return comp.name.lower().endswith("continuity")

def is_intended_for_continuity(comp:avb.components.Component) -> bool:
	"""Determine if this continuity clip is meant to be included or not (so we can exclude things like head/tail leaders)"""

	# Look for text in bin column "Ignore In List"
	return not bool(comp.attributes.get("_USER").get("Ignore In List", "").strip())

def get_continuity_tracks_from_timeline(sequence:avb.trackgroups.Composition) -> list[avb.trackgroups.Track]:
	"""Choose the appropriate track in which the continuity clips reside"""

	# Looking for a video track (media_kind="picture") with the custom name "Continuity" (track.attributes.get("_COMMENT") == "Continuity")
	return [t for t in sequence.tracks if t.media_kind == "picture" and hasattr(t,"attributes") and t.attributes.get("_COMMENT","").lower() == "continuity"]

	# ALT: Return top-most video track
	return sorted([t for t in sequence.tracks if t.media_kind == "picture"], key=lambda t: t.index)[-1]

def get_continuity_subclips_from_sequence(sequence:avb.components.Sequence) -> list[avb.components.Component]:
	"""Return a list of subclips (assumed to be Continuity Clips) in the given sequence"""

	# A sequence begins and ends with a zero-length `avb.components.Filler`, so trim those babies off
	# TODO: Additional validation/filtering?
	# NOTE: sequence.components[1:-1]  ...uhhh... doesn't work
	return list(sequence.components)[1:-1]


def print_timeline_pretty(timeline:avb.trackgroups.Composition, continuity_scenes:list[ContinuitySceneInfo]):
	""""Pretty-print" the continuity"""

	print(f"{timeline.name}:")
	
	timeline_trt = Timecode(0, rate=round(timeline.edit_rate))

	for continuity_scene in continuity_scenes:
		print(f" - {continuity_scene.scene_number.ljust(20)}{timecode_as_duration(continuity_scene.duration).rjust(11)}      {continuity_scene.description.ljust(48)}      {' - '.join([continuity_scene.location, continuity_scene.time_of_day])}")
		timeline_trt += continuity_scene.duration
	
	print(f"Reel TRT: {timecode_as_duration(timeline_trt)}")

def print_timeline_tsv(timeline:avb.trackgroups.Composition, continuity_scenes:list[ContinuitySceneInfo]):
	"""Output the continuity as tab-separated values"""

	print(f"{timeline.name}:")
	
	timeline_trt = Timecode(0, rate=round(timeline.edit_rate))

	for continuity_scene in continuity_scenes:
		print('\t'.join([
			continuity_scene.scene_number,
			timecode_as_duration(continuity_scene.duration),
			continuity_scene.description,
			' - '.join([continuity_scene.location, continuity_scene.time_of_day])
		]))
		timeline_trt += continuity_scene.duration
	
	print(f"Reel TRT: {timecode_as_duration(timeline_trt)}")

def print_numbers_doc(reels_info:list[ReelInfo], output_path:str="out.numbers", template_path:str|None=None):
	"""Create a Numbers document for the given"""

	def _num_columns(table:numbers_parser.document.Table) -> int:
		"""Return the number of columns in a table"""
		# TODO: Probably really slow

		return max(len(row) for row in table.rows())

	def _doc_style_from_existing(doc:numbers_parser.Document, existing:numbers_parser.Style, **kwargs) -> numbers_parser.Style:
		"""Add a document style based on an existing"""

		return doc.add_style(
			alignment     = kwargs["alignment"] if "alignment" in kwargs else existing.alignment,
			bg_image      = kwargs["bg_image"] if "bg_image" in kwargs else existing.bg_image,
			bg_color      = kwargs["bg_color"] if "bg_color" in kwargs else existing.bg_color,
			font_color    = kwargs["font_color"] if "font_color" in kwargs else existing.font_color,
			font_size     = kwargs["font_size"] if "font_size" in kwargs else existing.font_size,
			font_name     = kwargs["font_name"] if "font_name" in kwargs else existing.font_name,
			bold          = kwargs["bold"] if "bold" in kwargs else existing.bold,
			italic        = kwargs["italic"] if "italic" in kwargs else existing.italic,
			strikethrough = kwargs["strikethrough"] if "strikethrough" in kwargs else existing.strikethrough,
			underline     = kwargs["underline"] if "underline" in kwargs else existing.underline,
			first_indent  = kwargs["first_indent"] if "first_indent" in kwargs else existing.first_indent,
			left_indent   = kwargs["left_indent"] if "left_indent" in kwargs else existing.left_indent,
			right_indent  = kwargs["right_indent"] if "right_indent" in kwargs else existing.right_indent,
			text_inset    = kwargs["text_inset"] if "text_inset" in kwargs else existing.text_inset,
			text_wrap     = kwargs["text_wrap"] if "text_wrap" in kwargs else existing.text_wrap,
			name          = kwargs["text_wrap"] if "text_wrap" in kwargs else None
		)

	def _draw_borders(table:numbers_parser.document.Table, row_start:int, row_end:int, col_start:int, col_end:int, border_style=None):
		"""Draw borders around a range of cells"""

		border_style = border_style or numbers_parser.Border(2.0, numbers_parser.RGB(0,0,0), "solid")

		with warnings.catch_warnings():
			[table.set_cell_border(row_start, x,  ["top"], border_style) for x in range(col_end+1)]
			[table.set_cell_border(row_end, x, ["bottom"], border_style) for x in range(col_end+1)]
			[table.set_cell_border(x, col_start, ["left"], border_style) for x in range(row_start, row_end+1)]
			[table.set_cell_border(x, col_end,  ["right"], border_style) for x in range(row_start, row_end+1)]

	def _draw_blank_row(table:numbers_parser.document.Table):
		[table.set_cell_border(row_num, x, ["left","right"], numbers_parser.Border(0.0, numbers_parser.RGB(0, 0, 0), "none")) for x in range(5)]

	doc = numbers_parser.Document(template_path) or numbers_parser.Document()
	
	default_style = doc.styles["Table Style 2"]
	default_style.alignment = numbers_parser.Alignment("left","top")
	default_style.text_inset = 0

	# Setup styles
	style_scene_duration = _doc_style_from_existing(
		doc=doc,
		existing=default_style,
		alignment = numbers_parser.Alignment("right","top")
	)

	style_scene_location = _doc_style_from_existing(
		doc=doc,
		existing=default_style,
		alignment = numbers_parser.Alignment("right","top"),
		italic = True
	)

	style_reel_column = _doc_style_from_existing(
		doc=doc,
		existing=default_style,
		bg_color = numbers_parser.RGB(123, 161, 205)
	)

	style_reel_trt = _doc_style_from_existing( 
		doc=doc,
		existing=style_reel_column,
		alignment = numbers_parser.Alignment("right","top"),
		italic = True
	)

	style_lp_label = _doc_style_from_existing( 
		doc=doc,
		existing=style_reel_column,
		bold=True
	)

	style_lp_trt = _doc_style_from_existing(
		doc=doc,
		existing=style_reel_trt,
		#alignment = numbers_parser.Alignment("right"),
		#italic = True,
		bold = True
	)

	style_header_column = _doc_style_from_existing(
		doc=doc,
		existing=default_style,
		bg_color = numbers_parser.RGB(63, 103, 151),
		font_size = 13.0,
		alignment = numbers_parser.Alignment("center","top"),
		bold = True
	)

	style_blank_row = _doc_style_from_existing(
		doc=doc,
		existing=default_style,
		bg_color = numbers_parser.RGB(255,255,255)
	)

	sheet = doc.sheets[0]
	#sheet.name = "Continuity (Timings)"
	#sheet.add_table("Continuity Per Reel")
	table = sheet.tables[0]


	row_num = 0

	table.write(row_num, 1, "Scene", style=style_header_column)
	table.write(row_num, 2, "Duration", style=style_header_column)
	table.write(row_num, 3, "Scene Description", style=style_header_column)
	table.write(row_num, 4, "Location", style=style_header_column)

	table.set_cell_style(row_num, 0, style_blank_row)
	_draw_borders(table, row_num, row_num, 1, _num_columns(table)-1)
	table.set_cell_border(row_num, 0, ["left","top","bottom"], numbers_parser.Border(2.0, numbers_parser.RGB(0,0,0), "none"))
	
	row_num += 1
	_draw_blank_row(table)
	#table.write(row_num, 1, "")
	
	table.num_header_cols = 0
	table.num_header_rows = 1

	_draw_blank_row(table)
	[table.set_cell_style(row_num, x, style_blank_row) for x in range(_num_columns(table))]

	row_num += 1

	for reel_info in reels_info:

		row_start = row_num

		for scene_info in reel_info.scenes:

			table.write(row_num, 1, scene_info.scene_number, style=default_style)
			
			table.write(row_num, 2, str(scene_info.duration).lstrip("0:"), style=style_scene_duration)
			table.write(row_num, 3, scene_info.description, style=default_style)
			table.write(row_num, 4, ' - '.join([scene_info.location, scene_info.time_of_day]), style=style_scene_location)

			row_num += 1
		
		row_end = row_num-1

		# Write Reel Info Column
		# TODO: Handle reels with scenes < reel info rows
		table.write(row_start, 0, f"R{reel_info.reel_number} v{reel_info.reel_version}")
		table.write(row_end-1, 0, f"R{reel_info.reel_number} TRT:")
		table.write(row_end, 0, str(reel_info.reel_trt).lstrip("0:"))
		
		
		table.merge_cells(numbers_parser.xl_rowcol_to_cell(row_start,0)+":"+numbers_parser.xl_rowcol_to_cell(row_end-2,0))

		# BORDERS AHOY

		# Clear out reel column header
		[table.set_cell_border(x, 0, ["top", "bottom"], numbers_parser.Border(2.0, numbers_parser.RGB(0,0,0), "none")) for x in range(row_start, row_end+1)]

		# Add side border to reel column header
		[table.set_cell_border(x, 1, ["left"], numbers_parser.Border(2.0, numbers_parser.RGB(0,0,0), "solid")) for x in range(row_start, row_end+1)]

		# Reel column backround color
		[table.set_cell_style(x, 0, style_reel_column) for x in range(row_start, row_end+1)]
		table.set_cell_style(row_end, 0, style_reel_trt)

		# Draw a border around dat reel
		_draw_borders(table, row_start, row_end, 0, _num_columns(table)-1)
		
		# Blank row
		_draw_blank_row(table)
		row_num += 1

	# Write LP TRT
	table.write(row_num-1, 0, "LP TRT:", style=style_lp_label)
	table.set_cell_border(row_num-1, 0, ["left","right"], numbers_parser.Border(2.0, numbers_parser.RGB(0,0,0), "solid"))

	table.write(row_num, 0, str(sum(reel.reel_trt for reel in reels_info)).lstrip("0:"), style=style_lp_trt)
	table.set_cell_border(row_num, 0, ["left","right","bottom"], numbers_parser.Border(2.0, numbers_parser.RGB(0,0,0), "solid"))

	[table.set_cell_border(row_num-1, x, ["right","bottom"], numbers_parser.Border(2.0, numbers_parser.RGB(0,0,0), "none")) for x in range(1,_num_columns(table))]
	[table.set_cell_border(row_num,   x, ["right","bottom"], numbers_parser.Border(2.0, numbers_parser.RGB(0,0,0), "none")) for x in range(1,_num_columns(table))]


	output_path_final = pathlib.Path(output_path)

	while output_path_final.exists():
		sequential_filename = pat_sequential.match(output_path_final.stem)
		if sequential_filename:
			name_base = sequential_filename.group("base")
			name_digits = str(int(sequential_filename.group("digits"))+1).zfill(len(sequential_filename.group("digits")))
		else:
			name_base = output_path_final.stem
			name_digits = "_001"
		output_path_final = output_path_final.with_stem(name_base + name_digits)

	
	# Cleanup formatting
	DEFAULT_HEIGHT = 14
	DEFAULT_WIDTHS = [62, 90, 60, 305, 200]
	for idx, row in enumerate(table.rows()):
		[table.col_width(x, DEFAULT_WIDTHS[x]) for x in range(_num_columns(table))]
		table.row_height(idx, DEFAULT_HEIGHT)
	
	# Too much cleanup
	table.row_height(0, 18)
			
	
	doc.save(output_path_final)

	return output_path_final


def get_continuity_list_for_timeline(timeline:avb.trackgroups.Composition) -> list[ContinuitySceneInfo]:
	"""Get the continuity info for a given timeline/reel"""

	continuity_tracks = get_continuity_tracks_from_timeline(timeline)
	if len(continuity_tracks) != 1:
		raise ValueError(f"Found {len(continuity_tracks)} continuity tracks")
	continuity_track = continuity_tracks[0]

	continuity_sequence = continuity_track.component
	continuity_subclips = get_continuity_subclips_from_sequence(continuity_sequence)

	timeline_continuity:list[ContinuitySceneInfo] = list()

	for continuity_subclip in continuity_subclips:

		continuity_masterclip = avbutils.matchback_sourceclip(continuity_subclip)
		
		# Need to do a recursive matchback thing, but for now we know there won't be a big heirarchy
		if not avbutils.is_masterclip(continuity_masterclip):
			print(f"** Skipping {continuity_masterclip}")
			continue

		if not is_intended_for_continuity(continuity_masterclip):
			continue

		timeline_continuity.append(ContinuitySceneInfo(
			scene_number=continuity_masterclip.name or "Sc ???",
			duration=Timecode(continuity_subclip.length, rate=round(continuity_subclip.edit_rate)),
			description=continuity_masterclip.attributes.get("_USER").get("Comments","-"),
			location=continuity_masterclip.attributes.get("_USER").get("Location","-"),
			time_of_day=continuity_masterclip.attributes.get("_USER").get("Time of Day","-")
		))
	
	return timeline_continuity

def get_continuity_for_reel(timeline:avb.trackgroups.Composition) -> ReelInfo:
	"""Get the continuity of a given reel"""
			
	reelname_match = pat_reelname.match(timeline.name)
	if not reelname_match:
		print(f"Timeline name does not match the usual format: {timeline.name}")

	continuity_scenes = get_continuity_list_for_timeline(timeline)

	return ReelInfo(
		reel_name=reelname_match.group(0),
		reel_number=reelname_match.group("reel_number"),
		reel_version=reelname_match.group("reel_version"),
		reel_timecode_range=avbutils.get_timecode_range_for_composition(timeline),
		scenes = continuity_scenes
	)

def get_continuity_for_all_reels_in_bin(bin_path:str, print_function=print_timeline_tsv):
	"""Generate the continuity report for all reels in a given bin"""

	print(f"Opening bin {pathlib.Path(bin_path).name}...")

	master_trt = Timecode(0, rate=24)

	with avb.open(bin_path) as bin_handle:

		print("Finding continuity sequences...")
		timelines = sorted([seq for seq in avbutils.get_timelines_from_bin(bin_handle.content) if is_continuity_sequence(seq)],key=lambda x: avbutils.human_sort(x.name))

		reels:list[ReelInfo] = list()

		for timeline in timelines:
			reels.append(get_continuity_for_reel(timeline))
			
		master_trt = sum(reel.reel_trt for reel in reels)

		numbers_filename = pathlib.Path(bin_path).with_suffix(".numbers").name

		final_path = print_numbers_doc(reels, output_path=numbers_filename, template_path=pathlib.Path(__file__).parent / "templates/FHS_Continuity_template.numbers")

	print(f"Total Feature Runtime: {timecode_as_duration(master_trt)}")
	print("")

	print("Nubmers document output to", final_path)

if __name__ == "__main__":
	
	print_style = print_timeline_tsv

	if "--pretty" in sys.argv:
		print_style = print_timeline_pretty
		del sys.argv[sys.argv.index("--pretty")]

	if not len(sys.argv) > 1:
		sys.exit(USAGE)
	
	get_continuity_for_all_reels_in_bin(sys.argv[1], print_style)