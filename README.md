# MIPS CPU Simulator
## Usage
input file : binary instructions

./mips-sim N reg
N개만큼의 instruction을 실행한 후의 레지스터 $0~$31의 값을 hexadecimal 형식으로 display
current PC 값 display
총 실행한 Instruction의 갯수, cache hit, cache miss, total access 의 갯수 display

![image](https://user-images.githubusercontent.com/76514241/120810237-cf0d2700-c585-11eb-91d3-9ff3d98bdcfb.png)





./mips-sim N mem 0x10000000
N개만큼의 instruction을 실행한 후의 메모리 주소 0x10000000부터 4개의 값을 display
총 실행한 Instruction의 갯수, cache hit, cache miss, total access 의 갯수 display

![image](https://user-images.githubusercontent.com/76514241/120810317-e21ff700-c585-11eb-9936-7600b06e37f5.png)

