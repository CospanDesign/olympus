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
`define CONTROL_RESET           0
`define CONTROL_FC_CTS_RTS      1
//XXX: Flow Control Flags
`define CONTROL_READ_INTERRUPT  2
`define CONTROL_WRITE_INTERRUPT 3

//Status Flag Defines
`define STATUS_RX_AVAILABLE     0
`define STATUS_TX_READY         1
`define STATUS_RX_FULL          2
`define STATUS_RX_ERROR         3
`define STATUS_FC_ERROR         4

`define PRESCALER_DIV           8

module uart_controller (
  clk,
  rst,

  rx,
  tx,

  cts,
  rts,

  control,
  status,
  status_reset,

  prescaler,
  set_clock_div,
  clock_div,
  default_clock_div,

  write_strobe,
  write_strobe_count,
  write_data0,
  write_data1,
  write_data2,
  write_data3,

  write_full,
  write_available,
  write_size,

  read_strobe,
  read_empty,
  read_data,
  read_count,
  read_size
);


input               clk;
input               rst;

input               rx;
output              tx;

//I need to verify flow control is correct
output  reg         cts;
input               rts;

input       [7:0]   control;
output reg  [7:0]   status;
input               status_reset;

output      [31:0]  prescaler;
input               set_clock_div;
input       [31:0]  clock_div;
output      [31:0]  default_clock_div;

input               write_strobe;
input       [3:0]   write_strobe_count;
input       [7:0]   write_data0;
input       [7:0]   write_data1;
input       [7:0]   write_data2;
input       [7:0]   write_data3;

output              write_full;
output      [31:0]  write_available;
output wire [31:0]  write_size;

output      [7:0]   read_data;
input               read_strobe;
output              read_empty;
output wire [31:0]  read_count;
output wire [31:0]  read_size;


//FIFO Registers
reg         [7:0]   write_fifo[0:255];
reg         [7:0]   read_fifo[0:255];


reg                 write_fifo_read_strobe;
wire        [31:0]  tx_read_count;

reg                 read_fifo_write_strobe;
wire        [31:0]  rx_fifo_size;
wire        [31:0]  rx_write_available;


//UART Core
reg                 transmit;
wire  [7:0]         tx_byte;
wire                received;
wire  [7:0]         rx_byte;

wire                is_receiving;
wire                is_transmitting;

wire                rx_error;

reg                 local_read;
wire                flowcontrol;
reg [3:0]           state;
reg                 test;


//STATUS FLAGs
reg                 write_overflow;
reg                 write_underflow;

reg                 read_overflow;
reg                 read_underflow;



uart_fifo uf_tx (
  .clk(clk),
  .rst(rst),

  .size(write_size),
  
  .write_strobe(write_strobe),
  .write_strobe_count(write_strobe_count),
  .write_available(write_available),
  .write_data0(write_data0),
  .write_data1(write_data1),
  .write_data2(write_data2),
  .write_data3(write_data3),

  .read_strobe(tx_read_strobe),
  .read_count(tx_read_count),
  .read_data(tx_byte),
  .overflow(tx_overflow),
  .underflow(tx_underflow),
  .full(tx_full),
  .empty(tx_empty)
);

uart_fifo uf_rx (
  .clk(clk),
  .rst(rst),
  
  .size(rx_fifo_size),

  .write_strobe(rx_write_strobe),
  .write_strobe_count(1), //always putting in 1 byte
  .write_available(rx_write_available),
  .write_data0(rx_byte),
  
  .read_strobe(received),
  .read_count(read_count),
  .read_data(read_data),
  .overflow(rx_overflow),
  .underflow(rx_underflow),
  .full(rx_full),
  .empty(rx_empty)
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
  .rx_error(rx_error),
  .set_clock_div(set_clock_div),
  .user_clock_div(clock_div),
  .default_clock_div(default_clock_div)
);


parameter     IDLE  = 3'h0;
parameter     SEND  = 3'h1;
parameter     READ  = 3'h2;


//asynchronous logic

assign        flowcontrol       = control[`CONTROL_FC_CTS_RTS];
assign        prescaler         = `CLOCK_RATE / `PRESCALER_DIV;


//synchronous logic

//main control state machine
always @ (posedge clk) begin
  if (rst) begin
    cts                           <=  0;
    state                         <=  IDLE;
    write_fifo_read_strobe        <=  0;
    read_fifo_write_strobe        <=  0;
    local_read                    <=  0;
    test                          <=  0;
    status                        <=  0;
  end
  else begin
    write_fifo_read_strobe        <=  0; 
    read_fifo_write_strobe        <=  0;
    transmit                      <=  0;
    local_read                    <=  0;
    cts                           <=  0;


    if (status_reset) begin
      //reset status flags
    end

    //transmitting
    if (!tx_empty && ! is_transmitting) begin
      if (flowcontrol) begin
        if (control[`CONTROL_FC_CTS_RTS]) begin
          //tell the remote device that we have data to send
          if (~rts) begin
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

    if (rx_full && control[`CONTROL_FC_CTS_RTS]) begin
      cts                   <=  1;
    end
  end
end

endmodule
