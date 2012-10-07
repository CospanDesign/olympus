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

module sdram_write (
  rst,
  clk,

  command,  
  address,
  bank,
  data_out,
  data_mask,

  idle,
  enable,
  auto_refresh,
  wait_for_refresh,
  
  app_address,

  fifo_data,
  fifo_read,
  fifo_ready,
  fifo_activate,
  fifo_size
);

input               rst;
input               clk;

//RAM control
output  reg [2:0]   command;
output  reg [11:0]  address;
output  reg [1:0]   bank;
output  reg [15:0]  data_out;
output  reg [1:0]   data_mask;

//sdram controller
output              idle;
input               enable;
input       [21:0]  app_address;
input               auto_refresh;
output  reg         wait_for_refresh;

//FIFO
input       [35:0]  fifo_data;
output  reg         fifo_read;
input               fifo_ready;
output  reg         fifo_activate;
input       [23:0]  fifo_size;

parameter           IDLE            = 4'h0;
parameter           WAIT            = 4'h1;
parameter           ACTIVATE        = 4'h2;
parameter           WRITE_COMMAND   = 4'h3;
parameter           WRITE_TOP       = 4'h4;
parameter           WRITE_BOTTOM    = 4'h5;
parameter           BURST_TERMINATE = 4'h6;
parameter           PRECHARGE       = 4'h7;

reg                 empty;

reg     [3:0]       state;
reg     [15:0]      delay;

//this address gets latched in when the user initiates a write
reg		  [21:0]			write_address;

wire    [11:0]      row;
wire    [7:0]       column;
wire                continue_writing;
reg     [23:0]      fifo_count;

//assign  bank    =   write_address[21:20];
assign  row     =   write_address[19:8];
assign  column  =   write_address[7:0]; //4 Byte Boundary


//assign idle
assign  idle    =   ((delay == 0) && ((state == IDLE) || (state == WAIT)));


always @(posedge clk) begin
  //Always reset FIFO Read
  fifo_read <=  0;

  if (rst) begin
    command           <=  `SDRAM_CMD_NOP;
    state             <=  IDLE;
    delay             <=  0;
    write_address     <=  22'h000000;
    bank              <=  2'b00;
    data_out          <=  16'h0000;
    data_mask         <=  2'b0;
    address           <=  12'h000;
    wait_for_refresh  <=  0;
    empty             <=  0;
    fifo_count        <=  0;

  end
  else begin
/*
    if (fifo_activate == 0) begin
      fifo_count  <=  0;
    end
*/
    data_out  <=  16'h0000;
    wait_for_refresh  <=  0;
    if (delay > 0) begin
      command     <=  `SDRAM_CMD_NOP;
      delay       <=  delay - 1;
    end
    else begin
      case (state)
        IDLE: begin
          //data_out      <=  16'hZZZZ;
          if (enable && fifo_ready) begin
            //$display ("SDRAM WRITE: IDLE New Data!");
            state           <=  WAIT;
            write_address   <=  app_address;
            fifo_count      <=  fifo_size - 1;
            fifo_activate   <=  1;
          end
          wait_for_refresh  <=  1;
        end
        WAIT: begin
          if (auto_refresh) begin
            wait_for_refresh  <=  1;
          end
          else begin
            if ((fifo_count == 0) && ~enable) begin
              state         <=  IDLE;
              fifo_activate <=  0;
            end
            else begin
              state <=  ACTIVATE;
            end
          end
        end
        ACTIVATE: begin
          //$display ("SDRAM_WRITE: ACTIVATE ROW %h", row);
          if (auto_refresh) begin
            state <=  WAIT;
          end
          else begin
            command       <=  `SDRAM_CMD_ACT;
            delay         <=  `T_RCD;
            bank          <=  write_address[21:20];
            address       <=  row;
            state         <=  WRITE_COMMAND;
//XXX: the FIFO data is already available
            //fifo_read     <=  1;
          end
        end
        WRITE_COMMAND: begin
          //$display ("SDRAM_WRITE: Issue the write command");
          empty         <=  0;
          command       <=  `SDRAM_CMD_WRITE;
          address       <=  {4'b0000, column};
          data_out      <=  fifo_data[31:16];     
          data_mask     <=  fifo_data[35:34];
          state         <=  WRITE_BOTTOM;
          write_address <=  write_address + 2;
          //increment our local version of the address
          //if (fifo_empty) begin
          //  empty       <=  1;
          //end

        end
        WRITE_TOP: begin
          empty         <=  0;
          command       <=  `SDRAM_CMD_NOP;
          data_out      <=  fifo_data[31:16];     
          data_mask     <=  fifo_data[35:34];
          state         <=  WRITE_BOTTOM;
          write_address <=  write_address + 2;
          //if (fifo_empty) begin
          //  empty       <=  1;
          //end
        end
        WRITE_BOTTOM: begin
          command       <=  `SDRAM_CMD_NOP;
          data_out      <=  fifo_data[15:0];
          data_mask     <=  fifo_data[33:32];
          //if there is more data to write then continue on with the write
          //and issue a command to the AFIFO to grab more data
          if (fifo_count == 0) begin
            //we could have reached the end of a row here
            state         <=  BURST_TERMINATE;
          end
          else if ((write_address[7:0] == 8'h00) || auto_refresh) begin
            //the fifo count != 0 so get the next peice of data
            fifo_read     <=  1;
            state         <=  BURST_TERMINATE;
          end
          else begin
            state         <=  WRITE_TOP;
            fifo_read     <=  1;
          end
        end
        BURST_TERMINATE: begin
          command       <=  `SDRAM_CMD_TERM;
          delay         <=  `T_WR;
          state         <=  PRECHARGE;
        end
        PRECHARGE: begin
          command       <=  `SDRAM_CMD_PRE;
          delay         <=  `T_RP;
          state         <=  WAIT;
        end
        default: begin
          //$display ("SDRAM_WRITE: Shouldn't have gotten here");
          state <=  IDLE;
        end
      endcase
    end
  end
end


endmodule
