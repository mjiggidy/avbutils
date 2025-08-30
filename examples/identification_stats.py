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
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.MASTER_MOB \
	   and avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.UNDEFINED

def composition_is_subclip(comp:avb.trackgroups.Composition) -> bool:
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.COMPOSITION_MOB \
	   and avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.SUBCLIP

def composition_is_source_mob(comp:avb.trackgroups.Composition) -> bool:
	# Straight-up source mob, not for effects renders etc, I don't think
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.SOURCE_MOB \
	   and avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.UNDEFINED

def composition_is_effect_mob(comp:avb.trackgroups.Composition) -> bool:
	return avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.EFFECT

def composition_is_groupclip(comp:avb.trackgroups.Composition) -> bool:
	# MobType.COMPOSITION_MOB always, it seems
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.COMPOSITION_MOB \
	   and avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.GROUP_CLIP

def composition_is_groupoofter(comp:avb.trackgroups.Composition) -> bool:
	# NOTE: GroupClip/GroupOofter == MasterClip/MasterMob?  Question mark?
	# Seems to accompany GroupClips 1-to-1
	# MobType.COMPOSITION_MOB always, it seems
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.COMPOSITION_MOB \
	   and avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.GROUP_OOFTER

def composition_is_motioneffect_mob(comp:avb.trackgroups.Composition) -> bool:
	# NOTE: DID NOT FIND ANY YET
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.COMPOSITION_MOB \
	   and avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.MOTION

def composition_is_precompute_clip(comp:avb.trackgroups.Composition) -> bool:
	# NOTE: avbutils.MobUsage.PRECOMPUTE seems to pair with avbutils.MobTypes.MASTER_MOB.  So like a Precompute Clip
	# Then avbutils.MobUsage.PRECOMPUTE_FILE,PRECOMPUTE_SOURCE_MOB source/file mobs pair with avbutils.MobTypes.SOURCE_MOB
	# Need to verify
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.MASTER_MOB \
	   and avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.PRECOMPUTE

def composition_is_precompute_mob(comp:avb.trackgroups.Composition) -> bool:
	# NOTE: avbutils.MobUsage.PRECOMPUTE seems to pair with avbutils.MobTypes.MASTER_MOB.  So like a Precompute Clip?
	# Then avbutils.MobUsage.PRECOMPUTE_FILE,PRECOMPUTE_SOURCE_MOB source/file mobs pair with avbutils.MobTypes.SOURCE_MOB
	# Need to verify
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.SOURCE_MOB \
	   and avbutils.MobUsage.from_composition(comp) in {avbutils.MobUsage.PRECOMPUTE_FILE, avbutils.MobUsage.PRECOMPUTE_SOURCE_MOB}

def composition_is_master_mob(comp:avb.trackgroups.Composition) -> bool:
	# I think this'll be reference mobs, vs user-placed Masterclips?  Let's seeee....
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.MASTER_MOB \
	   and avbutils.MobUsage.from_composition(comp) == avbutils.MobUsage.MASTER_MOB


def identify_mob(comp:avb.trackgroups.Composition) -> avbutils.BinDisplayOptions:

	if composition_is_timeline(comp):
		return avbutils.BinDisplayOptions.SEQUENCES
	if composition_is_masterclip(comp):
		return avbutils.BinDisplayOptions.MASTER_CLIPS
	if composition_is_subclip(comp):
		return avbutils.BinDisplayOptions.SUBCLIPS
	if composition_is_effect_mob(comp):
		return avbutils.BinDisplayOptions.EFFECTS
	if composition_is_groupclip(comp):
		return avbutils.BinDisplayOptions.GROUPS
	if composition_is_groupoofter(comp):
		return avbutils.BinDisplayOptions.GROUPS
	if composition_is_motioneffect_mob(comp):
		return avbutils.BinDisplayOptions.MOTION_EFFECTS
	if composition_is_precompute_clip(comp):
		return avbutils.BinDisplayOptions.PRECOMP_TITLES_MATTEKEYS
	if composition_is_precompute_mob(comp):
		return avbutils.BinDisplayOptions.PRECOMP_RENDERED_EFFECTS
	if composition_is_source_mob(comp):
		return avbutils.BinDisplayOptions.SOURCES
	if composition_is_master_mob(comp):
		return avbutils.BinDisplayOptions.MASTER_CLIPS
	else:
		return None
	


if __name__ == "__main__":

	import pathlib,dataclasses

	@dataclasses.dataclass(frozen=True)
	class MobInfo:
		mob_type: avbutils.MobTypes
		mob_usage: avbutils.MobUsage
		is_user_placed : bool
		identified_as: avbutils.BinDisplayOptions

	if not len(sys.argv) > 1:
		sys.exit(f"Usage: {pathlib.Path(__file__).name} folder/fulla/bins/")
	
	infos = set()

	print("")
	print(str().join([
		str(x).ljust(40) for x in ("Mob Type", "Mob Usage", "Mob Identification", "User Placed", "First Comp Name", "First Bin Path", )
	]))

	for bin_path in pathlib.Path(sys.argv[1]).rglob("*.avb", case_sensitive=False):
		
		if bin_path.name.startswith("."):
			continue

		with avb.open(bin_path) as bin_handle:

			for item in bin_handle.content.items:

				mob_info = MobInfo(
					mob_type  = avbutils.MobTypes.from_composition(item.mob),
					mob_usage = avbutils.MobUsage.from_composition(item.mob),
					is_user_placed = item.user_placed,
					identified_as = identify_mob(item.mob)
				)

				if mob_info not in infos:
					infos.add(mob_info)
					print(str().join([
						str(x).ljust(40) for x in (mob_info.mob_type, mob_info.mob_usage, mob_info.identified_as, "*" if mob_info.is_user_placed else "", item.mob.name, bin_path)
					]))