# Find the TYPE_WEIGHTS block in scripts/config.py and replace it with:

TYPE_WEIGHTS = {
    "type1_update": 1.0,
    "type2_tip": 1.4,
    "type3_visual": 1.0,
    "type4_koshish": 1.2,  # New: Koshish notebook notes
}

# Weight notes:
# - 1.0 = baseline frequency
# - Type 2 stays at 1.4 (tips travel well on LinkedIn)
# - Type 4 at 1.2 since it's eye-catching and new — adjust down later
#   if it crowds out the other types in your feed
#
# With AVOID_REPEATS=True, you'll never get the same type two weeks
# in a row, so the rotation feels natural.
