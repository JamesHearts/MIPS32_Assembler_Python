'''
This code reads MIPS assembly and spits out a .MIF file.
'''
import re

# List for storing instructions by line in order to print
INSTRUCTIONS = []

# This is a dictionary for storing labels and locations
LABELS_TABLE = dict()

# Open file
FILENAME = "test0.txt"
ASSEMBLY = open(FILENAME, "r")
# Read file
ASSEMBLY_CONTENT = ASSEMBLY.read()
# Tokenize file by line
LINE_TOKENS = ASSEMBLY_CONTENT.splitlines()
# Tokenize file by words
WORD_TOKENS = re.split(r' |, |\n|\(|\)', ASSEMBLY_CONTENT)

"""
All compilers need at least two passes over the entire file.
The first pass is to record where the labels are inside the file. 
This is in order to find out where we are going to jump or branch.
The second pass is to assemble the low level code and print it out.
"""

"""
The Code below is used to perform the first pass using a loop over the list of line tokens
"""
label_location = 0

for i in range(len(LINE_TOKENS)):
    line_token = LINE_TOKENS[i]
    MATCH_IDENTIFIER = re.match(r'^([a-z])\w*', line_token, flags=0) # We use regex to match identifiers
    MATCH_LABEL = re.match(r'^([a-z])\w*\:', line_token, flags=0) # We use regex to match labels
    if MATCH_IDENTIFIER: # If an identifier is found...
        if MATCH_LABEL: # Check to see if it is a label
            if label_location is 0:
                label_location = i
            else:
                label_location = i-1
            LABELS_TABLE[MATCH_IDENTIFIER[0]] = label_location # If it is a label store the line number along and label name in a dictionary

"""
The Code below is a collection of functions used in performing the second pass
"""

# This function will convert 2-byte hex numbers into 16-bit binary.
def hex_to_bin(hex):
    hex_integer = int(hex, 16)
    return format(int(hex_integer), '0>16b')

# This function will convert a signed integer into a signed 16-bit binary.
def int_to_bin(integer):
    negative_one = int("0xffff", 16)
    if integer < 0:
        return format(integer & negative_one, '0>16b')
    else:
        return format(integer, '0>16b')

def shift(integer):
    return format(int(integer), '0>5b')

# This function calculates the binary value of a register
def register(reg):
    searchobj = re.search(r'(?!\$)(\d+)', reg, flags=0)
    if searchobj:
        return '{0:05b}'.format(int(searchobj[0]))

# Our compiler needs to read immediate values in hex and convert them to binary first
def immediate(immediate_value):
    return hex_to_bin(immediate_value)

# This function looks up the branch key in the branch dictionary from the first pass
def branch(branch_value, current_location):
    branch_location = LABELS_TABLE[branch_value]
    if branch_location > current_location:
        offset = abs(current_location - branch_location) - 1
    else:
        offset = -abs(current_location - branch_location)
    offset_binary = int_to_bin(offset)
    return offset_binary

# This function converts the target to binary
def jump(target):
    jump_target = LABELS_TABLE[target]
    return format(jump_target, '0>26b')

"""
The Code below is used to perform the second pass using a loop over the list of word tokens
"""
LINE_COUNT = -1 # Keep trach of current line so we can calculate branch

