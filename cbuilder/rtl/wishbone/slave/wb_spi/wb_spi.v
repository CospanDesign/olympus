//wbs_spi.v

//////////////////////////////////////////////////////////////////////
////                                                              ////
////  spi_top.v                                                   ////
////                                                              ////
////  This file is part of the SPI IP core project                ////
////  http://www.opencores.org/projects/spi/                      ////
////                                                              ////
////  Author(s):                                                  ////
////      - Simon Srot (simons@opencores.org)                     ////
////                                                              ////
////  All additional information is avaliable in the Readme.txt   ////
////  file.                                                       ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2002 Authors                                   ////
////                                                              ////
//// This source file may be used and distributed without         ////
//// restriction provided that this copyright statement is not    ////
//// removed from the file and that any derivative work contains  ////
//// the original copyright notice and the associated disclaimer. ////
////                                                              ////
//// This source file is free software; you can redistribute it   ////
//// and/or modify it under the terms of the GNU Lesser General   ////
//// Public License as published by the Free Software Foundation; ////
//// either version 2.1 of the License, or (at your option) any   ////
//// later version.                                               ////
////                                                              ////
//// This source is distributed in the hope that it will be       ////
//// useful, but WITHOUT ANY WARRANTY; without even the implied   ////
//// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR      ////
//// PURPOSE.  See the GNU Lesser General Public License for more ////
//// details.                                                     ////
////                                                              ////
//// You should have received a copy of the GNU Lesser General    ////
//// Public License along with this source; if not, download it   ////
//// from http://www.opencores.org/lgpl.shtml                     ////
////                                                              ////
//////////////////////////////////////////////////////////////////////



/*
	Use this to tell sycamore how to populate the Device ROM table
	so that users can interact with your slave

	META DATA

	identification of your device 0 - 65536
	DRT_ID:  4

	flags (read drt.txt in the slave/device_rom_table directory 1 means
	a standard device
	DRT_FLAGS:  1

	parameters
	DRT_SIZE:  12

*/

`include "project_defines.v"
`include "spi_defines.v"
`include "timescale.v"

module wb_spi (
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

  ss_pad_o,
  sclk_pad_o,
  mosi_pad_o,
  miso_pad_i
);


input 				                    clk;
input 				                    rst;

//wishbone slave signals
input 				                    wbs_we_i;
input 				                    wbs_stb_i;
input 				                    wbs_cyc_i;
input		        [3:0]	            wbs_sel_i;
input		        [31:0]	          wbs_adr_i;
input  		      [31:0]	          wbs_dat_i;
output reg      [31:0]	          wbs_dat_o;
output reg			                  wbs_ack_o;
output reg			                  wbs_int_o;

// SPI signals                                     
output          [`SPI_SS_NB-1:0]  ss_pad_o;         // slave select
output                            sclk_pad_o;       // serial clock
output                            mosi_pad_o;       // master out slave in
input                             miso_pad_i;       // master in slave out
                                               
