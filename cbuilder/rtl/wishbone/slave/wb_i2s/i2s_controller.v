//i2s_controllerv
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


module i2s_controller (
  rst,
  clk,

  enable,

  clock_divider,

  request_data,
  request_size,
  request_finished,
  memory_data,
  memory_data_strobe,

  i2s_clock,
  i2s_data,
  i2s_lr
);

input               rst;
input               clk;

input               enable;
output              starved;


input       [31:0]  clock_divider;


output              request_data;
output      [23:0]  request_size;
input               request_finished;
input       [31:0]  memory_data;
input               memory_data_strobe;

output  reg         i2s_clock = 0;
output              i2s_data;
output              i2s_lr;

//registers/wires
reg         [31:0]  clock_count = 0;

wire                audio_data_request;
wire                audio_data_ack;
wire        [23:0]  audio_data;
wire                audio_lr_bit;

//sub modules
i2s_mem_controller mcontroller (
  .rst(rst),
  .clk(clk),

  //control
  .enable(enable),

  //clock
  .i2s_clock(i2s_clock),

  //memory interface
  .request_data(request_data),
  .request_size(request_size),
  .request_finished(request_finished),
  .memory_data(memory_data),
  .memory_data_strobe(memory_data_strobe),

  //i2s writer
  .audio_data_request(audio_data_request),
  .audio_data_ack(audio_data_ack),
  .audio_data(audio_data),
  .audio_lr_bit(audio_lr_bit)
);

i2s_writer writer(
  .rst(rst),
  .clk(clk),

  //control/clock
  .enable(enable),
  .starved(starved),

  //i2s clock
  .i2s_clock(i2s_clock),

  //i2s writer
  .audio_data_request(audio_data_request),
  .audio_data_ack(audio_data_ack),
  .audio_data(audio_data),
  .audio_lr_bit(audio_lr_bit),

  //i2s audio interface
  .i2s_data(i2s_data),
  .i2s_lr(i2s_lr)
);

//asynchronous logic

//synchronous logic
//clock generator
always @(posedge clk) begin
  if (clock_count == clock_divider) begin
    i2s_clock     <=  ~i2s_clock;
    clock_count   <= 0;
  end
  else begin
    clock_count   <=  clock_count + 1;
  end
end

endmodule