# Perform the second pass using a loop over the list of word tokens
for i in range(len(WORD_TOKENS)):
    word_token = WORD_TOKENS[i]
    # The variables below are used to compose each line of hex code
    opcode = "" # Is the op code of each instruction
    src = "" # Is the source register
    tmp = "" # Is the temporary register
    dst = "" # Is the destination register
    shamt = "" # Is the shift amount
    imm = "" # Is an immediate value
    br = "" # Is the branch location
    lsoff = "" # Load/Store offset
    jmp = "" # Jump target
    instruction = "" # The final instruction in hexadecimal

    # Almost every instruction is unique
    # They are assembled below
    if(word_token == "add"):
        LINE_COUNT += 1 # Everytime we encounter an instruction it means we are on a new line so increment by 1
        opcode = "000000" # There is a differnt opcode for different types of instructions R-TYPE, I-TYPE, J-TYPE
        dst = register(WORD_TOKENS[i+1])
        src = register(WORD_TOKENS[i+2])
        tmp = register(WORD_TOKENS[i+3])
        instruction = opcode + src + tmp + dst + "00000100000" # Notice that the order in which instructions are read are different when assembled
    elif(word_token == "addi"):
        LINE_COUNT += 1
        opcode = "001000"
        tmp = register(WORD_TOKENS[i+1])
        src = register(WORD_TOKENS[i+2])
        imm = immediate(WORD_TOKENS[i+3]) # This is the immediate value in an immediate type instruction
        instruction = opcode + src + tmp + imm # The order is also different for I-Type Instructions.
    elif(word_token == "beq"):
        LINE_COUNT += 1
        opcode = "000100"
        src = register(WORD_TOKENS[i+1])
        tmp = register(WORD_TOKENS[i+2])
        br = branch(WORD_TOKENS[i+3], LINE_COUNT) # For branch instructions he branch offset must be calculated
        instruction = opcode + src + tmp + br
    elif(word_token == "j"):
        LINE_COUNT += 1
        opcode = "000010"
        jmp = jump(WORD_TOKENS[i+1])
        instruction = opcode + jmp
    elif(word_token == "jr"):
        LINE_COUNT += 1
        opcode = "000000"
        src = register(WORD_TOKENS[i+1])
        instruction = opcode + src + "000000000000000001000"
    elif(word_token == "lw"):
        LINE_COUNT += 1
        opcode = "100011"
        tmp = register(WORD_TOKENS[i+1])
        lsoff = int_to_bin(int(WORD_TOKENS[i+2])) # For load instructions we might have to convert the offset from integer to binary
        src = register(WORD_TOKENS[i+3])
        instruction = opcode + src + tmp + lsoff
    elif(word_token == "srl"):
        LINE_COUNT += 1
        opcode = "000000"
        dst = register(WORD_TOKENS[i+1])
        tmp = register(WORD_TOKENS[i+2])
        sft = shift(WORD_TOKENS[i+3]) # Shift instructions need to have the shift amount converted
        instruction = opcode + "00000" + tmp + dst + sft + "000010"
    elif(word_token == "sub"):
        LINE_COUNT += 1
        opcode = "000000"
        dst = register(WORD_TOKENS[i+1])
        src = register(WORD_TOKENS[i+2])
        tmp = register(WORD_TOKENS[i+3])
        instruction = opcode + src + tmp + dst + "00000100010" 
    elif(word_token == "sw"):
        LINE_COUNT += 1
        opcode = "101011"
        tmp = register(WORD_TOKENS[i+1])
        lsoff = hex_to_bin(WORD_TOKENS[i+2]) # For the sw instruction we convert from hex to binary
        src = register(WORD_TOKENS[i+3])
        instruction = opcode + src + tmp + lsoff
    if instruction:
        INSTRUCTIONS.append(instruction)


"""
The below code writes to a textfile
"""
# This function converts a 32-bit instruction to hex
def inst_to_hex(inst):
    return '%08X' % int(inst, 2)

OUTPUT = open('output.txt', 'w')

# Print out the header
OUTPUT.write(
"""
WIDTH=32;
DEPTH=256;

ADDRESS_RADIX=HEX;
DATA_RADIX=HEX;

CONTENT BEGIN
"""
)

# This loop below prints out each line of instruction.
for i in range(LINE_COUNT):
    OUTPUT.write("      ")
    OUTPUT.write(format(i, '0>3x'))
    OUTPUT.write("  :   ")
    OUTPUT.write(inst_to_hex(INSTRUCTIONS[i]))
    OUTPUT.write(";" + "\n")

# This loop below prints out the rest of the instructions as zero if not used.
if LINE_COUNT is not 255:
    OUTPUT.write("      ")
    OUTPUT.write("[" + format(LINE_COUNT, '0>3x'))
    OUTPUT.write(" : " + format(255, '0>3x') + "]")
    OUTPUT.write("  :   " + "00000000;")
    OUTPUT.write("\n" + "END;")
    