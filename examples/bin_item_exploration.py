import sys
import avb, avbutils

def list_bin(bin:avb.bin.Bin):
	"""List the bin contents"""

	for idx, item in enumerate([x for x in bin.items if x.user_placed]):
		mob = item.mob
		item.y = 16 + (idx * 175)
		print(mob.name, f"({item.x},{item.y})", f"Thumb Frame: {item.keyframe}")

def main(path_bins):

	for path_bin in path_bins:
		with avb.open(path_bin) as ref_bin:

			list_bin(ref_bin.content)

			ref_bin.write("out.avb")

if __name__ == "__main__":

	if len (sys.argv) < 2:
		sys.exit("Usage: {__file__} bin.avb")
	
	main(sys.argv[1:])