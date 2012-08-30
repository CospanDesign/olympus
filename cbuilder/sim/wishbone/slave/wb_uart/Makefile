all:
	iverilog -I../../../../rtl -o design -cfile_list.txt -DSIMULATION
strict:
	iverilog -I../../../../rtl -o design -cfile_list.txt -DSIMULATION -Wall
synthesis:
	iverilog -I../../../../rtl -o design -cfile_list.txt
clean:
	rm design
	rm *.vcd
sim:
	vvp design
wave:
	vvp design
	gtkwave design.vcd -T wave_script.tcl &

