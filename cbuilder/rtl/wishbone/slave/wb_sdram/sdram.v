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

`timescale 1 ns/100 ps
`include "sdram_include.v"


module sdram (
  clk,
  rst,

  app_write_pulse,
  app_write_data,
  app_write_mask,
  write_fifo_full,

  app_read_pulse,
  app_read_data,
  read_fifo_empty,

  //Wishbone command
  sdram_ready,

  app_write_enable,
  app_read_enable,
  app_address,

  sd_clk,
  cs_n,
  cke,
  ras,
  cas,
  we,

  address,
  bank,
  data,
  data_mask
);

input         clk;
input         rst;

input         app_write_pulse;
input [31:0]  app_write_data;
input [3:0]   app_write_mask;
output        write_fifo_full;

input         app_read_pulse;
output [31:0] app_read_data;
output        read_fifo_empty;

input         app_write_enable;
input         app_read_enable;

input [21:0]  app_address;
output reg    sdram_ready;

output        sd_clk;
output reg    cke;
output reg    cs_n;
output        ras;
output        cas;
output        we;

output      [11:0]  address;
output      [1:0]   bank;
inout       [15:0]  data;
output      [1:0]   data_mask;


wire          sdram_clock_ready;
wire          sdram_clk;

//Generate the SDRAM Clock
sdram_clkgen clkgen (
  .clk (clk),
  .rst (rst),

  .locked(sdram_clock_ready),
  .out_clk(sdram_clk),
  .phy_out_clk(sd_clk)
);


//setup the cke
always @(posedge clk) begin
  if (rst || ~sdram_clock_ready) begin
    cke <= 0;
  end
  else begin
    if (sdram_clock_ready) begin
      cke <=  1;
    end
  end
end

reg           refresh_ack;
reg           refresh;

//Write path
wire  [2:0]   write_command;
wire  [11:0]  write_address;
wire  [1:0]   write_bank;
wire          write_idle;
wire  [1:0]   write_data_mask;
wire  [35:0]  write_path_data;
reg           write_enable;
wire  [15:0]  data_out;

wire          writing;
wire          write_fifo_empty;
assign        writing = ~write_idle;


//Write FIFO
afifo 
	#(		.DATA_WIDTH(36),
			.ADDRESS_WIDTH(8)
	)
fifo_wr (
	.rst(rst || ~sdram_ready),

  //Clocks
	.din_clk(clk),
	.dout_clk(sdram_clk),

  //Data
	.data_in({app_write_mask, app_write_data}),
	.data_out(write_path_data),

  //Status
	.full(write_fifo_full),
	.empty(write_fifo_empty),

  //Commands
	.wr_en(app_write_pulse),
	.rd_en(write_path_read_pulse)
);

sdram_write write_path (
  .rst(rst || ~sdram_ready),
  .clk(sdram_clk),

  //Write Path SDRAM Control
  .command(write_command),
  .address(write_address),
  .bank(write_bank),
  .data_out(data_out),
  .data_mask(write_data_mask),

  //Control
  .idle(write_idle),
  .enable(app_write_enable),
  .auto_refresh(refresh),
  
  //Application address
  .app_address(app_address),

  //Data Out Path
  .fifo_data(write_path_data),
  .fifo_read(write_path_read_pulse),
  .fifo_empty(write_fifo_empty)

);

//Read path
wire  [2:0]   read_command;
wire          read_idle;
reg           read_fifo_reset;
wire  [11:0]  read_address;
wire  [1:0]   read_bank;
wire  [31:0]  read_path_data;
//reg           read_enable;

wire  [15:0]  data_in;
assign        data_in = data;

wire          reading;
assign        reading = ~read_idle;

//instantiate the read fifo (32 bits)
afifo 
	#(		.DATA_WIDTH(32),
			.ADDRESS_WIDTH(8)
	)
fifo_rd (
	.rst(~app_read_enable),

  //Clocks
	.din_clk(sdram_clk),
	.dout_clk(clk),

  //Data
	.data_in(read_path_data),
	.data_out(app_read_data),

  //Status
	.full(read_fifo_full),
	.empty(read_fifo_empty),

  //Commands
	.wr_en(read_path_write_pulse),
	.rd_en(app_read_pulse)
);


sdram_read read_path (
  .rst(rst || ~sdram_ready),
  .clk(sdram_clk),

  //Read Path SDRAM Control
  .command(read_command),
  .address(read_address),
  .bank(read_bank),
  .data_in(data_in),

  //Control
  .enable(app_read_enable),
  .idle(read_idle),
  .auto_refresh(refresh),

  //application address
  .app_address(app_address),

  //Data In Path
  .fifo_data(read_path_data),
  .fifo_write(read_path_write_pulse),
  .fifo_full(read_fifo_full)
);

//Initialization Write Path
reg   [2:0]   init_command;
reg   [11:0]  init_address;
reg   [1:0]   init_bank;

wire  [2:0]   command;

//Combine all the ras/cas/we
assign command  = ~write_idle ? write_command : ~read_idle ? read_command : init_command;
assign ras  = command[2];
assign cas  = command[1];
assign we   = command[0];
assign bank = ~write_idle ? write_bank : ~read_idle ? read_bank : init_bank;
assign address  = ~write_idle ? write_address : ~read_idle ? read_address : init_address;

