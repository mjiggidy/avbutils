import dataclasses, datetime
from timecode import Timecode

@dataclasses.dataclass(frozen=True)
class ReelInfo:
	"""Representation of a Sequence from an Avid bin"""

#	file_path:pathlib.Path
#	"""The file path of the originating bin"""

	sequence_name:str
	"""The name of the sequence"""

	date_modified:datetime.datetime
	"""The date the sequence was last modified in the bin"""

	duration_total:Timecode
	"""The total duration of the sequence"""

	duration_head_leader:Timecode
	"""The duration of the head leader"""

	duration_tail_leader:Timecode
	"""The duration of the tail leader"""

#	locked:str
#	"""If the bin was locked at the time of reading"""

	@property
	def duration_adjusted(self) -> Timecode:
		"""Duration of active picture, without head or tail leaders"""
		return self.duration_total - self.duration_head_leader - self.duration_tail_leader
	
	@property
	def lfoa(self) -> str:
		"""Last frame of action at 35mm 4-perf"""
		frame_number = (self.duration_total - self.duration_tail_leader).frame_number - 1
		return f"{frame_number//16}+{(frame_number%16):02}"