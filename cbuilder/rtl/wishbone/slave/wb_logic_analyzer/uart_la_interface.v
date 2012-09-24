/*
Distributed under the MIT license.
Copyright (c) 2012 Dave McCoy (dave.mccoy@cospandesign.com)

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

`include "logic_analyzer_defines.v"

module uart_la_interface (
  rst,
  clk,

  //logic analyzer control
  trigger,
  trigger_mask,
  trigger_after,
  repeat_count,
  set_strobe,
  enable,
  finished,

  //data interface
  data_read_strobe,
  data_read_size,
  data,

  phy_rx,
  phy_tx

);

input                       rst;
input                       clk;
                           
output reg  [31:0]          trigger;
output reg  [31:0]          repeat_count;
output reg  [31:0]          trigger_mask;
output reg  [31:0]          trigger_after;
output reg                  set_strobe;
output reg                  enable;
input                       finished;
                           
input       [31:0]          data_read_size;
output reg                  data_read_strobe;
input       [31:0]          data;
                           
input                       phy_rx;
output                      phy_tx;




parameter                   IDLE                  = 0;
parameter                   READ_COMMAND          = 1;
parameter                   READ_ENABLE_SET       = 2;
parameter                   READ_TRIGGER          = 3;
parameter                   READ_TRIGGER_MASK     = 4;
parameter                   READ_TRIGGER_AFTER    = 5;
parameter                   READ_REPEAT_COUNT     = 6;
parameter                   SEND_RESPONSE         = 7;

//UART Control
reg                         write_strobe;
wire                        write_full;
wire  [31:0]                write_available;
reg   [7:0]                 write_data;
wire  [31:0]                write_size;

wire                        read_overflow;
reg                         read_strobe;
wire                        read_empty;
wire  [31:0]                read_size;
wire  [7:0]                 read_data;
wire  [31:0]                uart_read_count;

//Register/Wires
reg                         ready;
reg   [3:0]                 read_state;
reg   [3:0]                 write_state;

reg                         write_status;
reg                         status_written;

reg   [7:0]                 command_response;
reg   [7:0]                 response_status;
reg                         process_byte;
reg   [31:0]                read_count;

reg   [31:0]                la_data_read_count;
reg   [31:0]                la_data;
reg   [1:0]                 byte_count;

wire  [3:0]                 nibble;

//reg   [3:0]                 read_history;
//reg                         reset;

//submodules
uart_controller uc (
  .clk(clk),
  //should this be reset here?
  .rst(rst),
  .rx(la_uart_rx),
  .tx(la_uart_tx),
  .rts(0),
  
  .control_reset(rst),
  .cts_rts_flowcontrol(0),
  .read_overflow(read_overflow),
  .set_clock_div(0),
  .clock_div(0),

  //Data in
  .write_strobe(write_strobe),
  .write_data(write_data),
  .write_full(write_full),
  .write_available(write_available),
  .write_size(write_size),

  //Data Out
  .read_strobe(read_strobe),
  .read_data(read_data),
  .read_empty(read_empty),
  .read_count(uart_read_count),
  .read_size(read_size)
);


//asynchronous logic
assign nibble         = decode_ascii(read_data); 

//extended reset logic
/*
always @ (posedge clk) begin
  if (rst) begin
    reset                   <=  0;
    read_history            <=  0;
  end
  else begin
    reset                   <=  0;

    if (read_history == 4'b0111) begin
      reset                 <=  1;
    end
    read_history            <=  {read_history[2:0], 1'h1};
  end
end
*/

