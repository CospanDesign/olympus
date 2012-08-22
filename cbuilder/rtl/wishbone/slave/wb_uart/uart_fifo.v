//UART FIFO
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
A custom FIFO that can take multiple bytes in at a time
*/

module uart_fifo (
  clk,
  rst,

  size,

  write_strobe,
  write_strobe_count,
  write_available,
  write_data0,
  write_data1,
  write_data2,
  write_data3,

  read_strobe,
  read_count,
  read_data,

  overflow,
  underflow,

  full,
  empty
);

//parameters
parameter           FIFO_SIZE       = 8; 
parameter           ALLOW_OVERFLOW  = 1;


input                           clk;
input                           rst;
                              
output  wire  [31:0]            size;
                              
input                           write_strobe;
input         [3:0]             write_strobe_count;
output                          write_size;
output  reg   [31:0]            write_available;
input         [7:0]             write_data0;
input         [7:0]             write_data1;
input         [7:0]             write_data2;
input         [7:0]             write_data3;
                              
input                           read_strobe;
output  reg   [31:0]            read_count;
output  wire  [7:0]             read_data;

output  reg                     overflow;
output  reg                     underflow;

output                          full;
output                          empty;

//Wires, Registers
reg         [7:0]               fifo [FIFO_SIZE - 1: 0];
reg         [FIFO_SIZE - 1: 0]  in_pointer;
reg         [FIFO_SIZE - 1: 0]  out_pointer;
wire                            last;
wire                            allow_overflow;

//Asynchronous Logic
assign                          size            =  (1 << FIFO_SIZE); 
assign                          last            = (out_pointer - 1);
assign                          full            = (in_pointer == last);
assign                          empty           = (out_pointer == in_pointer);
assign                          allow_overflow  = ALLOW_OVERFLOW;
assign                          read_data       = fifo[out_pointer];

integer                         i;

//Synchronous Logic
always @ (posedge clk) begin
  if (rst) begin
    write_available   <=  size;
    read_count        <=  0;
    in_pointer        <=  0;
    out_pointer       <=  0;

    overflow          <=  0;
    underflow         <=  0;

    for (i = 0; i < size; i = i + 1) begin
      fifo[i]         <=  0;
    end

  end
  else begin
    overflow          <=  0;
    underflow         <=  0;
    //if there is a write strobe put data into the FIFO
     //allowed overflow

    if (write_strobe) begin
/*
      if (full) begin
        write_available       <=  0;
        if (allow_overflow) begin
          out_pointer           <=  out_pointer + write_strobe_count;
        end
        overflow              <=  1;
      end
      else if ((write_strobe_count >= 2) && (in_pointer + 1 == last)) begin
        write_available       <=  0;
        if (allow_overflow) begin
          out_pointer           <=  out_pointer + (write_strobe_count - 1);
        end
        else begin
          //only go up to 1
          fifo[in_pointer]      <=  write_data0;
          in_pointer            <=  in_pointer  + 1;
          overflow              <=  1;
        end
        overflow              <=  1;
      end
      else if ((write_strobe_count >= 3) && (in_pointer + 2 == last)) begin
        write_available       <=  0;
        if (allow_overflow) begin
          out_pointer           <=  out_pointer + (write_strobe_count - 2);
        end
        else begin
          //only go up to 2
          fifo[in_pointer]      <=  write_data0;
          fifo[in_pointer + 1]  <=  write_data1;
          in_pointer            <=  in_pointer + 2;
        end
        overflow              <=  1;
      end
      else if ((write_strobe_count == 4) && (in_pointer + 3 == last)) begin
        write_available       <=  0;
        if (allow_overflow) begin
          //only go up to 3
          fifo[in_pointer]      <=  write_data0;
          fifo[in_pointer + 1]  <=  write_data1;
          fifo[in_pointer + 2]  <=  write_data2;
          fifo[in_pointer + 3]  <=  write_data3;
          in_pointer            <=  in_pointer + 4;
        end
        else begin
          fifo[in_pointer]      <=  write_data0;
          fifo[in_pointer + 1]  <=  write_data1;
          fifo[in_pointer + 2]  <=  write_data2;
          out_pointer           <=  out_pointer + 3;
        end
        overflow                <=  1;
      end
      //no restrictions
*/
//      else begin
        if (write_strobe_count == 1) begin
          write_available       <=  0;
          $display("Writing without restrictions");
          fifo[in_pointer]      <=  write_data0;
          in_pointer            <=  in_pointer  + 1;
        end
        else if (write_strobe_count == 2) begin
          $display("Writing without restrictions");
          fifo[in_pointer]      <=  write_data0;
          fifo[in_pointer + 1]  <=  write_data1;
          in_pointer            <=  in_pointer + 2;
        end
        else if (write_strobe_count == 3) begin
          fifo[in_pointer]      <=  write_data0;
          fifo[in_pointer + 1]  <=  write_data1;
          fifo[in_pointer + 2]  <=  write_data2;
          in_pointer            <=  in_pointer + 3;
        end
        else if (write_strobe_count == 4) begin
          fifo[in_pointer]      <=  write_data0;
          fifo[in_pointer + 1]  <=  write_data1;
          fifo[in_pointer + 2]  <=  write_data2;
          fifo[in_pointer + 3]  <=  write_data3;
          in_pointer            <=  in_pointer + 4;
        end
//      end
    end
 
    //if there is a read strobe read a byte from the FIFO and increment the out_pointer
    if (read_strobe) begin
      if (!empty) begin
//XXX: There is an edge case when a read_strobe happens on the same edge a a write strobe
//XXX: Basically the out pointer will be messed up
        out_pointer           <=  out_pointer + 1;
      end
      else begin
        underflow             <=  1;
      end
    end
  end
end 


endmodule
