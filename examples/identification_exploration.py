import sys, os, typing
import avb, avbutils

# Masterclip:		mob_type = MasterMob. (usage/media_kind n/a)
# Subclip:			mob_type = CompositionMob;  usage = subclip
# Timeline:			mob_type = CompositionMob; user_placed=True, usage_code=None, media_kind=None
# Source mobs:		mob_type = SourceMob; have .descriptor pointing to essence
#	MDTP: Tape descriptor
#	MDES: Media descriptor (file import?)
#	MDNG: NagraDescriptor (soundroll?)
#	PCMA: Audio essence
#	CDCI: Codec...? Something?  Corresponds to subclip?

def composition_is_timeline(comp:avb.trackgroups.Composition) -> bool:
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.COMPOSITION_MOB \
	   and avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.UNDEFINED

def composition_is_masterclip(comp:avb.trackgroups.Composition) -> bool:
	"""Composition is a regular masterclip"""
	return avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.UNDEFINED \
	   and avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.MASTER_MOB

# NOTE: I think we can just rely on usage code here
def composition_is_master_mob(comp:avb.trackgroups.Composition) -> bool:
	"""Composition is a master mob, which consists of masterclips as well as precomputes and other clips"""
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.MASTER_MOB

def composition_is_subclip(comp:avb.trackgroups.Composition) -> bool:
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.COMPOSITION_MOB \
	   and avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.SUBCLIP

def composition_is_source_mob(comp:avb.trackgroups.Composition) -> bool:
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.SOURCE_MOB

def composition_is_effect_mob(comp:avb.trackgroups.Composition) -> bool:
	return avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.EFFECT





def get_masterclips_from_bin(bin_content:avb.bin.Bin, allow_reference_clips:bool=False) -> typing.Generator[avb.trackgroups.Composition,None,None]:

	for i in bin_content.items:
		if not composition_is_masterclip(i.mob):
			continue
		if not allow_reference_clips and not i.user_placed:
			continue
		yield i.mob

def get_master_mobs_from_bin(bin_content:avb.bin.Bin, allow_reference_clips:bool=False) -> typing.Generator[avb.trackgroups.Composition,None,None]:

	for i in bin_content.items:
		if not composition_is_master_mob(i.mob):
			continue
		if not allow_reference_clips and not i.user_placed:
			continue
		yield i.mob

def get_subclips_from_bin(bin_content:avb.bin.Bin, allow_reference_clips:bool=False) -> typing.Generator[avb.trackgroups.Composition,None,None]:

	for i in bin_content.items:
		if not composition_is_subclip(i.mob):
			continue
		if not allow_reference_clips and not i.user_placed:
			continue
		yield i.mob


def get_source_mobs_from_bin(bin_content:avb.bin.Bin, allow_reference_clips:bool=False) -> typing.Generator[avb.trackgroups.Composition,None,None]:

	for i in bin_content.items:
		if not composition_is_source_mob(i.mob):
			continue
		if not allow_reference_clips and not i.user_placed:
			continue
		yield i.mob

def get_effect_mobs_from_bin(bin_content:avb.bin.Bin, allow_reference_clips:bool=False) -> typing.Generator[avb.trackgroups.Composition,None,None]:

	for i in bin_content.items:
		if not composition_is_effect_mob(i.mob):
			continue
		if not allow_reference_clips and not i.user_placed:
			continue
		yield i.mob













def show_effectmob_data_for_bin(bin_content:avb.bin.Bin, allow_reference_clips:bool=False):

	clip_audio = []
	clip_video = []
	clip_other = []

	for clip in get_effect_mobs_from_bin(bin_content, allow_reference_clips=allow_reference_clips):

		print(clip)

		track_types = avbutils.get_track_types_from_composition(clip)


		if avbutils.TrackTypes.PICTURE in track_types:
			print("Looks like a video", clip.usage)
			clip_video.append(clip)
		elif avbutils.TrackTypes.SOUND in track_types:
			print("Looks like an audio", clip.usage)
			clip_audio.append(clip)
		else:
			print("Weird one:", track_types)
			clip_other.append(clip)
		
		print("--")

	print(f"{len(clip_video)=}  {len(clip_audio)=}  {len(clip_other)=}")

