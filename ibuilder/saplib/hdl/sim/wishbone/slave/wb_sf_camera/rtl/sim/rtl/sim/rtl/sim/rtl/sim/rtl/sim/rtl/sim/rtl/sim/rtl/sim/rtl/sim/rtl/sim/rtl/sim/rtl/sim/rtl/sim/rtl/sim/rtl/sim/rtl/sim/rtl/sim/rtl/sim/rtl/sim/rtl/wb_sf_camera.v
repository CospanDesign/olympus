//wb_sf_camera.v
/*
Distributed under the MIT license.
Copyright (c) 2011 Dave McCoy (dave.mccoy@cospandesign.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to 
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do 
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.
*/
/*
	Use this to tell sycamore how to populate the Device ROM table
	so that users can interact with your slave

	META DATA

	identification of your device 0 - 65536
	DRT_ID:  13

	flags (read drt.txt in the slave/device_rom_table directory 1 means
	a standard device
	DRT_FLAGS:  1

	number of registers this should be equal to the nubmer of ADDR_???
	parameters
	DRT_SIZE:  3

*/


`include "project_defines.v"

`define CONTROL_ENABLE            0
`define CONTROL_CONTINUOUS        1 
`define CONTROL_INTERRUPT_ENABLE  2

`define STATUS_BUSY               0
`define STATUS_IMAGE_FINISHED     1

module wb_sf_camera (
	clk,
	rst,

	//Add signals to control your device here

	wbs_we_i,
	wbs_cyc_i,
	wbs_sel_i,
	wbs_dat_i,
	wbs_stb_i,
	wbs_ack_o,
	wbs_dat_o,
	wbs_adr_i,
	wbs_int_o,

  //mem master
	mem_we_o,
	mem_stb_o,
	mem_cyc_o,
	mem_sel_o,
	mem_adr_o,
	mem_dat_o,
	mem_dat_i,
	mem_ack_i,
	mem_int_i,

  cam_out_clk,
  cam_enable,
  cam_reset,
  cam_vblank,
  cam_hblank,
  cam_clk,
  cam_data
);

input 				      clk;
input 				      rst;

//wishbone slave signals
input 				      wbs_we_i;
input 				      wbs_stb_i;
input 				      wbs_cyc_i;
input		    [3:0]	  wbs_sel_i;
input		    [31:0]	wbs_adr_i;
input  		  [31:0]	wbs_dat_i;
output reg  [31:0]	wbs_dat_o;
output reg			    wbs_ack_o;
output reg			    wbs_int_o;


//master control signal for memory arbitration
output reg			    mem_we_o;
output reg			    mem_stb_o;
output reg			    mem_cyc_o;
output reg	[3:0]	  mem_sel_o;
output reg	[31:0]	mem_adr_o;
output reg	[31:0]	mem_dat_o;
input		    [31:0]	mem_dat_i;
input				        mem_ack_i;
input				        mem_int_i;

//camera I/O
output              cam_out_clk;
output              cam_enable;
output              cam_reset;
input               cam_vblank;
input               cam_hblank;
input               cam_clk;
input       [7:0]   cam_data;


parameter			      REG_CONTROL	=	32'h00000000;
parameter			      REG_STATUS	=	32'h00000001;
parameter			      REG_CLOCK_RATE	=	32'h00000002;

parameter           MEM_BASE  = 31'h00000000;


//Registers/Wires

reg         [31:0]  mem_address;
wire         [31:0] mem_data;
wire                mem_write;

reg         [31:0]  control;
wire                control_enable;

reg         [31:0]  status;
wire                image_finished;

//Clock Divider
reg         [31:0]  clock_divisor;

//submodules
sf_camera sfc (
  .clk(clk),
  .rst(rst),

  .out_clk(cam_out_clk),
  .enable(cam_enable),
  .reset(cam_reset),
  .vblank(cam_vblank),
  .hblank(cam_hblank),
  .cam_clk(cam_clk),
  .data(cam_data),

  .control_enable(control_enable),

  .image_finished  (image_finished),

  .memory_data(mem_data),
  .memory_write(mem_write),

  .clock_divisor(clock_divisor)

);

//Assigns
assign  control_enable    = control[`CONTROL_ENABLE];


//blocks
always @ (posedge clk) begin
	if (rst) begin
		wbs_dat_o	    <=  32'h0;
		wbs_ack_o	    <=  0;
		wbs_int_o	    <=  0;

    control       <=  0;
    status        <=  0;
    clock_divisor <=  0;
	end

	else begin

    status[`STATUS_IMAGE_FINISHED]  <=  image_finished;

		//when the master acks our ack, then put our ack down
		if (wbs_ack_o & ~ wbs_stb_i)begin
			wbs_ack_o <= 0;
		end

		if (wbs_stb_i & wbs_cyc_i) begin
			//master is requesting somethign
			if (wbs_we_i) begin
				//write request
				case (wbs_adr_i) 
					REG_CONTROL: begin
            control   <=  wbs_dat_i;
						$display("user wrote %h", wbs_dat_i);
					end
					default: begin
					end
				endcase
			end

			else begin 
				//read request
				case (wbs_adr_i)
					REG_CONTROL: begin
						wbs_dat_o <= control;
					end
					REG_STATUS: begin
						wbs_dat_o <= status;
					end
					REG_CLOCK_RATE: begin
						wbs_dat_o <= `CLOCK_RATE;
					end
					default: begin
					end
				endcase
			end
			wbs_ack_o <= 1;
		end
	end
end


//XXX: There is a big problem with Latency, I need to make sure I'm ahead of the data


//Send Data to the Memory
always @ (posedge clk) begin
  if (rst) begin
  end
  else begin

    if (mem_write) begin
      //initiate a transaction
    end
  end
end

endmodule
