import enum

bet_fmt = "64s"
block_header_fmt = '<32sIII'
# < : little endian
# 32s : prev_hash of 32 bytes (char) +
# I : timestamp, unsigned int (32 bit) +
# I : nonce, unsigned int (32 bit) +
# I : number of bets in the block, unsigned int (32 bit) +

# <32sII = little endian | byte[32] | unsigned int | unsigned int



class MessageType(enum.IntEnum):
    IBD_REQUEST = 1 # Request to download whole blockchain from peers
    IBD_RESPONSE = 2 # Response of whole blockchain download from peers
    NEW_BLOCK = 3 # A new valid block found

    NEW_BET = 4 # Request to place a new open bet
