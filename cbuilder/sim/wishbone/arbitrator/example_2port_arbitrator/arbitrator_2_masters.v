//wishbone_interconnect.v
/*
Distributed under the MIT licesnse.
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


`timescale 1 ns/1 ps

module arbitrator_2_masters (
  clk,
  rst,

  //master ports
	m0_we_i,
	m0_cyc_i,
	m0_stb_i,
	m0_sel_i,
	m0_ack_o,
	m0_dat_i,
	m0_dat_o,
	m0_adr_i,
	m0_int_o,


	m1_we_i,
	m1_cyc_i,
	m1_stb_i,
	m1_sel_i,
	m1_ack_o,
	m1_dat_i,
	m1_dat_o,
	m1_adr_i,
	m1_int_o,




  //slave port
    s_we_o,
    s_cyc_o,
    s_stb_o,
    s_sel_o,
    s_ack_i,
    s_dat_o,
    s_dat_i,
    s_adr_o,
    s_int_i

);


//control signals
input               clk;
input               rst;

//wishbone slave signals
output              s_we_o;
output              s_stb_o;
output              s_cyc_o;
output  [3:0]       s_sel_o;
output  [31:0]      s_adr_o;
output  [31:0]      s_dat_o;

input   [31:0]      s_dat_i;
input               s_ack_i;
input               s_int_i;

parameter           MASTER_COUNT = 2;
//wishbone master signals
input			m0_we_i;
input			m0_cyc_i;
input			m0_stb_i;
input	[3:0]	m0_sel_i;
input	[31:0]	m0_adr_i;
input	[31:0]	m0_dat_i;
output	[31:0]	m0_dat_o;
output			m0_ack_o;
output			m0_int_o;


input			m1_we_i;
input			m1_cyc_i;
input			m1_stb_i;
input	[3:0]	m1_sel_i;
input	[31:0]	m1_adr_i;
input	[31:0]	m1_dat_i;
output	[31:0]	m1_dat_o;
output			m1_ack_o;
output			m1_int_o;




//registers/wires
//this should be parameterized
reg [7:0]           master_select;
reg [7:0]           priority_select;


wire                master_we_o  [MASTER_COUNT:0];
wire                master_stb_o [MASTER_COUNT:0];
wire                master_cyc_o [MASTER_COUNT:0];
wire  [3:0]         master_sel_o [MASTER_COUNT:0];
wire  [31:0]        master_adr_o [MASTER_COUNT:0];
wire  [31:0]        master_dat_o [MASTER_COUNT:0];


//master select block
parameter MASTER_NO_SEL = 8'hFF;
parameter MASTER_0 = 0;
parameter MASTER_1 = 1;


always @ (posedge clk) begin
	if (rst) begin
		master_select <= MASTER_NO_SEL;
	end
	else begin
		case (master_select)
			MASTER_0: begin
				if (~m0_cyc_i && ~s_ack_i) begin
					master_select <= MASTER_NO_SEL;
				end
			end
			MASTER_1: begin
				if (~m1_cyc_i && ~s_ack_i) begin
					master_select <= MASTER_NO_SEL;
				end
			end
			default: begin
				//nothing selected
				if (m0_cyc_i) begin
					master_select <= MASTER_0;
				end
				else if (m1_cyc_i) begin
					master_select <= MASTER_1;
				end
			end
		endcase
		if ((master_select != MASTER_NO_SEL) && (priority_select < master_select) && (!s_stb_o && !s_ack_i))begin
			master_select  <=  MASTER_NO_SEL;
		end
	end
end


//priority select




always @ (posedge clk) begin
	if (rst) begin
		priority_select <= MASTER_NO_SEL;
	end
	else begin
		//find the highest priority
		if (m0_cyc_i) begin
			priority_select  <= MASTER_0;
		end
		else if (m1_cyc_i) begin
			priority_select  <= MASTER_1;
		end
		else begin
			priority_select  <= MASTER_NO_SEL;
		end
	end
end




//slave assignments
assign  s_we_o  = (master_select != MASTER_NO_SEL) ? master_we_o[master_select]  : 0;
assign  s_stb_o = (master_select != MASTER_NO_SEL) ? master_stb_o[master_select] : 0;
assign  s_cyc_o = (master_select != MASTER_NO_SEL) ? master_cyc_o[master_select] : 0;
assign  s_sel_o = (master_select != MASTER_NO_SEL) ? master_sel_o[master_select] : 0;
assign  s_adr_o = (master_select != MASTER_NO_SEL) ? master_adr_o[master_select] : 0;
assign  s_dat_o = (master_select != MASTER_NO_SEL) ? master_dat_o[master_select] : 0;


//write select block
assign master_we_o[MASTER_0] = m0_we_i;
assign master_we_o[MASTER_1] = m1_we_i;



//strobe select block
assign master_stb_o[MASTER_0] = m0_stb_i;
assign master_stb_o[MASTER_1] = m1_stb_i;



//cycle select block
assign master_cyc_o[MASTER_0] = m0_cyc_i;
assign master_cyc_o[MASTER_1] = m1_cyc_i;



//select select block
assign master_sel_o[MASTER_0] = m0_sel_i;
assign master_sel_o[MASTER_1] = m1_sel_i;



//address seelct block
assign master_adr_o[MASTER_0] = m0_adr_i;
assign master_adr_o[MASTER_1] = m1_adr_i;



//data select block
assign master_dat_o[MASTER_0] = m0_dat_i;
assign master_dat_o[MASTER_1] = m1_dat_i;




//assign block
assign m0_ack_o = (master_select == MASTER_0) ? s_ack_i : 0;
assign m0_dat_o = s_dat_i;
assign m0_int_o = (master_select == MASTER_0) ? s_int_i : 0;

assign m1_ack_o = (master_select == MASTER_1) ? s_ack_i : 0;
assign m1_dat_o = s_dat_i;
assign m1_int_o = (master_select == MASTER_1) ? s_int_i : 0;



endmodule