def show_sourcemob_data_for_bin(bin_content:avb.bin.Bin, allow_reference_clips:bool=False):

	clip_audio = []
	clip_video = []
	clip_other = []

	for clip in get_source_mobs_from_bin(bin_content, allow_reference_clips=allow_reference_clips):

		print(clip)

		track_types = avbutils.get_track_types_from_composition(clip)


		if avbutils.TrackTypes.PICTURE in track_types:
			print("Looks like a video ", clip.usage)
			clip_video.append(clip)
		elif avbutils.TrackTypes.SOUND in track_types:
			print("Looks like an audio ", clip.usage)
			clip_audio.append(clip)
		else:
			print("Weird one:", track_types)
			clip_other.append(clip)
		
		print("--")

	print(f"{len(clip_video)=}  {len(clip_audio)=}  {len(clip_other)=}")


def show_subclip_data_for_bin(bin_content:avb.bin.Bin, allow_reference_clips:bool=False):

	clip_audio = []
	clip_video = []
	clip_other = []

	for clip in get_subclips_from_bin(bin_content, allow_reference_clips=allow_reference_clips):

		print(clip)

		track_types = avbutils.get_track_types_from_composition(clip)

		if avbutils.TrackTypes.PICTURE in track_types:
			print("Looks like a video masterclip")
			clip_video.append(clip)
		elif avbutils.TrackTypes.SOUND in track_types:
			print("Looks like an audio masterclip")
			clip_audio.append(clip)
		else:
			print("Weird one:", track_types)
			clip_other.append(clip)
		
		print("--")

	print(f"{len(clip_video)=}  {len(clip_audio)=}  {len(clip_other)=}")

def show_master_mob_data_for_bin(bin_content:avb.bin.Bin, allow_reference_clips:bool=False):

	clip_audio = []
	clip_video = []
	clip_other = []

	usage = []
	for clip in get_master_mobs_from_bin(bin_content, allow_reference_clips=allow_reference_clips):
		
		print(clip)
		
		# Lookup by masterclip.mob_id yields the same as masterclip itself... just checking
		#print(bin_handle.content.find_by_mob_id(masterclip.mob_id))

		track_types = avbutils.get_track_types_from_composition(clip)

		if avbutils.TrackTypes.PICTURE in track_types:
			print("Looks like a video", clip.usage)
			clip_video.append(clip)
		elif avbutils.TrackTypes.SOUND in track_types:
			print("Looks like an audio", clip.usage)
			clip_audio.append(clip)
		else:
			print("Weird one:", clip.usage, track_types)
			clip_other.append(clip)

		usage.append(clip.usage)
		
		print("--")

	print(f"{len(clip_video)=}  {len(clip_audio)=}  {len(clip_other)=}")
	print(set(usage))

def show_masterclip_data_for_bin(bin_content:avb.bin.Bin, allow_reference_clips:bool=False):

	masterclip_audio = []
	masterclip_video = []
	masterclip_other = []

	for masterclip in get_masterclips_from_bin(bin_content, allow_reference_clips=allow_reference_clips):
		
		usage = set()
		print(masterclip)
		
		# Lookup by masterclip.mob_id yields the same as masterclip itself... just checking
		#print(bin_handle.content.find_by_mob_id(masterclip.mob_id))

		track_types = avbutils.get_track_types_from_composition(masterclip)

		if avbutils.TrackTypes.PICTURE in track_types:
			print("Looks like a video", masterclip.usage)
			masterclip_video.append(masterclip)
		elif avbutils.TrackTypes.SOUND in track_types:
			print("Looks like an audio", masterclip.usage)
			masterclip_audio.append(masterclip)
		else:
			print("Weird one:", masterclip.usage, track_types)
			masterclip_other.append(masterclip)

		usage.add(masterclip.usage)
		
		print("--")

	print(f"{len(masterclip_video)=}  {len(masterclip_audio)=}  {len(masterclip_other)=}")
	print(usage)

def main(bin_path:os.PathLike):

	with avb.open(bin_path) as bin_handle:
		print(f"GOT BIN") #Binfo
		
		# File info
		print(f"Path:       {bin_handle.f.name}")
		print(f"Last Saved: {bin_handle.last_save}")
		print(f"Creator:    {bin_handle.creator_version}")
		print("\n")


		#show_masterclip_data_for_bin(bin_handle.content, True)
		
		show_master_mob_data_for_bin(bin_handle.content, True)




if __name__ == "__main__":

	if not len(sys.argv) > 1:
		import pathlib
		sys.exit(f"Usage: {pathlib.Path(__file__).name} bin_path.avb")
	
	main(sys.argv[1])