//XXX: Disable Data mask for testing
//assign data_mask = ~write_idle ? write_data_mask : 2'b00; 
assign data_mask = 2'b00;

//Attach the tristate Data to an in and out

assign        data = writing ? data_out : 16'hZZZZ;

parameter     START               = 4'h0;
parameter     PRECHARGE           = 4'h1;
parameter     AUTO_REFRESH1       = 4'h2;
parameter     AUTO_REFRESH2       = 4'h3;
parameter     LOAD_MODE_REGISTER  = 4'h4;
parameter     IDLE                = 4'h5;
parameter     READING             = 4'h6;
parameter     WRITING             = 4'h7;
parameter     AUTO_REFRESH_PRE    = 4'h8;
parameter     AUTO_REFRESH        = 4'h9;



//General Registers
reg   [3:0]   state;
reg   [15:0]  delay;

always @(posedge sdram_clk) begin

  read_fifo_reset           <=  0;
  refresh_ack               <=  0;
  init_bank                 <=  2'b00;

  if (rst || ~cke) begin
    //either the whole device is in reset or the DCM is not settled
    state                   <=  START;
    delay                   <=  16'h0;
    cs_n                    <=  1;
    init_command            <=  `SDRAM_CMD_NOP;
    init_bank               <=  2'b00;
    init_address            <=  12'h000;
    sdram_ready             <=  0;
//    read_enable             <=  0;
    write_enable            <=  0;
    read_fifo_reset         <=  1;
  end
  else begin
    
    if (delay > 0) begin
      init_command          <=  `SDRAM_CMD_NOP;
      delay                 <=  delay - 1;
    end
    else begin
      case (state)
        START: begin
          //$display ("SDRAM_INIT: START Initialization");
          //wait for the PLL to settle
          delay             <=  `T_PLL;
          state             <=  PRECHARGE;
        end
        PRECHARGE: begin
          //$display ("SDRAM_INIT: PRECHARGE");
          cs_n              <=  0;
          init_command      <=  `SDRAM_CMD_PRE; 
          init_address[10]  <=  1;
          delay             <=  `T_RP;
          state             <=  AUTO_REFRESH1;
          init_bank         <=  2'b11;
        end
        AUTO_REFRESH1: begin
          //$display ("SDRAM_INIT: AUTO_REFRESH1");
          init_command      <=  `SDRAM_CMD_AR;
          delay             <=  `T_RFC;
          state             <=  AUTO_REFRESH2;
        end
        AUTO_REFRESH2: begin
          //$display ("SDRAM_INIT: AUTO_REFRESH2");
          init_command      <=  `SDRAM_CMD_AR;
          delay             <=  `T_RFC;
          state             <=  LOAD_MODE_REGISTER;
        end
        LOAD_MODE_REGISTER: begin
          //$display ("SDRAM_INIT: LOAD_MODE_REGISTER");
          init_command      <=  `SDRAM_CMD_MRS;
          delay             <=  `T_MRD;
          init_address      <=  `SDRAM_INIT_LMR;
          state             <=  IDLE;
        end
        IDLE: begin
          sdram_ready       <=  1;
          //the write/read path are disabled until the app calls write/read in this state
          write_enable      <=  0;
//          read_enable       <=  0;
          read_fifo_reset   <=  1;
          //waiting for user to initiate a command
          if (refresh) begin
            //$display ("SDRAM_INIT: Auto Refresh");
            //init_bank       <=  2'b11;
            state           <=  AUTO_REFRESH_PRE;
          end
          //if the user starts a write enable the write path
          if (app_write_enable) begin
            //$display ("SDRAM_INIT: write initiated");
            state           <=  WRITING;
            write_enable    <=  1;
          end
          //if the user starts a read enable the read path
          if (app_read_enable) begin
            //$display ("SDRAM_INIT: read initiated");
            state           <=  READING;
            //get rid of any data that is in the read FIFO
//            read_enable     <=  1;
            read_fifo_reset <=  0;
          end
        end
        READING: begin
          if (read_idle && ~app_read_enable) begin
            state <=  IDLE;
          end
        end
        WRITING: begin
          if (write_idle && ~app_write_enable) begin
            state <=  IDLE;
          end
        end
        AUTO_REFRESH_PRE: begin
          init_command    <= `SDRAM_CMD_PRE;
          init_address[10]<=  1;
          state           <= AUTO_REFRESH;
          delay           <= `T_RP; 
        end
        AUTO_REFRESH: begin
          init_command    <= `SDRAM_CMD_AR;
          state           <=  IDLE;
          delay           <=  `T_RFC;
          refresh_ack     <=  1;

        end

        default: begin
          //$display ("Shouldn't be here");
          state <=  START;
        end
      endcase
    end
  end
end


//auto refresh master timeout
reg   [31:0]  auto_refresh_count;

always @(posedge sdram_clk) begin
  if (rst || ~sdram_ready) begin
    auto_refresh_count  <=  `T_AR_TIMEOUT;
    refresh <=  0;
  end
  else begin
    if (refresh_ack || ~sdram_ready) begin
      refresh <= 0;
    end
    if (auto_refresh_count > 0) begin
      auto_refresh_count  <= auto_refresh_count - 1;
    end
    else begin
      auto_refresh_count  <= `T_AR_TIMEOUT;
      refresh             <= 1;
    end
  end
end


endmodule
