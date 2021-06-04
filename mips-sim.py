# -*- coding: utf-8 -*-
import sys
binfile = sys.argv[1]
N = int(sys.argv[2])
try:
    mode = sys.argv[3]
except:
    mode = ''

reg = [0]*33 # $0 ~ $31 + $32(PC)
hex_insts = list()
instMem = ['ff'] * (2**14 *4) # 0x00000000 ~ 0x00010000  1-byte boundaries (init 0xFF)
dataMem = ['ff']*(2**14*4) # 0x10000000 ~ 0x10010000 (init 0xFF)
cache = [{'set' : k, 'lru' : 0,
          'v' : [0,0], 'd':[0,0],'tag':[-1,-1],
                     'data': [[[] # word
                              for i in range(16)] for j in range(2)]} for k in range(8)]

dst_funct = {'100000':'add','100001':'addu','100100':'and','100111':'nor',
             '100101':'or','100010':'sub','100011':'subu','100110':'xor',
             '101010':'slt','101011':'sltu'}
dts_funct={'000100':'sllv','000111':'srav','000110':'srlv'}
st_funct={'011010':'div','011011':'divu','011000':'mult','011001':'multu'}
ds_funct={'001001':'jalr'}
s_funct={'001000':'jr','010001':'mthi','010011':'mtlo'}
d_funct={'010000':'mfhi','010010':'mflo'}
dt_shamt_funct = {'000000':'sll','000011':'sra','000010':'srl'}
syscall_funct={'001100' : 'syscall'}
st_label_opcode={'000100':'beq','000101':'bne'}
t_address_opcode={'100000':'lb','100100':'lbu','100001':'lh','100101':'lhu',
                  '100011':'lw','101001':'sh','101011':'sw','101000':'sb'}
ts_opcode_s={'001000':'addi','001100':'andi','001101':'ori','001110':'xori',
             '001010':'slti', '001001':'addiu'}
ts_opcode_us={'001011':'sltiu'}
target_opcode = {'000010':'j','000011':'jal'}
t_imm_opcode={'001111':'lui'}

inst_count = 0
hits = 0
misses = 0

def BinToHex(s):
    binary_value = int('0b'+s, 2)
    hex_value = hex(binary_value)
    hex_string = str(hex_value)[2:]
    if len(hex_string) == 2:
        return hex_string
    else:
        hex_string = '0'+hex_string
        return hex_string

def BinToDec(a, n):
    result = 0
    if a[0] == '0':
        return str(int('0b'+a, 2))
    else:
        neg = a.index('1')
        rest = int('0b' + a[neg+1:], 2)
        neg = pow(2,(n-1)-neg) * (-1)
        a = a[neg+1:]
        result += (neg + rest)
        return result
    
def IntDecToBin(d) : # consider as 32bits
    if d < 0:
        return int(bin(2**32 + d),2)
    else:
        return d
    
def BinToIntDec(b):
    temp = bin(b)
    if len(temp) == 34:
        n = (-1)*2**31 + int(temp[:2] + temp[3:],2)
        return n
    else:
        return b


# append bin file -> List
List = list()
with open(binfile, "rb") as f:
    while True:
        byte = f.read(1)
        if not byte:
            break
        List.append(bin(ord(byte))) 

# binary line -> hexadecimal line
for i in range(len(List)):
    item = List[i]
    item = item[2:]
    numZero = 8 - len(item)
    item = '0'*numZero + item
    List[i] = item

# filling in instMem
# filling in hex_insts

for i in range(0,len(List)):
    instMem[i] = List[i]


