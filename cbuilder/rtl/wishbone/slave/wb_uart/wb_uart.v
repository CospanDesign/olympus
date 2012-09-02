//wb_uart.v
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
  Use this to tell olympus how to populate the Device ROM table
  so that users can interact with your slave

  META DATA

  identification of your device 0 - 65536
  DRT_ID:  2

  flags (read drt.txt in the slave/device_rom_table directory 1 means
  a standard device
  DRT_FLAGS:  1

  number of registers this should be equal to the nubmer of ADDR_???
  parameters
  DRT_SIZE:  7

*/
`include "project_defines.v"
`timescale 1ns/1ps

//Control Flag Defines
`define CONTROL_RESET             0
`define CONTROL_FC_CTS_RTS        1
`define CONTROL_FC_DTS_DSR        2
`define CONTROL_READ_INTERRUPT    3
`define CONTROL_WRITE_INTERRUPT   4

//Status
`define STATUS_TRANSMIT_OVERFLOW  0
`define STATUS_READ_OVERFLOW      1
`define STATUS_READ_UNDERFLOW     2
`define STATUS_READ_INTERRUPT     3
`define STATUS_WRITE_INTERRUPT    4


module wb_uart (
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

  tx,
  rx,
  rts,
  cts,
  dtr,
  dsr
);

input               clk;
input               rst;

//wishbone slave signals
input               wbs_we_i;
input               wbs_stb_i;
input               wbs_cyc_i;
input       [3:0]   wbs_sel_i;
input       [31:0]  wbs_adr_i;
input       [31:0]  wbs_dat_i;
output reg  [31:0]  wbs_dat_o;
output reg          wbs_ack_o;
output reg          wbs_int_o;

parameter           REG_CONTROL     = 32'h00000000;
parameter           REG_STATUS      = 32'h00000001;
parameter           REG_PRESCALER   = 32'h00000002;
parameter           REG_CLOCK_DIV   = 32'h00000003;
parameter           REG_WRITE_COUNT = 32'h00000004;
parameter           REG_WRITE       = 32'h00000005;
parameter           REG_READ_COUNT  = 32'h00000006;
parameter           REG_READ        = 32'h00000007;


//uart controller PHY
output              tx;
input               rx;

input               rts;
output              cts;

input               dtr;
output              dsr;


//Registers / Wires
reg         [7:0]   control;
reg         [7:0]   status;
wire        [31:0]  prescaler;
reg                 set_clock_div;
reg         [31:0]  clock_div;
wire        [31:0]  default_clock_div;

reg                 write_strobe;

reg         [7:0]   write_data;
wire                write_full;
wire        [31:0]  write_available;
reg         [15:0]  write_count;
reg         [1:0]   dw_countdown;
wire        [31:0]  write_size;

reg         [1:0]   read_delay;
reg                 read_strobe;
wire        [7:0]   read_data;
wire                read_empty;
wire        [31:0]  read_count;
wire        [31:0]  read_size;

//Status
wire                read_overflow;
wire                write_overflow;


//write_data
reg                 write_en;
reg                 read_en;
reg          [1:0]  local_read_count;
//user requests to read this much data
reg          [31:0] user_read_count;

wire                reading;
wire                writing;


uart_controller uc (
  .clk(clk),
  .rst(rst),

  //Physical Lines
  .rx(rx),
  .tx(tx),
  .cts(cts),
  .rts(rts),

  //Control/Status
  .control_reset(control[`CONTROL_RESET]),
  .cts_rts_flowcontrol(control[`CONTROL_FC_CTS_RTS]),
  .read_overflow(read_overflow),
  .prescaler(prescaler),
  .set_clock_div(set_clock_div),
  .clock_div(clock_div),
  .default_clock_div(default_clock_div),

  //Data In
  .write_strobe(write_strobe),
  .write_data(write_data),
  .write_full(write_full),
  .write_available(write_available),
  .write_size(write_size),

  //Data Out
  .read_strobe(read_strobe),
  .read_data(read_data),
  .read_empty(read_empty),
  .read_count(read_count),
  .read_size(read_size)
);

integer         i;

assign          reading   = ((wbs_cyc_i && !wbs_we_i && (read_count > 0) && (wbs_adr_i == REG_READ)) || read_en);
assign          writing   = (wbs_cyc_i && wbs_we_i && ((write_count > 0) || (wbs_adr_i == REG_WRITE)));

//blocks
always @ (posedge clk) begin
  if (rst) begin
    wbs_dat_o               <=  32'h0;
    wbs_ack_o               <=  0;
    wbs_int_o               <=  0;

    control                 <=  8'h0;
    write_strobe            <=  0;
    read_strobe             <=  0;
    read_delay              <=  0;

    user_read_count         <=  0;
    local_read_count        <=  0;

    //write
    write_en                <=  0;

    write_count             <=  0;
    dw_countdown            <=  0;
    write_data              <=  0;

    //status
    status                  <=  0;
    set_clock_div           <=  0;
    clock_div               <=  0;

    wbs_int_o               <=  0;

  end

  else begin
    write_strobe            <=  0;
    set_clock_div           <=  0;
    read_strobe             <=  0;
    control[`CONTROL_RESET] <=  0;


    //status
    if(write_overflow) begin
      status[`STATUS_TRANSMIT_OVERFLOW]   <=  1;
    end
    if(read_overflow) begin
      status[`STATUS_READ_OVERFLOW]       <=  1;
    end
    if (!read_empty) begin
      status[`STATUS_READ_INTERRUPT]      <=  1;
    end
    if (!write_full) begin
      status[`STATUS_WRITE_INTERRUPT]     <=  1;
    end

    if (control[`CONTROL_READ_INTERRUPT] && !read_empty) begin
      $display ("\tWB_UART: READ INTERRUPT!");
      wbs_int_o                           <=  1;
    end
    if (control[`CONTROL_WRITE_INTERRUPT] && !write_full) begin
      $display ("\tWB_UART: WRITE INTERRUPT!");
      wbs_int_o                           <=  1;
    end


    //when the master acks our ack, then put our ack down
    if (wbs_ack_o & ~wbs_stb_i)begin
      wbs_ack_o                         <= 0;
    end
    if (wbs_cyc_i == 0) begin
      //at the end of a cycle disable the special case of writing to the UART FIFO
      write_en                          <=  0;
      read_en                           <=  0;
    end

    if (wbs_stb_i & wbs_cyc_i) begin
      //master is requesting somethign
      //write request
      if (wbs_we_i) begin
        //check if this is a continuation of a read
        if (write_en) begin
          if (!wbs_ack_o) begin
            $display ("Writing a byte write_count == %d, dw_countdown == %d", write_count, dw_countdown);
            case (dw_countdown)
              0: begin
                write_data            <=  wbs_dat_i[7:0];
              end
              1: begin
                write_data            <=  wbs_dat_i[15:8];
              end
              2: begin
                write_data            <=  wbs_dat_i[23:16];
              end
              3: begin
                write_data            <=  wbs_dat_i[31:24];
              end
            endcase
            write_strobe              <=  1;
            if (dw_countdown == 0) begin
              wbs_ack_o               <=  1;
              //I KNOW this code is redundant but it is more readible
              dw_countdown            <=  3;
            end
            else begin
              dw_countdown            <=  dw_countdown - 1;
            end
            if (write_count == 0) begin
              dw_countdown            <=  3;
              wbs_ack_o               <=  1;
            end
            else begin
              write_count             <=  write_count - 1;
            end
          end
        end
 //not a continuation of a write
        else begin
          case (wbs_adr_i) 
            REG_CONTROL: begin
              control                 <=  wbs_dat_i[31:0];
            end
            REG_STATUS: begin
              //USER CANNOT WRITE ANYTHING TO STATUS
            end
            REG_PRESCALER: begin
              //USER CANNOT WRITE ANYTHING TO PRESCALER
            end
            REG_CLOCK_DIV: begin
              //the host will have to calculate out the baudrate
              clock_div               <=  wbs_dat_i[31:0];
              set_clock_div           <=  1;
              $display("user wrote %h", wbs_dat_i);
            end
            REG_WRITE_COUNT: begin
              //USER ANNOT WRITE ANYTHING TO WRITE COUNT
            end
            REG_WRITE: begin
              $display ("Starting a write cycle");
              //this is where the start of a UART write will begin, subsequent burst reads after this will be written to a output FIFO
              //I need a flag that will inidicate that the user will be writting to the buffer

              //write register
              write_en                <=  1;
              dw_countdown            <=  1;
              if (wbs_dat_i[31:16] <= 2) begin
                dw_countdown          <=  wbs_dat_i[17:16] - 1;
              end
              if (wbs_dat_i[31:16] == 0) begin
                write_count           <=  0;
                write_en              <=  0;
              end
              if (wbs_dat_i[31:16]     <= 2) begin
                write_count           <=  wbs_dat_i[31:16]  - 1;
              end
              else begin
                write_count             <=  wbs_dat_i[31:16];
              end
            end
            REG_READ_COUNT: begin
              //USER CANNOT WRITE ANYTHING TO READ COUNT
              user_read_count         <=  wbs_dat_i;
            end
            REG_READ: begin
              //USER CANNOT WRITE ANYTHING TO THE READ
            end
            default: begin
            end
          endcase
        end
      end

      //reading
      else begin 
        if (read_en) begin
          if (wbs_ack_o == 0) begin
              if (read_delay > 0) begin
              read_delay  <=  read_delay - 1;
            end
            else begin
              $display ("WB_UART (%g): Reading a byte user_read_count == %d, local_read_count == %d", $time, user_read_count, local_read_count);
              $display ("WB_UART: Data: %h", read_data);
              //I can't use a normal shift register because the first value won't be at the end if the user
              //specifies anything below a multiple of 4
              case (local_read_count)
                0: begin
                  //$display ("WB_UART (%g): putting read data into the top byte", $time);
                  wbs_dat_o[31:24]  <=  read_data;
                  wbs_dat_o[23:0]   <=  0;
                  read_strobe       <=  1;
                  read_delay        <=  2;
                end
                1: begin
                  wbs_dat_o[23:16]  <=  read_data;
                  read_strobe       <=  1;
                  read_delay        <=  2;

                end
                2: begin
                  wbs_dat_o[15:8]  <=  read_data;
                  read_strobe       <=  1;
                  read_delay        <=  2;

                end
                3: begin
                  wbs_dat_o[7:0]  <=  read_data;
                  read_strobe       <=  1;
                  read_delay        <=  2;
                end
              endcase

              
              if (local_read_count == 3) begin
                $display ("WB_UART (%g): Sending an Ack for a  32 bit data packet to the host", $time);
                wbs_ack_o         <=  1;
              end
              if (user_read_count == 0) begin
                $display ("WB_UART (%g): Finished reading all the user's data", $time);
                wbs_ack_o         <=  1;
              end
              else begin
                local_read_count  <=  local_read_count + 1;
                user_read_count   <=  user_read_count - 1;
              end
              if (read_count == 0) begin
                local_read_count  <=  0;
                $display ("WB_UART (%g): Read FIFO is empty", $time);
                wbs_ack_o         <=  1;
              end
            end
          end
        end
        else begin
          //read request
          case (wbs_adr_i)
            REG_CONTROL: begin
              wbs_dat_o <= control;
            end
            REG_STATUS: begin
              //reset all status flags on a READ
              status[`STATUS_TRANSMIT_OVERFLOW]          <=  0;
              status[`STATUS_READ_OVERFLOW]              <=  0;
              status[`STATUS_READ_UNDERFLOW]             <=  0;
              status[`STATUS_READ_INTERRUPT]             <=  0;
              status[`STATUS_WRITE_INTERRUPT]            <=  0;
              wbs_dat_o                                 <= status;
              wbs_int_o                                 <=  0;
            end
            REG_PRESCALER: begin
              wbs_dat_o           <= prescaler;
            end
            REG_CLOCK_DIV: begin
              if (clock_div ==  0) begin
                wbs_dat_o         <=  default_clock_div;
              end
              else begin
                wbs_dat_o         <= clock_div;
              end
            end
            REG_WRITE_COUNT: begin
              wbs_dat_o           <=  write_available;
            end
            REG_WRITE: begin
              wbs_dat_o           <=  32'h00000000;
            end
            REG_READ_COUNT: begin
              wbs_dat_o           <=  read_count;
            end
            REG_READ: begin
              $display ("User requested data");
              if (read_count > 0) begin
                read_en           <=  1;
                read_strobe       <=  0;
                //reset the 8-bit -> 32-bit converter counter
                local_read_count  <=  0;
                wbs_dat_o         <=  0;
                wbs_dat_o[31:24]  <=  read_data;
                wbs_dat_o[23:0]   <=  0;
                if (user_read_count > 1) begin
                  read_delay      <=  2;
                  //user has specified an amount of data to read
                  local_read_count  <=  0;
                  //decrement the user_read_count because we are requesting a byte right now
                  if (user_read_count >= 2) begin
                    user_read_count <=  user_read_count - 1;
                  end
                end
                else begin
                  read_delay        <=  2;
                  local_read_count  <=  0;
                  user_read_count   <=  0;
                end
              end
              else begin
                //no data just return 0
                wbs_dat_o <=  32'h00000000;
                status[`STATUS_READ_UNDERFLOW]  <=  1;
              end
            end
            default: begin
              wbs_dat_o <=  32'h00000000;
            end
          endcase
        end
      end
      if (!reading && !writing) begin
        $display ("WB_UART (%g): Sending Main ACK", $time);
        wbs_ack_o <= 1;
      end
    end
  end
end

endmodule