//UART Interface Controller
always @ (posedge clk) begin
  if (rst) begin
    read_strobe             <=  0;
    trigger                 <=  0;
    repeat_count            <=  0;
    trigger_mask            <=  0;
    trigger_after           <=  0;
    set_strobe              <=  0;
    enable                  <=  0;

    ready                   <=  0;
    read_state                   <=  IDLE;

    command_response        <=  0;
    response_status         <=  0;

    write_status            <=  0;
  end
  else begin


    //read commands from the host computer
    read_strobe             <=  0;
    process_byte            <=  0;
    write_status            <=  0;

    if (ready && !read_empty) begin
      //new command data to process
      read_strobe       <=  1;
      ready             <=  0;
    end
    if (read_strobe) begin
      process_byte      <=  1;
    end

    //check if incomming UART is not empty
    case (read_state)
      IDLE: begin
        ready               <=  1;
        response_status     <=  0;
        if (process_byte) begin
          if (read_data != `START_ID) begin
            $display ("Start ID not found");
            read_state             <=  IDLE;
          end
          else begin
            $display ("Start ID Found!");
            read_state            <=  READ_COMMAND;
            ready                 <=  1;
          end
        end
      end
      READ_COMMAND: begin
        if (process_byte) begin
          case (read_data)
            `LA_PING: begin
              ready               <=  0;
              command_response    <=  `RESPONSE_SUCCESS; 
              read_state          <=  SEND_RESPONSE;
            end
            `LA_WRITE_SETTINGS: begin
              //disable the LA when updating settings
              $display("ULA: Write settings (Disable LA)");
              enable              <=  0;
              read_state          <=  READ_TRIGGER;
              read_count          <=  7;
            end
            `LA_SET_ENABLE: begin
              read_state          <=  READ_ENABLE_SET; 
            end
            `LA_GET_ENABLE: begin
              ready               <=  0;
              read_state          <=  SEND_RESPONSE;
              response_status     <=  enable + `HEX_0;
            end
            default: begin
              //unrecognized command
              ready               <=  0;
              command_response    <=  `RESPONSE_FAIL;
              read_state          <=  SEND_RESPONSE;
            end
          endcase
        end
      end
      READ_TRIGGER: begin
        if (process_byte) begin
          trigger                 <=  {trigger[27:0], nibble}; 
          read_count              <=  read_count -  1;
          if (read_count == 0) begin
            read_count            <=  7;
            read_state            <=  READ_TRIGGER_MASK;
          end
        end
      end
      READ_TRIGGER_MASK: begin
        if (process_byte) begin
          trigger_mask            <=  {trigger_mask[27:0], nibble}; 
          read_count              <=  read_count -  1;
          if (read_count == 0) begin
            read_count            <=  7;
            read_state            <=  READ_REPEAT_COUNT;
          end
        end
      end
      READ_TRIGGER_AFTER: begin
        if (process_byte) begin
          trigger_after           <=  {trigger_after[27:0], nibble}; 
          read_count              <=  read_count -  1;
          if (read_count == 0) begin
            read_count            <=  7;
            read_state            <=  READ_REPEAT_COUNT;
          end
        end
      end
      READ_REPEAT_COUNT: begin
        if (process_byte) begin
          repeat_count            <=  {repeat_count[27:0], nibble}; 
          read_count              <=  read_count -  1;
          if (read_count == 0) begin
            read_count            <=  7;
            set_strobe            <=  1;
            command_response      <=  `RESPONSE_SUCCESS; 
            read_state            <=  SEND_RESPONSE;
          end
        end
      end
      READ_ENABLE_SET: begin
        if (process_byte) begin
          if (read_data == (0 + `HEX_0)) begin
            enable                <=  0;
            command_response      <=  `RESPONSE_SUCCESS;
          end
          else if (read_data == (1 + `HEX_0)) begin
              enable              <=  1;
          end
          else begin
            command_response      <=  `RESPONSE_FAIL;
            read_state            <=  SEND_RESPONSE;
          end
        end
      end
      SEND_RESPONSE: begin
        if (status_written) begin
          $display ("ULA: Got a response back from the write state machine that data was sent");
          read_state           <=  IDLE;
        end
      end
     default: begin
        read_state             <=  IDLE;
      end
    endcase
    //write data back to the host
  end
end

parameter                   RESPONSE_WRITE_ID     = 1;
parameter                   RESPONSE_WRITE_STATUS = 2;
parameter                   RESPONSE_WRITE_ARG    = 3;
parameter                   GET_DATA_PACKET       = 4;
parameter                   SEND_DATA_PACKET      = 5;



//write data state machine
always @ (posedge clk) begin
  if (rst) begin
    write_strobe                <=  0;
    write_data                  <=  0;
    status_written              <=  0;
    write_state                 <=  IDLE;
    la_data_read_count          <=  0;
    la_data                     <=  0;
  end
  else begin
    write_strobe                <=  0;
    status_written              <=  0;
    data_read_strobe            <=  0;
    case (write_state ==  IDLE)
      IDLE: begin
        if (write_status) begin
          write_state           <=  RESPONSE_WRITE_ID;
        end
        if (enable && finished) begin
          write_state           <=  GET_DATA_PACKET;
          la_data_read_count    <=  data_read_size;
          data_read_strobe      <=  1;
        end
      end
      RESPONSE_WRITE_ID: begin
        if (write_available) begin
          write_data            <=  `RESPONSE_ID;  
          write_strobe          <=  1;
          write_state            <=  RESPONSE_WRITE_STATUS;
        end
      end
      RESPONSE_WRITE_STATUS: begin
        if (write_available) begin
          write_data            <=  command_response;
          write_strobe          <=  1;
          if (response_status > 0) begin
            write_state          <=  RESPONSE_WRITE_ARG;
          end
          else begin
            write_state          <=  IDLE;
          end
        end
      end
      RESPONSE_WRITE_ARG: begin
        if (write_available) begin
          write_data            <=  response_status;
          write_strobe          <=  1;
          write_state            <=  IDLE;
        end
      end
      GET_DATA_PACKET: begin
        byte_count              <=  0;
        la_data                 <=  data;
      end
      SEND_DATA_PACKET: begin
        if (write_available) begin
          write_data              <=  la_data[31:24];
          la_data                 <=  {la_data[23:0], 8'h00};
 
          if (byte_count == 3) begin
            if (la_data_read_count > 0) begin
              data_read_strobe    <=  1;
              write_state         <=  GET_DATA_PACKET;
            end
            else begin
              write_state         <=  IDLE;
            end
          end
 
          byte_count              <=  byte_count + 1;
        end
      end
      default begin
        write_state               <=  IDLE;
      end
    endcase
  end
end


function decode_ascii;
input ascii_byte;
begin
  if (ascii_byte >= 8'h41) begin
    decode_ascii  =  ascii_byte - 55;
  end
  else begin
    decode_ascii  =  ascii_byte - 32;
  end
end
endfunction

endmodule
