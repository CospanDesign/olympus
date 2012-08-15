//UART Controller
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
  07/08/2012
    -Initial Commit

  07/30/2012
    -Attached Flow control for CTS RTS
    -Removed DTR DSR for this initial version
*/

`timescale 1 ns/100 ps

//Control Flag Defines
`define CONTROL_RESET         0
`define CONTROL_SET_BAUDRATE  1
`define CONTROL_FC_CTS_RTS    2
//XXX: Flow Control Flags

//Status Flag Defines
`define STATUS_RX_AVAILABLE   0
`define STATUS_TX_READY       1
`define STATUS_RX_FULL        2
`define STATUS_RX_ERROR       3
`define STATUS_FC_ERROR       4

module uart_controller (
  clk,
  rst,

  rx,
  tx,

  cts,
  rts,

  control,
  status,

  prescaler,

  write_pulse,
  write_data,
  write_fifo_full,

  read_pulse,
  read_fifo_empty,
  read_data
);


input               clk;
input               rst;

input               rx;
output              tx;

//I need to verify flow control is correct
output  reg         cts;
input               rts;

input [7:0]         control;
output reg [7:0]    status;

input [31:0]        prescaler;

input               write_pulse;
input [7:0]         write_data;
output              write_fifo_full;

output [7:0]        read_data;
input               read_pulse;
output              read_fifo_empty;


//FIFO Registers
reg                 write_fifo_read_pulse;
reg                 read_fifo_write_pulse;


reg                 transmit;
wire [7:0]          tx_byte;
wire                received;
wire [7:0]          rx_byte;

wire                is_receiving;
wire                is_transmitting;

wire                rx_error;

reg                 local_read;


//Write FIFO
afifo #(
  .DATA_WIDTH(8),
  .ADDRESS_WIDTH(8) //256 byte FIFO
  )
  fifo_wr (
    .rst(rst),

    //Clocks
    .din_clk(clk),
    .dout_clk(clk),

    //Data
    .data_in(write_data),
    .data_out(tx_byte),

    //Status
    .full(write_fifo_full),
    .empty(write_fifo_empty),

    //commands
    .wr_en(write_pulse),
    .rd_en(write_fifo_read_pulse)
);

//Read FIFO
afifo #(
  .DATA_WIDTH(8),
  .ADDRESS_WIDTH(8)
  )
  fifo_rd(
    .rst(rst),

    //Clocks
    .din_clk(clk),
    .dout_clk(clk),

    //Data
    .data_in(rx_byte),
    .data_out(read_data),

    //Status
    .full(read_fifo_full),
    .empty(read_fifo_empty),

    //Commands
    .wr_en(read_fifo_write_pulse),
    .rd_en(read_pulse || local_read)
);

//Low Level UART
uart u (
  .clk(clk),
  .rst(rst),
  .rx(rx),
  .tx(tx),
  .transmit(transmit),
  .tx_byte(tx_byte),
  .received(received),
  .rx_byte(rx_byte),
  .is_receiving(is_receiving),
  .is_transmitting(is_transmitting),
  .rx_error(rx_error)
);


parameter     IDLE  = 3'h0;
parameter     SEND  = 3'h1;
parameter     READ  = 3'h2;

wire          flowcontrol;
assign        flowcontrol = control[`CONTROL_FC_CTS_RTS];

reg [3:0]     state;

reg           test;


always @ (posedge clk) begin
  if (rst) begin
    cts                         <=  0;
    state                       <=  IDLE;
    write_fifo_read_pulse       <=  0;
    read_fifo_write_pulse       <=  0;
    local_read                  <=  0;


    test                        <=  0;
  end
  else begin
    write_fifo_read_pulse       <=  0; 
    read_fifo_write_pulse       <=  0;
    transmit                    <=  0;
    local_read                  <=  0;

    //transmitting
    if (!write_fifo_empty && ! is_transmitting) begin
      if (flowcontrol) begin
        if (control[`CONTROL_FC_CTS_RTS]) begin
          //tell the remote device that we have data to send
          if (~cts) begin
            //device is ready to receive data
            transmit         <=  1; 
          end
        end
        //here is where DTR DSR can be put in
      end
      else begin
        transmit            <=  1;
      end
    end


    if (read_fifo_full && control[`CONTROL_FC_CTS_RTS]) begin
      cts                   <=  1;
    end

    //Check the remote side for receive data
    if (received && !read_fifo_full) begin
      read_fifo_write_pulse   <=  1;
    end
    else if (received && read_fifo_full) begin
//X: the user will pull this line low
      local_read  <=  1;
    end
  end
end

endmodule
