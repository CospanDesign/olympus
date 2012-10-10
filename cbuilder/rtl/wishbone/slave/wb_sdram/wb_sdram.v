//wb_sdram.v
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
  Use this to tell sycamore how to populate the Device ROM table
  so that users can interact with your slave

  META DATA

  identification of your device 0 - 65536
  DRT_ID:  5

  flags (read drt.txt in the slave/device_rom_table directory 1 means
  a standard device
  DRT_FLAGS:  1

  number of registers this should be equal to the nubmer of ADDR_???
  parameters
  DRT_SIZE:  8388607

*/


module wb_sdram (
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


  sdram_clk,
  sdram_cke,
  sdram_cs_n,
  sdram_ras,
  sdram_cas,
  sdram_we,

  sdram_addr,
  sdram_bank,
  sdram_data,
  sdram_data_mask,
  sdram_ready,

  ext_sdram_clk

);

input         clk;
input         rst;

//wishbone slave signals
input             wbs_we_i;
input             wbs_stb_i;
input             wbs_cyc_i;
input     [3:0]   wbs_sel_i;
input     [31:0]  wbs_adr_i;
input     [31:0]  wbs_dat_i;
output reg[31:0]  wbs_dat_o;
output reg        wbs_ack_o;
output reg        wbs_int_o;


//SDRAM signals
output            sdram_clk;
output            sdram_cke;
output            sdram_cs_n;
output            sdram_ras;
output            sdram_cas;
output            sdram_we;

output    [11:0]  sdram_addr;
output    [1:0]   sdram_bank;
inout     [15:0]  sdram_data;
output    [1:0]   sdram_data_mask;
output            sdram_ready;

output            ext_sdram_clk;


reg               if_write_strobe;
wire      [1:0]   if_write_ready;
reg       [1:0]   if_write_activate;
wire      [23:0]  if_write_fifo_size;
reg       [23:0]  if_count;
wire              if_starved;

reg               of_read_strobe;
wire              of_read_ready;
reg               of_read_activate;
wire      [23:0]  of_read_count;
wire      [31:0]  of_read_data;
reg       [23:0]  of_count;

//wire              wr_fifo_full;
//wire              rd_fifo_empty;

reg       [3:0]   delay;
reg               wb_reading;

reg               writing;
reg               reading;
reg       [21:0]  ram_address;
reg               first_exchange;


sdram ram (
  .clk(clk),
  .rst(rst),

  //write path
  .if_write_strobe(if_write_strobe),
  .if_write_data(wbs_dat_i),
  .if_write_mask(~wbs_sel_i),
  .if_write_ready(if_write_ready),
  .if_write_activate(if_write_activate),
  .if_write_fifo_size(if_write_fifo_size),
  .if_starved(if_starved),

  //read path
  .of_read_strobe(of_read_strobe),
  .of_read_data(of_read_data),
  .of_read_ready(of_read_ready),
  .of_read_activate(of_read_activate),
  .of_read_count(of_read_count),

  .sdram_write_enable(writing),
  .sdram_read_enable(reading),
  .sdram_ready(sdram_ready),
  //.app_address(wbs_adr_i[23:2]),
  .app_address(ram_address),
  
  .sd_clk(sdram_clk),
  .cke(sdram_cke),
  .cs_n(sdram_cs_n),
  .ras(sdram_ras),
  .cas(sdram_cas),
  .we(sdram_we),

  .address(sdram_addr),
  .bank(sdram_bank),
  .data(sdram_data),
  .data_mask(sdram_data_mask),

  .ext_sdram_clk(ext_sdram_clk)

);

//blocks
always @ (posedge clk) begin
  if (rst) begin
    wbs_ack_o         <=  0;
    wbs_int_o         <=  0;
    if_write_strobe   <=  0;
    of_read_strobe    <=  0;
    delay             <=  0;
    wb_reading        <=  0;
    writing           <=  0;
    reading           <=  0;
    if_count          <=  0;
    of_count          <=  0;
    if_write_activate <=  0;
    ram_address       <=  0;
    first_exchange    <=  0;      
    wbs_dat_o         <=  0;
  end
  else begin
    if_write_strobe                 <= 0;
    of_read_strobe                  <= 0;
    
    //when the master acks our ack, then put our ack down
    if (~wbs_cyc_i) begin
      writing                       <= 0;
      reading                       <= 0;
      of_read_activate              <= 0;
      first_exchange                <= 1;
    end
    
    if (wbs_ack_o & ~wbs_stb_i)begin
      wbs_ack_o                     <= 0;
      if ((if_write_activate > 0) && if_starved) begin
        //release any previously held FIFOs
        if_count                      <= 0;
        if_write_activate             <= 0;
      end
    end

    else if (!wbs_ack_o && wbs_stb_i && wbs_cyc_i) begin
      if (first_exchange) begin
        ram_address                 <=  wbs_adr_i[23:2];
        first_exchange              <=  0;
      end
      //master is requesting something
      if (wbs_we_i) begin
        writing <=  1;
        if (if_write_activate == 0) begin
          //try and get a FIFO
          if (if_write_ready > 0) begin
            if_count                <= if_write_fifo_size - 1;
            if (if_write_ready[0]) begin
              $display ("Getting FIFO 0");
              if_write_activate[0]  <=  1; 
            end
            else begin
              $display ("Getting FIFO 1");
              if_write_activate[1]  <=  1;
            end
          end
        end
        else begin
          $display ("Writing");
          //write request
          if (~wbs_ack_o) begin
            if (if_count > 0) begin
              $display("user wrote %h to address %h", wbs_dat_i, wbs_adr_i);
              wbs_ack_o           <= 1;
              if_write_strobe     <= 1;
              if_count            <= if_count - 1;

            end
            else begin
              if_write_activate         <=  0;
            end
          end
        end
      end

      //Reading
      else if (~writing) begin 
        reading <=  1;
        if (of_read_ready && !of_read_activate) begin
          of_count              <=  of_read_count;
          of_read_activate      <=  1;
        end
        else if (of_read_activate) begin
          if (of_count > 0) begin
            if (~wbs_ack_o) begin
              wbs_dat_o         <=  of_read_data;
              of_count          <=  of_count - 1;
              of_read_strobe    <=  1;
              wbs_ack_o         <=  1;
              $display("user wb_reading %h", wbs_dat_o);
            end
          end
          else begin
            //release the FIFO
            of_read_activate    <=  0;
          end
        end
      end
    end
  end
end


endmodule
