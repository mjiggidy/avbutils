import sys
import avb, avbutils

def matchback_composition(composition:avb.trackgroups.Composition) -> dict[avb.trackgroups.Track, avb.components.Component]:

	return {
		track: track.component
		for track in composition.tracks
	}

def matchback_from_subclip(subclip:avb.trackgroups.Composition):

	print("Subclip:", subclip)

	subclip_tracks = matchback_composition(subclip)
	print("Has tracks:", subclip_tracks)
	
	print("")
	# Sequence component of usage "picture"

	# Matchback _masterclip_ component
	for track, component in subclip_tracks.items():
		print(f"{avbutils.format_track_label(track)}: Track Component")
		
		
		# Video track tends to be a avb.components.Sequence component.
		# TODO: Investigate sound subs cuz idunno lol

		if isinstance(component, avb.components.Sequence):

			if not len(component.components) == 3:
				raise ValueError(f"Enountered {len(component.components)} components, expected 3")
			
			if not isinstance(component.components[0], avb.components.Component) or not isinstance(component.components[2], avb.components.Component):
				raise ValueError(f"Didn't find expected Filler")
			
			subclip_track_component = component.components[1]
		
		elif isinstance(component, avb.components.Clip):
			subclip_track_component = component
		
		else:
			print("Subclip track component is weird:", component)
		
		# SourceClip interesting property data:
		# len == mastercliplength hopefully.
		# start_time=0 hopefully.
		# track_id (for video usually 1; for audio 1,2,3 etc as in A1, A2, A3)
		# mob_id
		print(subclip_track_component)


		# Matchback sourceclipcomponent
		# Matches back to SourceMob Composition
		master_mob = subclip_track_component.root.content.find_by_mob_id(subclip_track_component.mob_id)
		
		matchback_from_masterclip(master_mob)	

def matchback_from_masterclip(masterclip:avb.trackgroups.Composition):

	# Masterclip has length
	print("Masterclip:", masterclip)

	masterclip_tracks = matchback_composition(masterclip)
	print("Has tracks:", masterclip_tracks)
	
	print("")
	# Sequence component of usage "picture"

	# Matchback _masterclip_ component
	for track, component in masterclip_tracks.items():
		print(f"{avbutils.format_track_label(track)}: Track Component")
		
		
		# Video track tends to be a avb.components.Sequence component.
		# Audio track tends to go directly to avb.components.SoureClip

		if isinstance(component, avb.components.Sequence):

			if not len(component.components) == 3:
				raise ValueError(f"Enountered {len(component.components)} components, expected 3")
			
			if not isinstance(component.components[0], avb.components.Component) or not isinstance(component.components[2], avb.components.Component):
				raise ValueError(f"Didn't find expected Filler")
			
			masterclip_track_component = component.components[1]
		
		elif isinstance(component, avb.components.Clip):
			masterclip_track_component = component
		
		else:
			print("Masterclip track component is weird:", component)
		
		# SourceClip interesting property data:
		# len == mastercliplength hopefully.
		# start_time=0 hopefully.
		# track_id (for video usually 1; for audio 1,2,3 etc as in A1, A2, A3)
		# mob_id
		print(masterclip_track_component)


		# Matchback sourceclipcomponent
		# Matches back to SourceMob Composition
		source_mob_comp = masterclip_track_component.root.content.find_by_mob_id(masterclip_track_component.mob_id)
		
		print("")
		print("Source mob comp:")
		print(source_mob_comp)

		source_mob_comp_tracks = matchback_composition(source_mob_comp)
		print("Has tracks:", source_mob_comp_tracks)


		# ======================================================
		# AT FIRST SOURCE MOB THING: SOURCE MOB COMP:  PER-CLIP?
		# ======================================================

		for track, component in source_mob_comp_tracks.items():
			print(f"{avbutils.format_track_label(track)}: Source Mob Comp Track Component")

			if isinstance(component, avb.components.Sequence):
				
				if not len(component.components) == 3:
					raise ValueError(f"Enountered {len(component.components)} components, expected 3")
				
				if not isinstance(component.components[0], avb.components.Component) or not isinstance(component.components[2], avb.components.Component):
					raise ValueError(f"Didn't find expected Filler")
				
				source_mob_comp_track_component = component.components[1]
			
			elif isinstance(component, avb.components.Clip):
				source_mob_comp_track_component = component
			
			else:
				print("Sourcemob track component is weird:", component)


			# SourceClip again! interesting property data:
			# len == mastercliplength hopefully.
			# edit_rate float
			# start_time=Frame Offset from zero!! hopefully.
			# track_id (for video usually 1; for audio 1,2,3 etc as in A1, A2, A3)
			# mob_id	

			# SourceClip so match back via mob id lookup
			print(source_mob_comp_track_component)
			print("Mob ID Ref:", source_mob_comp_track_component.mob_id)
			# Note: Multitrack things, like soundrolls: all masterclip tracks above end up pointing to the same MOB ID
			# So like A1-5.mob_id is all the same.  Then matching back to soundroll below, it'll have all tracks
			tape_composition = source_mob_comp_track_component.root.content.find_by_mob_id(source_mob_comp_track_component.mob_id)
			
			# ==========================================================
			# AT SECOND SOURCE MOB THING: SOURCE MOB COMP:  TAPE/SOURCE?
			# ==========================================================
			print("")
			print("Source (Tape/Soundroll?) mob comp:")
			print(tape_composition)

			tape_tracks = matchback_composition(tape_composition)
			print("Has tracks:", tape_tracks)

			for track, component in tape_tracks.items():
				print(f"{avbutils.format_track_label(track)}: Source/Tape/Soundroll Mob Comp Track Component")

				if isinstance(component, avb.components.Sequence):
					
					if not len(component.components) == 3:

						# AT THIS POINT, dealing with the soundroll: it's basically all sources laid out with filler between

						print("Skipping", component, "(Got components:", str(len(component.components)),")")
						continue
						raise ValueError(f"Enountered {len(component.components)} components, expected 3: {component.components}")
					
					if not isinstance(component.components[0], avb.components.Component) or not isinstance(component.components[2], avb.components.Component):
						raise ValueError(f"Didn't find expected Filler")
					
					tape_comp_track_component = component.components[1]
				
				elif isinstance(component, avb.components.Clip):
					tape_comp_track_component = component
				
				else:
					print("Sourcemob track component is weird:", tape_comp_track_component)
			
				print(tape_comp_track_component)
				#import pprint
				#pprint.pprint(tape_comp_track_component.property_data)





		#pprint.pprint(masterclip_track_sequence_component.property_data)

		# In a masterclip -> track -> Sequence component,
		# The Sequence.components should only be 3:
		# Filler, Source Clip, Filler
		


if __name__ == "__main__":

	if not len(sys.argv) > 1:
		import pathlib
		sys.exit(f"Usage: {pathlib.Path(__file__).name} bin.avb")
	
	with avb.open(sys.argv[1]) as bin_handle:

		try:
			masterclip = next(item.mob for item in bin_handle.content.items if item.user_placed and avbutils.compositions.composition_is_subclip(item.mob))
		except StopIteration:
			sys.exit("Aint none")
		else:
			matchback_from_subclip(masterclip)