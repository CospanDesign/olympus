//wishbone master interconnect testbench
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

module waveform(
  clk,
  rst,
  wavelength,
  pos,
  value
);

input               clk;
input               rst;
input       [7:0]   pos;
output      [7:0]   wavelength;
output reg  [15:0]  value;


parameter WAVELENGTH = 44;

assign  wavelength = WAVELENGTH;

//register
reg [15:0] wave [WAVELENGTH:0];

initial begin
  wave[0] <=  16'h0000;
  wave[1] <=  16'h1237; 
  wave[2] <=  16'h240F;
  wave[3] <=  16'h352C;
  wave[4] <=  16'h4533;
  wave[5] <=  16'h53D2;
  wave[6] <=  16'h60BC;
  wave[7] <=  16'h6BAE;
  wave[8] <=  16'h746E;
  wave[9] <=  16'h7AD0;
  wave[10] <=  16'h7EB2;
  wave[11] <=  16'h7FFF;
  wave[12] <=  16'h7EB2;
  wave[13] <=  16'h7AD0;
  wave[14] <=  16'h746E;
  wave[15] <=  16'h6BAE;
  wave[16] <=  16'h60BC;
  wave[17] <=  16'h53D2;
  wave[18] <=  16'h4533;
  wave[19] <=  16'h352C;
  wave[20] <=  16'h240F;
  wave[21] <=  16'h1237;
  wave[22] <=  16'h0000;
  wave[23] <=  16'hEDC9;
  wave[24] <=  16'hDBF1;
  wave[25] <=  16'hCAD4;
  wave[26] <=  16'hBACD;
  wave[27] <=  16'hAC2E;
  wave[28] <=  16'h9F43;
  wave[29] <=  16'h9452;
  wave[30] <=  16'h8B92;
  wave[31] <=  16'h8530;
  wave[32] <=  16'h814E;
  wave[33] <=  16'h8001;
  wave[34] <=  16'h814E;
  wave[35] <=  16'h8530;
  wave[36] <=  16'h8B92;
  wave[37] <=  16'h9452;
  wave[38] <=  16'h9F43;
  wave[39] <=  16'hAC2E;
  wave[40] <=  16'hBACD;
  wave[41] <=  16'hCAD4;
  wave[42] <=  16'hDBF1;
  wave[43] <=  16'hEDC9;
end

always @ (posedge clk) begin
  if (rst) begin
    value <= 0;
  end
  else begin
    value <=  wave[pos];
  end
end

endmodule
