all:
	iverilog -I../../../../rtl -o design -cfile_list.txt -DSIMULATION

clean:
	rm design
	rm *.vcd
	rm *.output.txt

sim:
	vvp design

wave:
	vvp design
	gtkwave design.vcd -T wave_script.tcl &