// Internal signals
reg       [`SPI_DIVIDER_LEN-1:0] divider;          // Divider register
reg       [`SPI_CTRL_BIT_NB-1:0] ctrl;             // Control and status register
reg             [`SPI_SS_NB-1:0] ss;               // Slave select register
reg                     [32-1:0] wbs_dat;           // wb data out
wire         [`SPI_MAX_CHAR-1:0] rx;               // Rx register
wire                             rx_negedge;       // miso is sampled on negative edge
wire                             tx_negedge;       // mosi is driven on negative edge
wire    [`SPI_CHAR_LEN_BITS-1:0] char_len;         // char len
wire                             go;               // go
wire                             lsb;              // lsb first on line
wire                             ie;               // interrupt enable
wire                             ass;              // automatic slave select
wire                             spi_divider_sel;  // divider register select
wire                             spi_ctrl_sel;     // ctrl register select
wire                       [3:0] spi_tx_sel;       // tx_l register select
wire                             spi_ss_sel;       // ss register select
wire                             tip;              // transfer in progress
wire                             pos_edge;         // recognize posedge of sclk
wire                             neg_edge;         // recognize negedge of sclk
wire                             last_bit;         // marks last character bit
  


parameter SPI_CTRL        = 4'h0;
parameter SPI_CLOCK_RATE  = 4'h1;
parameter SPI_DIVIDER     = 4'h2;
parameter SPI_SS          = 4'h3;
parameter SPI_RX_0        = 4'h4;
parameter SPI_RX_1        = 4'h5;
parameter SPI_RX_2        = 4'h6;
parameter SPI_RX_3        = 4'h7;
parameter SPI_TX_0        = 4'h8;
parameter SPI_TX_1        = 4'h9;
parameter SPI_TX_2        = 4'hA;
parameter SPI_TX_3        = 4'hB;

// Address decoder
assign spi_tx_sel[0]   = wbs_cyc_i & wbs_stb_i & wbs_we_i & (wbs_adr_i[3:0] == SPI_TX_0);
assign spi_tx_sel[1]   = wbs_cyc_i & wbs_stb_i & wbs_we_i & (wbs_adr_i[3:0] == SPI_TX_1);
assign spi_tx_sel[2]   = wbs_cyc_i & wbs_stb_i & wbs_we_i & (wbs_adr_i[3:0] == SPI_TX_2);
assign spi_tx_sel[3]   = wbs_cyc_i & wbs_stb_i & wbs_we_i & (wbs_adr_i[3:0] == SPI_TX_3);
 

always @ (posedge clk) begin
	if (rst) begin
		wbs_dat_o	        <=  32'h00000000;
		wbs_ack_o	        <=  0;
    ctrl              <=  0;
    divider           <=  100;
    ss                <=  0;
	end

	else begin
    //interrupts
    if (ie && tip && last_bit && pos_edge) begin
      wbs_int_o   <=  1;
    end
    else if (wbs_ack_o) begin
      wbs_int_o   <=  0;
    end
		//when the master acks our ack, then put our ack down
		if (wbs_ack_o & ~ wbs_stb_i)begin
			wbs_ack_o   <= 0;
		end
    
    if (go && last_bit && pos_edge) begin
      ctrl[8]     <=  0;

    end
    
		if (wbs_stb_i & wbs_cyc_i) begin
			//master is requesting somethign
			if (wbs_we_i && !tip) begin
				//write request
				case (wbs_adr_i) 
					SPI_CTRL: begin
            ctrl      <=  wbs_dat_i[15:0];
					end
					SPI_DIVIDER: begin
            divider <=  wbs_dat_i[31:0];
					end
					SPI_SS: begin
            ss      <=  wbs_dat_i[`SPI_SS_NB - 1: 0];
					end
					default: begin
					end
				endcase
			end

			else begin 
				//read request
				case (wbs_adr_i)
					SPI_RX_0: begin
            wbs_dat_o <= rx[31:0];
					end
					SPI_RX_1: begin
            wbs_dat_o <= rx[63:32];
					end
					SPI_RX_2: begin
            wbs_dat_o <= rx[95:64];
					end
					SPI_RX_3: begin
            wbs_dat_o <= rx[`SPI_MAX_CHAR-1:96];
					end
					SPI_CTRL: begin
            wbs_dat_o <= {{32-`SPI_CTRL_BIT_NB{1'b0}}, ctrl};
					end
					SPI_DIVIDER: begin
            wbs_dat_o <=  divider;
					end
					SPI_SS: begin
            wbs_dat_o <= {{32-`SPI_SS_NB{1'b0}}, ss};
					end
          SPI_CLOCK_RATE: begin
            wbs_dat_o <= `CLOCK_RATE; 
          end
					default: begin
            //user should write here
            wbs_dat_o <= 32'bx;
					end
				endcase
			end
			wbs_ack_o <= 1;
		end
	end
end

 
assign rx_negedge = ctrl[`SPI_CTRL_RX_NEGEDGE];
assign tx_negedge = ctrl[`SPI_CTRL_TX_NEGEDGE];
assign go         = ctrl[`SPI_CTRL_GO];
assign char_len   = ctrl[`SPI_CTRL_CHAR_LEN];
assign lsb        = ctrl[`SPI_CTRL_LSB];
assign ie         = ctrl[`SPI_CTRL_IE];
assign ass        = ctrl[`SPI_CTRL_ASS];
 
assign ss_pad_o = ~((ss & {`SPI_SS_NB{tip & ass}}) | (ss & {`SPI_SS_NB{!ass}}));

spi_clgen clgen (
  .clk_in(clk), 
  .rst(rst), 
  .go(go), 
  .enable(tip), 
  .last_clk(last_bit),
  .divider(divider), 
  .clk_out(sclk_pad_o), 
  .pos_edge(pos_edge), 
  .neg_edge(neg_edge)
);
  
spi_shift shift (
  .clk(clk), 
  .rst(rst), 
  .len(char_len[`SPI_CHAR_LEN_BITS - 1:0]),
  .latch(spi_tx_sel[3:0]), 
  .byte_sel(4'hF), 
  .lsb(lsb), 
  .go(go), 
  .pos_edge(pos_edge), 
  .neg_edge(neg_edge), 
  .rx_negedge(rx_negedge), 
  .tx_negedge(tx_negedge),
  .tip(tip), 
  .last(last_bit), 
  .p_in(wbs_dat_i), 
  .p_out(rx), 
  .s_clk(sclk_pad_o), 
  .s_in(miso_pad_i), 
  .s_out(mosi_pad_o)
);
endmodule
  
