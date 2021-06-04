# MIPS CPU Simulator
## Usage
input file : binary instructions

./mips-sim N reg
N개만큼의 instruction을 실행한 후의 레지스터 $0~$31의 값을 hexadecimal 형식으로 display
current PC 값 display

./mips-sim N mem 0x10000000
N개만큼의 instruction을 실행한 후의 메모리 주소 0x10000000부터 4개의 값을 display

![simulate](https://user-images.githubusercontent.com/76514241/119775746-fcf7c900-befe-11eb-86df-3fd734bef843.PNG)
