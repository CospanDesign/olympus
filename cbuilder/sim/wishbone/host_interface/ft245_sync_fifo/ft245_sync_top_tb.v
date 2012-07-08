//uart_top_tb.v
/*
Distributed under the MIT licesnse.
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

`timescale 1ns/1ps

`include "project_defines.v"

module ft245_sync_top_tb; 


reg           clk     = 0;
reg           rst     = 0;

wire  [7:0]   data;
reg   [7:0]   ftdi_in_data;
reg           txe_n;
wire          wr_n;
reg           rde_n;
wire          rd_n;
wire          oe_n;
wire          siwu;

reg           ftdi_clk  = 0;



assign        data  = (oe_n) ? 8'hZ:ftdi_in_data;
//control register
reg   [31:0]  syc_command;
//address register
reg   [31:0]  syc_address;
//data register
reg   [31:0]  syc_data;
wire  [24:0]  syc_data_count;
assign        syc_data_count = syc_command[23:0];

reg   [31:0]  read_data;



wire          master_ready;
wire          in_ready;
wire [31:0]   in_command;
wire [31:0]   in_address;
wire [31:0]   in_data;
wire [27:0]   in_data_count;
wire          out_ready;
wire          out_en;
wire [31:0]   out_status;
wire [31:0]   out_address;
wire [31:0]   out_data;
wire [27:0]   out_data_count;
wire          ih_reset;


  
//instantiate the ft245_sync core
ft_host_interface ft_hi(
  .clk(clk),
  .rst(rst),

  .master_ready(master_ready),
  .ih_ready(in_ready),
  .ih_reset(ih_reset),

  .in_command(in_command),
  .in_address(in_address),
  .in_data_count(in_data_count),
  .in_data(in_data),

  .oh_ready(out_ready),
  .oh_en(out_en),

  .out_status(out_status),
  .out_address(out_address),
  .out_data_count(out_data_count),
  .out_data(out_data),

  .ftdi_clk(ftdi_clk),
  .ftdi_data(data),
  .ftdi_txe_n(txe_n),
  .ftdi_wr_n(wr_n),
  .ftdi_rde_n(rde_n),
  .ftdi_rd_n(rd_n),
  .ftdi_oe_n(oe_n),
  .ftdi_siwu(siwu)
);




//wishbone signals
wire    wbm_we_o;
wire    wbm_cyc_o;
wire    wbm_stb_o;
wire [3:0]  wbm_sel_o;
wire [31:0] wbm_adr_o;
wire [31:0] wbm_dat_i;
wire [31:0] wbm_dat_o;
wire    wbm_ack_i;
wire    wbm_int_i;



wishbone_master wm (
  .clk(clk),
  .rst(rst),
  .in_ready(in_ready),
  .in_command(in_command),
  .in_address(in_address),
  .in_data(in_data),
  .in_data_count(in_data_count),
  .out_ready(out_ready),
  .out_en(out_en),
  .out_status(out_status),
  .out_address(out_address),
  .out_data(out_data),
    .out_data_count(out_data_count),
  .master_ready(master_ready),

  .wb_adr_o(wbm_adr_o),
  .wb_dat_o(wbm_dat_o),
  .wb_dat_i(wbm_dat_i),
  .wb_stb_o(wbm_stb_o),
  .wb_cyc_o(wbm_cyc_o),
  .wb_we_o(wbm_we_o),
  .wb_msk_o(wbm_msk_o),
  .wb_sel_o(wbm_sel_o),
  .wb_ack_i(wbm_ack_i),
  .wb_int_i(wbm_int_i)
);

//wishbone slave 0 signals
wire    wbs0_we_o;
wire    wbs0_cyc_o;
wire[31:0]  wbs0_dat_o;
wire    wbs0_stb_o;
wire [3:0]  wbs0_sel_o;
wire    wbs0_ack_i;
wire [31:0] wbs0_dat_i;
wire [31:0] wbs0_adr_o;
wire    wbs0_int_i;


//wishbone slave 1 signals
wire    wbs1_we_o;
wire    wbs1_cyc_o;
wire[31:0]  wbs1_dat_o;
wire    wbs1_stb_o;
wire [3:0]  wbs1_sel_o;
wire    wbs1_ack_i;
wire [31:0] wbs1_dat_i;
wire [31:0] wbs1_adr_o;
wire    wbs1_int_i;


reg [31:0]  gpio_in = 32'h01234567;
wire [31:0] gpio_out;

assign wbs0_int_i = 0;

//slave 1
wb_gpio s1 (

  .clk(clk),
  .rst(rst),
  
  .wbs_we_i(wbs1_we_o),
  .wbs_cyc_i(wbs1_cyc_o),
  .wbs_dat_i(wbs1_dat_o),
  .wbs_stb_i(wbs1_stb_o),
  .wbs_ack_o(wbs1_ack_i),
  .wbs_dat_o(wbs1_dat_i),
  .wbs_adr_i(wbs1_adr_o),
  .wbs_int_o(wbs1_int_i),

  .gpio_in(gpio_in),
  .gpio_out(gpio_out)

);


wishbone_interconnect wi (
    .clk(clk),
    .rst(rst),

    .m_we_i(wbm_we_o),
    .m_cyc_i(wbm_cyc_o),
    .m_stb_i(wbm_stb_o),
    .m_ack_o(wbm_ack_i),
    .m_dat_i(wbm_dat_o),
    .m_dat_o(wbm_dat_i),
    .m_adr_i(wbm_adr_o),
    .m_int_o(wbm_int_i),

    .s0_we_o(wbs0_we_o),
    .s0_cyc_o(wbs0_cyc_o),
    .s0_stb_o(wbs0_stb_o),
    .s0_ack_i(wbs0_ack_i),
    .s0_dat_o(wbs0_dat_o),
    .s0_dat_i(wbs0_dat_i),
    .s0_adr_o(wbs0_adr_o),
    .s0_int_i(wbs0_int_i),

    .s1_we_o(wbs1_we_o),
    .s1_cyc_o(wbs1_cyc_o),
    .s1_stb_o(wbs1_stb_o),
    .s1_ack_i(wbs1_ack_i),
    .s1_dat_o(wbs1_dat_o),
    .s1_dat_i(wbs1_dat_i),
    .s1_adr_o(wbs1_adr_o),
    .s1_int_i(wbs1_int_i)


);



integer ch;
integer read_count;
integer fd_in;
integer fd_out;


reg   ftdi_new_data_available;
reg   ftdi_ready_to_read;


//make the ftdi clock 3X faster than the regular clock
always #4   ftdi_clk  = ~ftdi_clk;

always #5   clk     = ~clk;



//reg [15:0]  number_to_write;
//virtual FTDI variables
reg [3:0] state;
reg [3:0] temp_state; //weird behavior in the while loops, need something to do in them


parameter IDLE         = 4'h0;
parameter RX_ENABLE_OUTPUT   = 4'h1;
parameter RX_WRITING     = 4'h2;
parameter RX_STOP        = 4'h3;
parameter TX_READING     = 4'h4;
parameter TX_READING_FULL    = 4'h5;
parameter TX_READING_FINISHED  = 4'h6;


reg [31:0]  cmd;
reg [31:0]  addr;
reg [31:0]  dat;
reg [31:0]  dat_out;
reg [23:0]  data_count;
reg [23:0]  count_data;
reg [23:0]  temp_count;

initial begin

  ch    = 0;
  $dumpfile ("design.vcd");
  $dumpvars (0, ft245_sync_top_tb);
  fd_in = $fopen ("fsync_input_data.txt", "r");
  ftdi_new_data_available <= 0;

  #20
  rst           <= 1;
  ftdi_new_data_available <= 0;
  ftdi_ready_to_read    = 0;
//  number_to_write     <= 0;

  syc_command       <= 32'h0;
  syc_address       <= 32'h0;
  syc_data          <= 32'h0;

  cmd               <=  32'h0000;
  addr              <=  32'h0000;
  dat               <=  32'h0000;
  data_count        <=  24'h000;
  count_data        <=  24'h000;

  #20
  rst           <= 0;
  #20

  //testing input
  if (fd_in == 0) begin
    //$display("fsync_input_data.txt was not found");
  end 
  else begin
    //process data from a file
    while (!$feof(fd_in)) begin
      read_count = $fscanf (fd_in, "%h:%h:%h\n", syc_command, syc_address, syc_data);
      $display ("tb: data from file: %h:%h:%h", syc_command, syc_address, syc_data);
      cmd <=  syc_command;
      addr <= syc_address;
      dat <=  syc_data;
      data_count <= syc_command[23:0];

      //$display ("tb: sending data down to core");
      ftdi_ready_to_read    = 1;

      while (state !=  RX_STOP) begin
        #1
        temp_state  <= state;
      end
      ftdi_ready_to_read    = 0;
      #1000
      temp_state    <= state;

    end
  end

  $fclose (fd_in);
  //$display ("Finished tests");
  #300
  $finish;
end

parameter BUFFER_SIZE    = 512;

reg [24:0]  ftdi_write_size;
reg [24:0]  ftdi_read_count;

reg [24:0]  write_count;


reg         rxe_debug;
reg         txe_debug;

initial begin
  rxe_debug <=  1;
//  #1236;
//  rxe_debug <=  0;
//  #100;
//  rxe_debug <=  1;
end

initial begin
  txe_debug <=  1;
  #6208;
  txe_debug <=  0;
  #84;
  txe_debug <=  1;
end
//virtual FTDI chip
always @ (negedge ftdi_clk) begin
  if (rst) begin
    state      <=  IDLE;
    ftdi_write_size   <=  0;
    ftdi_read_count   <=  0;
    write_count     <=  0;
    ftdi_in_data    <=  0;
    temp_count      <=  0;
    txe_n     <=  1;  
  end
  else begin
    //not in reset
    rde_n <= ~(ftdi_ready_to_read && rxe_debug);
    txe_n <=  ~(txe_debug);
    //rde_n <= ~ftdi_ready_to_read;
    //inject a stop reading command
    if (rde_n && (rxe_debug == 0)) begin
      if (state == RX_WRITING) begin
        $display("Putting the state machine into a safe state");
        state =  RX_ENABLE_OUTPUT;
      end
    end
    else begin
      case (state)
        IDLE: begin
          //no command from the test bench
////I should allow the write count not to reset when the user isn't finished reading and prematurely quits a read sequence
          ftdi_write_size   <= 0;
          ftdi_read_count   <= 0;
 
          //check ifthe 'initial' wants to receive
  ///       rde_n <= ~ftdi_ready_to_read;
 
          //read always gets priority
          if (~rde_n & ~oe_n) begin
            //$display("tb: rde_n and oe_n LOW, wait for rd_n to go LOW");
            state  <=  RX_ENABLE_OUTPUT;
            //count is given in 32 bits, so need to multiply it by 4 to send all bytes
            //add eight for the address and control data
            ftdi_write_size <= (data_count  * 4) + 8;
            count_data  = 1;
            write_count   <= 0;
            ftdi_in_data    <= 8'hCD;
          end
 
        end
        RX_ENABLE_OUTPUT: begin
          //$display ("tb: total number of bytes to send: %d", ftdi_write_size);
          //$display ("tb: waiting for rd_n to go low");
          //enable is high, now wait for the read to go low
          if (~rd_n) begin
            //$display("tb: rd_n LOW, start writing data to the core");
            state  <= RX_WRITING;         
    //        //$display ("tb: sending %h", syc_command[31:24]);
            //ftdi_in_data      <= syc_command[31:24];
            //ftdi_in_data    <= 8'hCD;
            //syc_command   <= {syc_command[24:0], 8'h0};
            if (write_count < ftdi_write_size) begin
              write_count <= write_count;
            end
          end
        end
        RX_WRITING: begin
        if (write_count < ftdi_write_size) begin
          if (!rd_n) begin
            //hacky way of sending all the data down
            if (write_count >= 0 && write_count <= 3) begin
              //already sent the first byte of the command
      //          //$display ("tb: sending %h", syc_command[31:24]);
              ftdi_in_data  <= syc_command[31:24];
              syc_command <= {syc_command[23:0], 8'h0};
            end
            else if (write_count > 3 && write_count <= 7) begin 
      //            //$display ("tb: sending %h", syc_address[31:24]);
              ftdi_in_data <= syc_address[31:24];
              syc_address <= {syc_address[23:0], 8'h0};
            end
            else if (write_count > 7 && write_count < 4'hC) begin
              //larger than 7
              
              //else if (write_count > 7) begin
        //could possible read data from a file if we need to send multiple 32 bits
        //            //$display ("tb: sending %h", syc_data[31:24]);
              ftdi_in_data <= syc_data[31:24];
              syc_data <= {syc_data[23:0], 8'h0};
              if (write_count == 4'hB && data_count > 1 && cmd[31:24] == 1) begin
                count_data  = count_data + 1;
                $display ("tb: BURST WRITING!");
                read_count = $fscanf (fd_in, "%h\n", dat);
                $display ("tb: burst write =  %h, write_count = %d", dat, write_count); 
                syc_data  <=  dat;
              end
            end
            else begin
              ftdi_in_data <= syc_data[31:24];
              syc_data <= {syc_data[23:0], 8'h0};
              temp_count  =  write_count % 4;
              if (cmd[31:24] == 1 && write_count >= 4'hC && (count_data < data_count)) begin
                //$display ("\t\tcount_data < data_count: %d < %d", count_data, data_count);
                //$display ("\t\tWrite Count: %d", write_count);
                //$display ("\t\tWrite Count: %d\n", temp_count);
                if (temp_count == 4'h3) begin
                  read_count = $fscanf (fd_in, "%h\n", dat);
                  $display ("tb: burst write =  %h, write_count = %d", dat, write_count); 
                  syc_data  <=  dat;
                  count_data  = count_data + 1;
                end
              end 
            end
              write_count <= write_count + 1;
            end
          end
          else if (oe_n) begin
            state <=  RX_ENABLE_OUTPUT;
          end
          //can't wait an entire clock cycle to see if we have reached the max count
          else begin
            $display("%t: Sent last byte, telling the core that I've sent all my data", $time);
            state  <= RX_STOP;
            rde_n   <= 1;
          end
        end
        RX_STOP: begin
          //$display ("Wating for core to acknowledge my stop");
          //the core signaled that it is finished transmitting
          if (oe_n & rd_n & ~ftdi_ready_to_read) begin
            //$display ("Core acknowledged my empty, going to IDLE");
            state  <= IDLE;
          end
        end
        default:          begin
          state  <= IDLE;
        end
      endcase
    end
  end
end

reg     new_data;
reg [1:0] data_read_count;
reg     new_transaction;

//reading interface
always @ (posedge ftdi_clk) begin
  if (rst) begin
    data_read_count <=  0;
    new_data    <=  0;
    read_data   <=  0;
    dat_out     <=  0;

  end
  else begin
    //not in reset
    if (~rd_n) begin
      //this is a good place to see if the core is readinga command
      new_transaction     <= 1;
      data_read_count[1:0]  <= 3;
      read_data       <= 0;
    end

    if (new_data) begin
      new_data  <= 0;
      if (new_transaction) begin
        new_transaction <= 0;
        data_read_count <= 0;
      end
      $display ("\tTB READ : %h", read_data);
      dat_out   <=  read_data;
      read_data <= 0;
      new_data  <= 0;

    end
    if (~wr_n && ~txe_n) begin
//      //$display ("tb: incomming byte: %2h", data);
      
      read_data <= {read_data[23:0], data};
      if (data_read_count == 3) begin
        new_data  <= 1;
      end
      data_read_count <= data_read_count + 1;
      
    end
  end
end

endmodule
