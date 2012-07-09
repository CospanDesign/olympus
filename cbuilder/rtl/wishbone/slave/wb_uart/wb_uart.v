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
  Use this to tell sycamore how to populate the Device ROM table
  so that users can interact with your slave

  META DATA

  identification of your device 0 - 65536
  DRT_ID:  2

  flags (read drt.txt in the slave/device_rom_table directory 1 means
  a standard device
  DRT_FLAGS:  1

  number of registers this should be equal to the nubmer of ADDR_???
  parameters
  DRT_SIZE:  4

*/


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
  wbs_int_o
);

input         clk;
input         rst;

//wishbone slave signals
input         wbs_we_i;
input         wbs_stb_i;
input         wbs_cyc_i;
input   [3:0] wbs_sel_i;
input   [31:0]  wbs_adr_i;
input     [31:0]  wbs_dat_i;
output reg  [31:0]  wbs_dat_o;
output reg      wbs_ack_o;
output reg      wbs_int_o;

parameter     ADDR_0  = 32'h00000000;
parameter     ADDR_1  = 32'h00000001;
parameter     ADDR_2  = 32'h00000002;


//uart controller PHY
output        tx;
input         rx;

input         rts;
output        cts;

input         dtr;
output        dsr;

reg   [7:0]   control;
wire  [7:0]   status;
reg   [31:0]  prescaler;

reg           write_pulse;
reg   [7:0]   write_data;
wire          write_fifo_full;

reg           read_pulse;
wire  [7:0]   read_data;
wire          read_fifo_empty;

uart_controller uc (
  .clk(clk),
  .rst(rst),

  //Physical Lines
  .rx(rx),
  .tx(tx),
  .cts(cts),
  .rts(rts),
  .dtr(drt),
  .dsr(dsr),

  //Control/Status
  .control(control),
  .status(status),
  .prescaler(prescaler),

  //Data In
  .write_pulse(write_pulse),
  .write_data(write_data),
  .write_fifo_full(write_fifo_full),

  //Data Out
  .read_pulse(read_pulse),
  .read_fifo_empty(read_fifo_empty),
  .read_data(read_data)
);


//blocks
always @ (posedge clk) begin
  if (rst) begin
    wbs_dat_o         <= 32'h0;
    wbs_ack_o         <= 0;
    wbs_int_o         <= 0;

    control           <=  8'h0;
    prescaler         <=  32'h0000;
    write_pulse       <=  0;
    write_data        <=  8'h0;
    read_pulse        <=  0;
  end

  else begin
    //when the master acks our ack, then put our ack down
    if (wbs_ack_o & ~ wbs_stb_i)begin
      wbs_ack_o <= 0;
    end

    if (wbs_stb_i & wbs_cyc_i) begin
      //master is requesting somethign
      if (wbs_we_i) begin
        //write request
        case (wbs_adr_i) 
          ADDR_0: begin
            //writing something to address 0
            //do something

            //NOTE THE FOLLOWING LINE IS AN EXAMPLE
            //  THIS IS WHAT THE USER WILL WRITE TO ADDRESS 0
            $display("user wrote %h", wbs_dat_i);
          end
          ADDR_1: begin
            //writing something to address 1
            //do something
  
            //NOTE THE FOLLOWING LINE IS AN EXAMPLE
            //  THIS IS WHAT THE USER WILL WRITE TO ADDRESS 0
            $display("user wrote %h", wbs_dat_i);
          end
          ADDR_2: begin
            //writing something to address 3
            //do something
  
            //NOTE THE FOLLOWING LINE IS AN EXAMPLE
            //  THIS IS WHAT THE USER WILL WRITE TO ADDRESS 0
            $display("user wrote %h", wbs_dat_i);
          end
          //add as many ADDR_X you need here
          default: begin
          end
        endcase
      end

      else begin 
        //read request
        case (wbs_adr_i)
          ADDR_0: begin
            //reading something from address 0
            //NOTE THE FOLLOWING LINE IS AN EXAMPLE
            //  THIS IS WHAT THE USER WILL READ FROM ADDRESS 0
            $display("user read %h", ADDR_0);
            wbs_dat_o <= ADDR_0;
          end
          ADDR_1: begin
            //reading something from address 1
            //NOTE THE FOLLOWING LINE IS AN EXAMPLE
            //  THIS IS WHAT THE USER WILL READ FROM ADDRESS 0
            $display("user read %h", ADDR_1);
            wbs_dat_o <= ADDR_1;
          end
          ADDR_2: begin
            //reading soething from address 2
            //NOTE THE FOLLOWING LINE IS AN EXAMPLE
            //  THIS IS WHAT THE USER WILL READ FROM ADDRESS 0
            $display("user read %h", ADDR_2);
            wbs_dat_o <= ADDR_2;
          end
          //add as many ADDR_X you need here
          default: begin
          end
        endcase
      end
      wbs_ack_o <= 1;
    end
  end
end


endmodule
