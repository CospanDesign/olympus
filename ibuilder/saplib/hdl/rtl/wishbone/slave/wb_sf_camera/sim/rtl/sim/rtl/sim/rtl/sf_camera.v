//sf_camera.v
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


module sf_camera(
  clk,
  rst,

  out_clk,
  enable,
  reset,
  vblank,
  hblank,
  cam_clk,
  data,

  //control
  control_enable,

  //status
  image_finished,

  //memory output
  memory_data,
  memory_write,

  //clok clock_divisor
  clock_divisor
);

input               clk;
input               rst;

//camera I/O
output reg          out_clk;
output reg          enable;
output reg          reset;
input               vblank;
input               hblank;
input               cam_clk;
input       [7:0]   data;

//Control
input               control_enable;

//Status
output reg          image_finished;

//Memory data
output reg  [31:0]  memory_data;
output reg          memory_write;

//Clock Divisor
input       [31:0]  clock_divisor;


//Registers/Wires
reg         [31:0]  clock_count;

reg                 vblank_sync;
reg                 hblank_sync;
reg         [7:0]   data_sync;


//Assigns
wire                vblank_stat;
wire                vblank_end;
wire                hblank_start;
wire                hblank_stop;



//blocks


//synchronize the data to this clock domain
always @ (posedge clk) begin
  if (rst) begin
    vblank_sync <=  0;
    hblank_sync <=  0;
    data_sync   <=  0;
  end
  else begin
    vblank_sync <=  vblank;
    hblank_sync <=  hblank;
    data_sync   <=  data;
  end
end


always @ (posedge clk) begin
  if (rst) begin
    image_finished      <=  0;
    memory_data         <=  0;
    memory_write        <=  0;
    enable              <=  0;
    reset               <=  0;
  end
  else begin
    
  end
end

//Clock Divider
always @(posedge clk) begin
  if (rst) begin
    clock_count   <=  clock_divisor;
    out_clk       <=  0;
  end
  else begin
    if (clock_count == 0) begin
      clock_count <= clock_divisor;
      out_clk     <=  ~out_clk;
    end
    else begin
      clock_count <= clock_count - 1;
    end
  end
end


endmodule
