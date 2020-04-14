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



module wishbone_mem_interconnect (
	clk,
	rst,

	m_we_i,
	m_cyc_i,
	m_stb_i,
	m_sel_i,
	m_ack_o,
	m_dat_i,
	m_dat_o,
	m_adr_i,
	m_int_o,

	s0_we_o,
	s0_cyc_o,
	s0_stb_o,
	s0_sel_o,
	s0_ack_i,
	s0_dat_o,
	s0_dat_i,
	s0_adr_o,
	s0_int_i


);


parameter MEM_SEL_0	=	0;
parameter MEM_OFFSET_0	=	0;
parameter MEM_SIZE_0	=	4096;


//state

//control signals
input 				clk;
input 				rst;

//wishbone master signals
input 				m_we_i;
input				m_stb_i;
input				m_cyc_i;
input		[3:0]	m_sel_i;
input		[31:0]	m_adr_i;
input  		[31:0]	m_dat_i;
output reg	[31:0]	m_dat_o;
output reg			m_ack_o;
output reg			m_int_o;


//wishbone mem signals
output			s0_we_o;
output			s0_cyc_o;
output			s0_stb_o;
output	[3:0]		s0_sel_o;
output	[31:0]		s0_adr_o;
output	[31:0]		s0_dat_o;
input	[31:0]		s0_dat_i;
input			s0_ack_i;
input			s0_int_i;




reg [31:0] mem_select;

always @(rst or m_adr_i or mem_select) begin
	if (rst) begin
		//nothing selected
		mem_select <= 32'hFFFFFFFF;
	end
	else begin
		if ((m_adr_i >= MEM_OFFSET_0) && (m_adr_i < (MEM_OFFSET_0 + MEM_SIZE_0))) begin
			mem_select <= MEM_SEL_0;
		end
		else begin
			mem_select <= 32'hFFFFFFFF;
		end
	end
end


//data in from slave
always @ (mem_select or s0_dat_i) begin
	case (mem_select)
		MEM_SEL_0: begin
			m_dat_o <= s0_dat_i;
		end
		default: begin
			m_dat_o <= 32'h0000;
		end
	endcase
end



//ack in from slave

always @ (mem_select or s0_ack_i) begin
	case (mem_select)
		MEM_SEL_0: begin
			m_ack_o <= s0_ack_i;
		end
		default: begin
			m_ack_o <= 1'h1;
		end
	endcase
end



//int in from slave

always @ (mem_select or s0_int_i) begin
	case (mem_select)
		MEM_SEL_0: begin
			m_int_o <= s0_int_i;
		end
		default: begin
			m_int_o <= 1'h0;
		end
	endcase
end



assign s0_we_o	=	(mem_select == MEM_SEL_0) ? m_we_i: 0;
assign s0_stb_o	=	(mem_select == MEM_SEL_0) ? m_stb_i: 0;
assign s0_sel_o	=	(mem_select == MEM_SEL_0) ? m_sel_i: 0;
assign s0_cyc_o	=	(mem_select == MEM_SEL_0) ? m_cyc_i: 0;
assign s0_adr_o	=	(mem_select == MEM_SEL_0) ? m_adr_i: 0;
assign s0_dat_o	=	(mem_select == MEM_SEL_0) ? m_dat_i: 0;



endmodule