#for idx, inst in enumerate(instMem):
for _ in range(N):
    inst_count += 1
    PC = reg[32]
    inst = ''
    for i in range(4):
         inst += instMem[PC+i]
    if inst == 'ffffffff':
        reg[32] += 4 #PC + 4
        print('unknown instruction')
        break
    opcode = inst[:6]
    rs = inst[6:11] # 5bits
    rt = inst[11:16] # 5bits
    rd = inst[16:21] # 5bits
    shamt = inst[21:26] # 5bits
    funct = inst[26:] # 6bits
    if opcode == '000000' : #R-type instructions
        if funct in dst_funct.keys() :
            rd = int('0b'+rd, 2)
            rs = int('0b'+rs, 2)
            rt = int('0b'+rt, 2)
            if rd == 0:
                continue
            if dst_funct[funct] == 'add' or dst_funct[funct] == 'addu':
                reg[rd] = reg[rs] + reg[rt]
            elif dst_funct[funct] == 'sub':    
                reg[rd] = reg[rs] - reg[rt]
            elif dst_funct[funct] == 'and':
                reg[rd] = BinToIntDec(IntDecToBin(reg[rs]) & IntDecToBin(reg[rt]))
            elif dst_funct[funct] == 'or':
                reg[rd] = BinToIntDec(IntDecToBin(reg[rs]) | IntDecToBin(reg[rt]))
            elif dst_funct[funct] == 'slt' or dst_funct[funct] == 'sltu':   
                if reg[rs] < reg[rt]:
                    reg[rd] = 1
                else:
                    reg[rd] = 0
            reg[32] += 4 # PC+4
            continue
        elif funct in dt_shamt_funct.keys():
            rd = int('0b'+rd, 2)
            rt = int('0b'+rt, 2)
            shamt = int('0b'+shamt, 2)
            temp = bin(IntDecToBin(reg[rt]))[2:]
            empty = 32 - len(temp)
            temp = '0'*empty + temp
            if dt_shamt_funct[funct] == 'sll':
                temp = '0b' + temp[shamt:] + '0'*shamt
                reg[rd] = BinToIntDec(int(temp,2))
            elif dt_shamt_funct[funct] == 'srl':
                temp = '0b' + '0'*shamt + temp[:32-shamt]
                reg[rd] = BinToIntDec(int(temp,2))
            reg[32] += 4 #PC + 4
        elif funct in s_funct.keys(): # jr
            rs = int('0b'+rs,2)
            reg[32] = reg[rs]
        else:
            reg[32] += 4 #PC + 4
            break
    else: #I-type instructions
        rs = inst[6:11] # 5bits
        rt = inst[11:16] # 5bits
        off_imm = inst[16:] # 16bits
        if opcode in st_label_opcode.keys(): #I-type instructions
            rs = int('0b'+rs, 2)
            rt = int('0b'+rt, 2)
            off = int(BinToDec(off_imm,16))
            if st_label_opcode[opcode] == 'beq':
                if reg[rs] == reg[rt]:
                    reg[32] += (1 + off) * 4
                else:
                    reg[32] += 4 # PC+4
                    continue
            elif st_label_opcode[opcode] == 'bne':
                if reg[rs] != reg[rt]:
                    reg[32] +=  (1 + off) * 4
                else:
                    reg[32] += 4 # PC+4
                    continue
        elif opcode in t_address_opcode.keys():
            rt = int('0b'+rt, 2)
            rs = int('0b'+rs, 2)
            off = int(BinToDec(off_imm,16))
            if t_address_opcode[opcode] == 'lw':
                temp = bin(reg[rs]+off)
                empty = 34-len(temp)
                address= '0'*empty + temp[2:]
                tag = address[:23]
                index = int(address[23:26],2)
                block_off = int(address[26:30],2)
                byte_off = int(address[30:],2)
                   
                ##################################################
                if tag in cache[index]['tag']: #cache hit
                    hits += 1
                    number = cache[index]['tag'].index(tag)
                    word = cache[index]['data'][number][block_off]
                    
                    reg[rt] = BinToIntDec(int(word,16))
                    cache[index]['lru'] = 1-number
                    
                else : #cache miss
                    misses += 1
                    
                    replaced = cache[index]['lru']
                    
                    if(cache[index]['d'][replaced] == 1) : #dirty bit replace
                        origin_tag = cache[index]['tag'][replaced]
                        
                        origin_index = bin(index)[2:]
                        empty = 3 - len(origin_index)
                        origin_index = '0'*empty  + origin_index
                        
                        start = int('0b' + origin_tag + origin_index + '0'*6, 2)
                        end = int('0b' + origin_tag + origin_index + '1'*6,2)
                        
                        for i in range(16):
                            dataMem[start-16**7] = cache[index]['data'][replaced][i][:2]
                            dataMem[start-16**7+1] = cache[index]['data'][replaced][i][2:4]
                            dataMem[start-16**7+2] = cache[index]['data'][replaced][i][4:6]
                            dataMem[start-16**7+3] = cache[index]['data'][replaced][i][6:]
                            start += 4
                            
                    #fetch the block
                    repl_index = bin(index)[2:]
                    empty = 3 - len(repl_index)
                    repl_index = '0'*empty  + repl_index
                    
                    start = int('0b' + tag + repl_index + '0'*6, 2)
                    end = int('0b'+tag+repl_index + '1'*6,2)
                    
                    for i in range(16):
                        word = ''
                        for j in range(4):
                            word += dataMem[start-16**7+j]
                        cache[index]['data'][replaced][i] = word
                        start += 4
                    
                    cache[index]['lru'] = 1-replaced
                    cache[index]['tag'][replaced] = tag
                    cache[index]['d'][replaced] = 0
                    
                    word = cache[index]['data'][replaced][block_off]
                    reg[rt] = BinToIntDec(int(word,16))
                ###################################################
                
            elif t_address_opcode[opcode] == 'sw':
                temp = bin(reg[rs]+off)
                empty = 34-len(temp)
                address= '0'*empty + temp[2:]
                tag = address[:23]
                index = int(address[23:26],2)
                block_off = int(address[26:30],2)
                byte_off = int(address[30:],2)
                
                ####################################################
                if tag in cache[index]['tag']: #cache hit
                    hits += 1
                    number = cache[index]['tag'].index(tag)
                    temp = hex(IntDecToBin(reg[rt]))[2:]
                    empty = 8 - len(temp)
                    word = '0'*empty + temp
                    
                    cache[index]['data'][number][block_off] = word
                    cache[index]['lru'] = 1-number
                    cache[index]['d'][number] = 1
                    
                else: #cache miss
                    misses += 1
                    # fetch the block
                    # dirty block update
                    replaced = cache[index]['lru']
                    if(cache[index]['d'][replaced] == 1) :
                        origin_tag = cache[index]['tag'][replaced]
                        origin_index = bin(index)[2:]
                        empty = 3 - len(origin_index)
                        origin_index = '0'*empty  + origin_index                        
                        start = int('0b' + origin_tag + origin_index + '0'*6, 2)
                        end = int('0b' + origin_tag + origin_index + '1'*6,2)
                        
                        for i in range(16):
                            dataMem[start-16**7] = cache[index]['data'][replaced][i][:2]
                            dataMem[start-16**7+1] = cache[index]['data'][replaced][i][2:4]
                            dataMem[start-16**7+2] = cache[index]['data'][replaced][i][4:6]
                            dataMem[start-16**7+3] = cache[index]['data'][replaced][i][6:]
                            start += 4
                            
                    #fetch the block
                    repl_index = bin(index)[2:]
                    empty = 3 - len(repl_index)
                    repl_index = '0'*empty  + repl_index
                    
                    start = int('0b' + tag + repl_index + '0'*6, 2)
                    end = int('0b'+tag+repl_index + '1'*6,2)
                    
                    for i in range(16):
                        word = ''
                        for j in range(4):
                            word += dataMem[start-16**7+j]
                        cache[index]['data'][replaced][i] = word
                        start += 4
                    
                    cache[index]['tag'][replaced] = tag
                    
                    #update cache(set dirty bit)
                    number = cache[index]['tag'].index(tag)
                    temp = hex(IntDecToBin(reg[rt]))[2:]
                    empty = 8 - len(temp)
                    word = '0'*empty + temp

                    cache[index]['data'][number][block_off] = word
                    
                    cache[index]['lru'] = 1-number
                    cache[index]['d'][number] = 1
                    ######################################
        
            elif t_address_opcode[opcode] == 'lh':
                temp = bin(reg[rs]+off)
                empty = 34-len(temp)
                address= '0'*empty + temp[2:]
                tag = address[:23]
                index = int(address[23:26],2)
                block_off = int(address[26:30],2)
                byte_off = int(address[30:],2)
                   
                ##################################################
                if tag in cache[index]['tag']: #cache hit
                    hits += 1
                    number = cache[index]['tag'].index(tag)
                    word = cache[index]['data'][number][block_off][byte_off*2:byte_off*2+4]
                    
                    if int(word,16) >= 32768: # sign-extension
                        word = '0x' + 'ffff' + word
                        reg[rt] = BinToIntDec(int(word,16))
                    else: # zero-extention
                        reg[rt] = BinToIntDec(int(word,16))
                    
                    cache[index]['lru'] = 1-number
                    
                else : #cache miss
                    misses += 1
                    
                    replaced = cache[index]['lru']
                    
                    if(cache[index]['d'][replaced] == 1) : #dirty bit replace
                        origin_tag = cache[index]['tag'][replaced]
                        origin_index = bin(index)[2:]
                        empty = 3 - len(origin_index)
                        origin_index = '0'*empty  + origin_index
                        
                        start = int('0b' + origin_tag + origin_index + '0'*6, 2)
                        end = int('0b' + origin_tag + origin_index + '1'*6,2)
                        
                        for i in range(16):
                            dataMem[start-16**7] = cache[index]['data'][replaced][i][:2]
                            dataMem[start-16**7+1] = cache[index]['data'][replaced][i][2:4]
                            dataMem[start-16**7+2] = cache[index]['data'][replaced][i][4:6]
                            dataMem[start-16**7+3] = cache[index]['data'][replaced][i][6:]
                            start += 4
                            
                    #fetch the block
                    repl_index = bin(index)[2:]
                    empty = 3 - len(repl_index)
                    repl_index = '0'*empty  + repl_index
                    
                    start = int('0b' + tag + repl_index + '0'*6, 2)
                    end = int('0b' + tag + repl_index + '1'*6,2)
                    
                    for i in range(16):
                        word = ''
                        for j in range(4):
                            word += dataMem[start-16**7+j]
                        cache[index]['data'][replaced][i] = word
                        start += 4
                        
                    cache[index]['lru'] = 1-replaced
                    cache[index]['tag'][replaced] = tag
                    cache[index]['d'][replaced] = 0
                    
                    word = cache[index]['data'][replaced][block_off][byte_off*2:byte_off*2+4]
                    if int(word,16) >= 32768: # sign-extension
                        word = '0x' + 'ffff' + word
                        reg[rt] = BinToIntDec(int(word,16))
                    else: # zero-extention
                        reg[rt] = BinToIntDec(int(word,16))
                ###################################################                
                        
            elif t_address_opcode[opcode] == 'lhu':
                temp = bin(reg[rs]+off)
                empty = 34-len(temp)
                address= '0'*empty + temp[2:]
                tag = address[:23]
                index = int(address[23:26],2)
                block_off = int(address[26:30],2)
                byte_off = int(address[30:],2)
                   
                ##################################################
                if tag in cache[index]['tag']: #cache hit
                    hits += 1
                    number = cache[index]['tag'].index(tag)
                    word = cache[index]['data'][number][block_off][byte_off*2:byte_off*2+4]
                    
                    reg[rt] = BinToIntDec(int(word,16)) #zero-extension
                    
                    cache[index]['lru'] = 1-number
                    
                else : #cache miss
                    misses += 1
                    
                    replaced = cache[index]['lru']
                    
                    if(cache[index]['d'][replaced] == 1) : #dirty bit replace
                        origin_tag = cache[index]['tag'][replaced]
                        
                        origin_index = bin(index)[2:]
                        empty = 3 - len(origin_index)
                        origin_index = '0'*empty  + origin_index
                        
                        start = int('0b' + origin_tag + origin_index + '0'*6, 2)
                        end = int('0b' + origin_tag + origin_index + '1'*6,2)
                        
                        for i in range(16):
                            dataMem[start-16**7] = cache[index]['data'][replaced][i][:2]
                            dataMem[start-16**7+1] = cache[index]['data'][replaced][i][2:4]
                            dataMem[start-16**7+2] = cache[index]['data'][replaced][i][4:6]
                            dataMem[start-16**7+3] = cache[index]['data'][replaced][i][6:]
                            start += 4
                            
                    #fetch the block
                    repl_index = bin(index)[2:]
                    empty = 3 - len(repl_index)
                    repl_index = '0'*empty  + repl_index
                    
                    start = int('0b' + tag + repl_index + '0'*6, 2)
                    end = int('0b'+tag+repl_index + '1'*6,2)
                    
                    for i in range(16):
                        word = ''
                        for j in range(4):
                            word += dataMem[start-16**7+j]
                        cache[index]['data'][replaced][i] = word
                        start += 4
                        
                    cache[index]['lru'] = 1-replaced
                    cache[index]['tag'][replaced] = tag
                    cache[index]['d'][replaced] = 0
                    
                    word = cache[index]['data'][replaced][block_off][byte_off*2:byte_off*2+4]
                    reg[rt] = BinToIntDec(int(word,16)) # zero-extension
                ###################################################   
                    
            elif t_address_opcode[opcode] == 'sh':
                temp = bin(reg[rs]+off)
                empty = 34-len(temp)
                address= '0'*empty + temp[2:]
                tag = address[:23]
                index = int(address[23:26],2)
                block_off = int(address[26:30],2)
                byte_off = int(address[30:],2)
                
                ####################################################
                if tag in cache[index]['tag']: #cache hit
                    hits += 1
                    number = cache[index]['tag'].index(tag)
                    temp = hex(IntDecToBin(reg[rt]))[2:]
                    empty = 8 - len(temp)
                    word = '0'*empty + temp
                    word = word[4:]
                    
                    cache_list = list(cache[index]['data'][number][block_off])
                    for i in range(4):
                        cache_list[byte_off*2+i] = word[i]
                    word = ''.join(cache_list)
                    cache[index]['data'][number][block_off] = word
                    
                    cache[index]['lru'] = 1-number
                    cache[index]['d'][number] = 1
                    
                else: #cache miss
                    misses += 1
                    # fetch the block
                    # dirty block update
                    replaced = cache[index]['lru']
                    if(cache[index]['d'][replaced] == 1) :
                        origin_tag = cache[index]['tag'][replaced]
                        origin_index = bin(index)[2:]
                        empty = 3 - len(origin_index)
                        origin_index = '0'*empty  + origin_index                        
                        start = int('0b' + origin_tag + origin_index + '0'*6, 2)
                        end = int('0b' + origin_tag + origin_index + '1'*6,2)
                        
                        for i in range(16):
                            dataMem[start-16**7] = cache[index]['data'][replaced][i][:2]
                            dataMem[start-16**7+1] = cache[index]['data'][replaced][i][2:4]
                            dataMem[start-16**7+2] = cache[index]['data'][replaced][i][4:6]
                            dataMem[start-16**7+3] = cache[index]['data'][replaced][i][6:]
                            start += 4
                            
                    #fetch the block
                    repl_index = bin(index)[2:]
                    empty = 3 - len(repl_index)
                    repl_index = '0'*empty  + repl_index
                    
                    start = int('0b' + tag + repl_index + '0'*6, 2)
                    end = int('0b'+tag+repl_index + '1'*6,2)
                    
                    for i in range(16):
                        word = ''
                        for j in range(4):
                            word += dataMem[start-16**7+j]
                        cache[index]['data'][replaced][i] = word
                        start += 4
                    
                    cache[index]['tag'][replaced] = tag
                    
                    #update cache(set dirty bit)
                    number = cache[index]['tag'].index(tag)
                    temp = hex(IntDecToBin(reg[rt]))[2:]
                    empty = 8 - len(temp)
                    word = '0'*empty + temp
                    word = word[4:]
                    
                    cache_list = list(cache[index]['data'][number][block_off])
                    for i in range(4):
                        cache_list[byte_off*2+i] = word[i]
                    word = ''.join(cache_list)
                    cache[index]['data'][number][block_off] = word
                    
                    cache[index]['lru'] = 1-number
                    cache[index]['d'][number] = 1
                    ######################################
        
            elif t_address_opcode[opcode] == 'lb':
                temp = bin(reg[rs]+off)
                empty = 34-len(temp)
                address= '0'*empty + temp[2:]
                tag = address[:23]
                index = int(address[23:26],2)
                block_off = int(address[26:30],2)
                byte_off = int(address[30:],2)
                   
                ##################################################
                if tag in cache[index]['tag']: #cache hit
                    hits += 1
                    number = cache[index]['tag'].index(tag)
                    word = cache[index]['data'][number][block_off][byte_off*2:byte_off*2+2]
                    
                    if int(word,16) >= 128: # sign-extension
                        word = '0x' + 'ffffff' + word
                        reg[rt] = BinToIntDec(int(word,16))
                    else: # zero-extention
                        reg[rt] = BinToIntDec(int(word,16))
                    
                    cache[index]['lru'] = 1-number
                    
                else : #cache miss
                    misses += 1
                    
                    replaced = cache[index]['lru']
                    
                    if cache[index]['d'][replaced] == 1 : #dirty bit replace
                        origin_tag = cache[index]['tag'][replaced]
                        
                        origin_index = bin(index)[2:]
                        empty = 3 - len(origin_index)
                        origin_index = '0'*empty  + origin_index
                        
                        start = int('0b' + origin_tag + origin_index + '0'*6, 2)
                        end = int('0b' + origin_tag + origin_index + '1'*6,2)
                        
                        for i in range(16):
                            dataMem[start-16**7] = cache[index]['data'][replaced][i][:2]
                            dataMem[start-16**7+1] = cache[index]['data'][replaced][i][2:4]
                            dataMem[start-16**7+2] = cache[index]['data'][replaced][i][4:6]
                            dataMem[start-16**7+3] = cache[index]['data'][replaced][i][6:]
                            start += 4
                            
                    #fetch the block
                    repl_index = bin(index)[2:]
                    empty = 3 - len(repl_index)
                    repl_index = '0'*empty  + repl_index
                    
                    start = int('0b' + tag + repl_index + '0'*6, 2)
                    end = int('0b'+tag+repl_index + '1'*6,2)
                    
                    for i in range(16):
                        word = ''
                        for j in range(4):
                            word += dataMem[start-16**7+j]
                        cache[index]['data'][replaced][i] = word
                        start += 4
                        
                    cache[index]['lru'] = 1-replaced
                    cache[index]['tag'][replaced] = tag
                    cache[index]['d'][replaced] = 0
                    
                    word = cache[index]['data'][replaced][block_off][byte_off*2:byte_off*2+2]
                    if int(word,16) >= 128: # sign-extension
                        word = '0x' + 'ffffff' + word
                        reg[rt] = BinToIntDec(int(word,16))
                    else: # zero-extention
                        reg[rt] = BinToIntDec(int(word,16))
                ###################################################   
                
            elif t_address_opcode[opcode] == 'lbu':
                temp = bin(reg[rs]+off)
                empty = 34-len(temp)
                address= '0'*empty + temp[2:]
                tag = address[:23]
                index = int(address[23:26],2)
                block_off = int(address[26:30],2)
                byte_off = int(address[30:],2)
                   
                ##################################################
                if tag in cache[index]['tag']: #cache hit
                    hits += 1
                    number = cache[index]['tag'].index(tag)
                    word = cache[index]['data'][number][block_off][byte_off*2:byte_off*2+2]
                    
                    # zero-extention
                    reg[rt] = BinToIntDec(int(word,16))
                    
                    cache[index]['lru'] = 1-number
                    
                else : #cache miss
                    misses += 1
                    
                    replaced = cache[index]['lru']
                    
                    if(cache[index]['d'][replaced] == 1) : #dirty bit replace
                        origin_tag = cache[index]['tag'][replaced]
                        
                        origin_index = bin(index)[2:]
                        empty = 3 - len(origin_index)
                        origin_index = '0'*empty  + origin_index
                        
                        start = int('0b' + origin_tag + origin_index + '0'*6, 2)
                        end = int('0b' + origin_tag + origin_index + '1'*6,2)
                        
                        for i in range(16):
                            dataMem[start-16**7] = cache[index]['data'][replaced][i][:2]
                            dataMem[start-16**7+1] = cache[index]['data'][replaced][i][2:4]
                            dataMem[start-16**7+2] = cache[index]['data'][replaced][i][4:6]
                            dataMem[start-16**7+3] = cache[index]['data'][replaced][i][6:]
                            start += 4
                            
                    #fetch the block
                    repl_index = bin(index)[2:]
                    empty = 3 - len(repl_index)
                    repl_index = '0'*empty  + repl_index
                    
                    start = int('0b' + tag + repl_index + '0'*6, 2)
                    end = int('0b'+tag+repl_index + '1'*6,2)
                    
                    for i in range(16):
                        word = ''
                        for j in range(4):
                            word += dataMem[start-16**7+j]
                        cache[index]['data'][replaced][i] = word
                        start += 4
                        
                    cache[index]['lru'] = 1-replaced
                    cache[index]['tag'][replaced] = tag
                    cache[index]['d'][replaced] = 0
                    
                    word = cache[index]['data'][replaced][block_off][byte_off*2:byte_off*2+2]
                    # zero-extention
                    reg[rt] = BinToIntDec(int(word,16))
                ###################################################  
                
                
            elif t_address_opcode[opcode] == 'sb':
                temp = bin(reg[rs]+off)
                empty = 34-len(temp)
                address= '0'*empty + temp[2:]
                tag = address[:23]
                index = int(address[23:26],2)
                block_off = int(address[26:30],2)
                byte_off = int(address[30:],2)
                
                ####################################################
                if tag in cache[index]['tag']: #cache hit
                    hits += 1
                    number = cache[index]['tag'].index(tag)
                    temp = hex(IntDecToBin(reg[rt]))[2:]
                    empty = 8 - len(temp)
                    word = '0'*empty + temp
                    word = word[6:]
                    
                    cache_list = list(cache[index]['data'][number][block_off])
                    for i in range(2):
                        cache_list[byte_off*2+i] = word[i]
                    word = ''.join(cache_list)
                    cache[index]['data'][number][block_off] = word
                    
                    cache[index]['lru'] = 1-number
                    cache[index]['d'][number] = 1
                    
                else: #cache miss
                    misses += 1
                    
                    # dirty block update
                    replaced = cache[index]['lru']
                    if(cache[index]['d'][replaced] == 1) :
                        origin_tag = cache[index]['tag'][replaced]
                        origin_index = bin(index)[2:]
                        empty = 3 - len(origin_index)
                        origin_index = '0'*empty  + origin_index                        
                        start = int('0b' + origin_tag + origin_index + '0'*6, 2)
                        end = int('0b' + origin_tag + origin_index + '1'*6,2)
                        
                        for i in range(16):
                            dataMem[start-16**7] = cache[index]['data'][replaced][i][:2]
                            dataMem[start-16**7+1] = cache[index]['data'][replaced][i][2:4]
                            dataMem[start-16**7+2] = cache[index]['data'][replaced][i][4:6]
                            dataMem[start-16**7+3] = cache[index]['data'][replaced][i][6:]
                            start += 4
                            
                    #fetch the block
                    repl_index = bin(index)[2:]
                    empty = 3 - len(repl_index)
                    repl_index = '0'*empty  + repl_index
                    
                    start = int('0b' + tag + repl_index + '0'*6, 2)
                    end = int('0b'+tag+repl_index + '1'*6,2)
                    
                    for i in range(16):
                        word = ''
                        for j in range(4):
                            word += dataMem[start-16**7+j]
                        cache[index]['data'][replaced][i] = word
                        start += 4
                    
                    cache[index]['tag'][replaced] = tag
                    
                    #update cache(set dirty bit)
                    number = cache[index]['tag'].index(tag)
                    temp = hex(IntDecToBin(reg[rt]))[2:]
                    empty = 8 - len(temp)
                    word = '0'*empty + temp
                    word = word[6:]
                    
                    cache_list = list(cache[index]['data'][number][block_off])
                    for i in range(2):
                        cache_list[byte_off*2+i] = word[i]
                    word = ''.join(cache_list)
                    cache[index]['data'][number][block_off] = word
                    
                    cache[index]['lru'] = 1-number
                    cache[index]['d'][number] = 1
                    ######################################
                        
            reg[32] += 4 # PC+4
        elif opcode in ts_opcode_s.keys():
            rt = int('0b'+rt, 2)
            rs = int('0b'+rs, 2)
            imm = int(BinToDec(off_imm,16))
            if rt == 0:
                continue
            if ts_opcode_s[opcode] == 'addi' or ts_opcode_s[opcode] == 'addiu':
                reg[rt] = reg[rs] + imm
            elif ts_opcode_s[opcode] == 'andi':
                imm = int(BinToDec('0'*16 + off_imm,32))
                reg[rt] = BinToIntDec(IntDecToBin(reg[rs]) & imm)
                
            elif ts_opcode_s[opcode] == 'ori':
                imm = int(BinToDec('0'*16 + off_imm,32))
                reg[rt] = BinToIntDec(IntDecToBin(reg[rs]) | imm)
                
            elif ts_opcode_s[opcode] == 'slti':
                if reg[rs] < imm:
                    reg[rt] = 1
                else:
                    reg[rt] = 0
            reg[32] += 4
            continue
        
        elif opcode in t_imm_opcode.keys():
            rt = int('0b'+rt, 2)
            if t_imm_opcode[opcode] == 'lui':
                temp = bin(IntDecToBin(reg[rt]))[2:]
                if len(temp) < 17:
                    empty = 16 - len(temp)
                    temp = '0b' + off_imm + '0'*empty + temp
                    reg[rt] = BinToIntDec(int(temp,2))
                else:
                    cut = len(temp) - 16
                    temp = '0b' + off_imm + temp[cut:]
                    reg[rt] = BinToIntDec(int(temp,2))
            reg[32] += 4 # PC + 4
            continue
        else: #j-type instructions
            target = inst[6:] # 26bits        
            if opcode in target_opcode.keys():
                if target_opcode[opcode] == 'j':
                    
                    PC = bin(reg[32])[2:]
                    
                    empty = 32 - len(PC)
                    PC = '0'*empty + PC
                    reg[32] = int(PC[:4] + target + '00',2)
                    
                elif target_opcode[opcode] == 'jal':
                    reg[31] = reg[32] + 4
                    
                    PC = bin(reg[32])[2:]
                    
                    empty = 32 - len(PC)
                    PC = '0'*empty + PC
                    reg[32] = int(PC[:4] + target + '00',2)
            else:
                reg[32] += 4 #PC + 4
                break

if mode == 'reg':
    print('Instructions:', inst_count)
    print('Hits:', hits)
    print('Misses:', misses)
    print('Total:', hits+misses)
    for i in range(32):
        temp = hex(IntDecToBin(reg[i]))[2:]
        empty = 8 - len(temp)
        temp = '0x'+'0'*empty + temp
        print('${}: '.format(i)+temp)
    temp = hex(IntDecToBin(reg[32]))[2:]
    empty = 8 - len(temp)
    temp = '0x'+'0'*empty + temp
    print('PC: '+temp)
    
elif mode == 'mem':
    print('Instructions:', inst_count)
    print('Hits:', hits)
    print('Misses:', misses)
    print('Total:', hits+misses)
    memStart = sys.argv[4]
    start = int(memStart,16)-16**7
    for i in range(start,start+16,4):
        temp = ''
        for j in range(4):
            temp += dataMem[i+(j)]
        print('0x'+temp)
