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
  10/29/2011
    -added an 'else' statement that so either the
    reset HDL will be executed or the actual code
    not both
*/

/*
  10/23/2011
    -fixed the wbs_ack_i to wbs_ack_o
    -added the default entries for read and write
      to illustrate the method of communication
    -added license
*/
/*
  9/10/2011
    -removed the duplicate wbs_dat_i
    -added the wbs_sel_i port
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
  cts
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
parameter           REG_BAUDRATE    = 32'h00000003;
parameter           REG_WRITE       = 32'h00000004;
parameter           REG_READ_COUNT  = 32'h00000005;
parameter           REG_READ        = 32'h00000006;


//uart controller PHY
output              tx;
input               rx;

input               rts;
output              cts;

input               dtr;
output              dsr;

reg         [7:0]   control;
wire        [7:0]   status;
reg                 status_reset;
wire        [31:0]  prescaler;
reg                 set_clock_div;
reg         [31:0]  clock_div;
wire        [31:0]  default_clock_div;

reg                 write_strobe;
reg         [3:0]   write_strobe_count;

reg         [7:0]   write_data [0:4];
wire                write_full;
wire        [31:0]  write_available;
reg         [15:0]  write_count;
reg         [15:0]  write_countdown;
wire        [31:0]  write_size;

reg                 read_strobe;
wire        [7:0]   read_data;
wire                read_empty;
wire        [31:0]  read_count;
wire        [31:0]  read_size;

//write_data
reg                 write_en;
reg                 read_en;
reg          [1:0]  local_read_count;
//user requests to read this much data
reg          [31:0] user_read_count;
reg                 user_read_limit;


uart_controller uc (
  .clk(clk),
  .rst(rst),

  //Physical Lines
  .rx(rx),
  .tx(tx),
  .cts(cts),
  .rts(rts),

  //Control/Status
  .control(control),
  .status(status),
  .status_reset(status_reset),
  .prescaler(prescaler),
  .set_clock_div(set_clock_div),
  .clock_div(clock_div),
  .default_clock_div(default_clock_div),

  //Data In
  .write_strobe(write_strobe),
  .write_strobe_count(write_strobe_count),
  .write_data0(write_data[0]),
  .write_data1(write_data[1]),
  .write_data2(write_data[2]),
  .write_data3(write_data[3]),
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

//blocks
always @ (posedge clk) begin
  if (rst) begin
    wbs_dat_o               <= 32'h0;
    wbs_ack_o               <= 0;
    wbs_int_o               <= 0;

    control                 <=  8'h0;
    write_strobe            <=  0;
//    write_data              <=  8'h0;
    read_strobe              <=  0;

    user_read_count         <=  0;
    user_read_limit         <=  0;

    //write
    write_en                <=  0;
    write_strobe_count      <=  0;
    write_count             <=  15'h000;

    write_countdown         <=  0;

    for (i = 0; i < 4; i = i + 1) begin
      write_data[i]         <=  0;
    end
    //status
    status_reset            <=  0;
    set_clock_div           <=  0;
    clock_div               <=  0;

  end

  else begin
    status_reset            <=  0;
    write_strobe            <=  0;
    set_clock_div           <=  0;

    //when the master acks our ack, then put our ack down
    if (wbs_ack_o & ~ wbs_stb_i)begin
      wbs_ack_o             <= 0;
    end
    if (wbs_cyc_i == 0) begin
      //at the end of a cycle disable the special case of writing to the UART FIFO
      write_en              <=  0;
      read_en               <=  0;
      write_count           <=  0;
    end

    if (wbs_stb_i & wbs_cyc_i) begin
      //master is requesting somethign
      if (wbs_we_i) begin

        //write request
        if (write_en) begin
          if (write_countdown == 0) begin
            write_strobe        <=  0;
            write_en            <=  0;
            write_strobe_count  <=  0;
          end
          else begin
            write_strobe              <=  1;
            write_strobe_count        <=  4;
            write_data[0]             <=  wbs_dat_i[31:24];
            write_data[1]             <=  wbs_dat_i[23:16];
            write_data[2]             <=  wbs_dat_i[15:8];
            write_data[3]             <=  wbs_dat_i[7:0];
          end
        end

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
            REG_BAUDRATE: begin
              //the host will have to calculate out the baudrate
              clock_div               <=  wbs_dat_i[31:0];
              set_clock_div           <=  1;
              $display("user wrote %h", wbs_dat_i);
            end
            REG_WRITE: begin
              //this is where the start of a UART write will begin, subsequent burst reads after this will be written to a output FIFO
              //I need a flag that will inidicate that the user will be writting to the buffer
 
              //write register
              write_en              <=  1;
              write_strobe          <=  1;
              write_strobe_count    <=  2;
              write_count           <=  wbs_dat_i[31:16];
              if (wbs_dat_i[31:16] < 2) begin
                write_strobe_count  <=  wbs_dat_i[31:16];
              end
              if (wbs_dat_i[31:16] == 0) begin
                write_countdown     <=  0;
                write_en            <=  0;
              end
              if (wbs_dat_i[31:16] == 1) begin
                write_countdown     <=  0;
              end
              else if (wbs_dat_i [31:16] > 1) begin
                write_countdown     <=  wbs_dat_i[31:16] - 2; 
              end
              write_data[0]         <=  wbs_dat_i[15:8];
              write_data[1]         <=  wbs_dat_i[7:0];
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

      else begin 
        if (read_en) begin
          if (wbs_ack_o == 0) begin
            if (user_read_limit) begin
              if (local_read_count == 3) begin
                wbs_ack_o <=  1;
              end
              local_read_count  <=  local_read_count + 1;
              if (local_read_count == 0) begin
                read_en           <=  0;
                wbs_ack_o         <=  1;
              end
              if (read_count == 0) begin
                read_en           <=  0;
                local_read_count  <=  0;
                wbs_ack_o         <=  1;
              end
            end
            else begin
              read_en             <=  0;
              wbs_ack_o           <=  1;
            end
            wbs_dat_o             <=  {wbs_dat_o[31:8], read_data};
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
              status_reset      <=  1;
              wbs_dat_o         <= status;
            end
            REG_PRESCALER: begin
              wbs_dat_o <= prescaler;
            end
            REG_BAUDRATE: begin
              if (clock_div ==  0) begin
                wbs_dat_o <=  default_clock_div;
              end
              else begin
                wbs_dat_o <= clock_div;
              end
            end
            REG_WRITE: begin
              wbs_dat_o <=  32'h00000000;
            end
            REG_READ_COUNT: begin
              wbs_dat_o <=  read_count;
            end
            REG_READ: begin
              if (read_count > 0) begin
                read_en           <=  1;
                read_strobe       <=  1;
                //reset the 8-bit -> 32-bit converter counter
                local_read_count  <=  0;
                wbs_dat_o         <=  0;
                if (user_read_count > 0) begin
                  user_read_limit <=  1;
                end
              end
              else begin
                wbs_dat_o <=  32'h00000000;
              end
            end
            default: begin
              wbs_dat_o <=  32'h00000000;
            end
          endcase
        end
      end
      if (!read_en || ((wbs_adr_i == REG_READ) && (read_count == 0))) begin
        wbs_ack_o <= 1;
      end
    end
  end
end


endmodule
