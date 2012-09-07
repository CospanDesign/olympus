//wb_i2c.v

/////////////////////////////////////////////////////////////////////
////                                                             ////
////  WISHBONE revB.2 compliant I2C Master controller Top-level  ////
////                                                             ////
////                                                             ////
////  Author: Richard Herveille                                  ////
////          richard@asics.ws                                   ////
////          www.asics.ws                                       ////
////                                                             ////
////  Downloaded from: http://www.opencores.org/projects/i2c/    ////
////                                                             ////
/////////////////////////////////////////////////////////////////////
////                                                             ////
//// Copyright (C) 2001 Richard Herveille                        ////
////                    richard@asics.ws                         ////
////                                                             ////
//// This source file may be used and distributed without        ////
//// restriction provided that this copyright statement is not   ////
//// removed from the file and that any derivative work contains ////
//// the original copyright notice and the associated disclaimer.////
////                                                             ////
////     THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY     ////
//// EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED   ////
//// TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS   ////
//// FOR A PARTICULAR PURPOSE. IN NO EVENT SHALL THE AUTHOR      ////
//// OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,         ////
//// INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES    ////
//// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE   ////
//// GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR        ////
//// BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF  ////
//// LIABILITY, WHETHER IN  CONTRACT, STRICT LIABILITY, OR TORT  ////
//// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT  ////
//// OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         ////
//// POSSIBILITY OF SUCH DAMAGE.                                 ////
////                                                             ////
/////////////////////////////////////////////////////////////////////

/*
  Adapted from OpenCores I2C project
  Author: dave.mccoy@cospandesign.com
*/


/*
  Use this to tell sycamore how to populate the Device ROM table
  so that users can interact with your slave

  META DATA

  identification of your device 0 - 65536
  DRT_ID:  3

  flags (read drt.txt in the slave/device_rom_table directory 1 means
  a standard device
  DRT_FLAGS:  1

  number of registers this should be equal to the nubmer of ADDR_???
  parameters
  DRT_SIZE:  7

*/

`include "project_defines.v"
`include "timescale.v"

`define CLK_DIVIDE_100KHZ (`CLOCK_RATE/(5 * 100000) - 1)
`define CLK_DIVIDE_400KHZ (`CLOCK_RATE/(5 * 400000) - 1)


module wb_i2c (
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

  scl,
  sda
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

inout               scl;
inout               sda;

parameter           ADDR_CONTROL        = 32'h00000000;
parameter           ADDR_STATUS         = 32'h00000001;
parameter           ADDR_CLOCK_RATE     = 32'h00000002;
parameter           ADDR_CLOCK_DIVIDER  = 32'h00000003;
parameter           ADDR_COMMAND        = 32'h00000004;
parameter           ADDR_TRANSMIT       = 32'h00000005;
parameter           ADDR_RECEIVE        = 32'h00000006;


//Registers/Wires
reg         [15:0]  clock_divider;
reg         [7:0]   control;
reg         [7:0]   transmit;
wire        [7:0]   receive;
reg         [7:0]   command;
wire        [7:0]   status;


wire                done;

//core enable signal
wire                core_en;
wire                ien;

//Control Register bits
wire                start;
wire                stop;
wire                read;
wire                write;
wire                ack;
reg                 iack;


//Status Register
wire                irxack;
reg                 rxack;      //Received acknowledge from slave
reg                 tip;        //Tranfer in progress
reg                 irq_flag;   //interrupt pending flag
wire                i2c_busy;   //busy (start sigal detected)
wire                i2c_al;     //arbitration lost
reg                 al;         //arbitration lost


//Assigns
//Command
assign  start               = command[0];
assign  stop                = command[1];
assign  read                = command[2];
assign  write               = command[3];
assign  ack                 = command[4];

// Control
assign  core_en             = control[0];
assign  ien                 = control[1];
assign  set_100khz          = control[2];
assign  set_400khz          = control[3];

// assign status register bits
assign status[7]            = rxack;
assign status[6]            = i2c_busy;
assign status[5]            = al;
assign status[4:2]          = 3'h0; // reserved
assign status[1]            = tip;
assign status[0]            = irq_flag;

assign  scl                 = scl_oen ? 1'hZ : scl_out;
assign  sda                 = sda_oen ? 1'hZ : sda_out;


i2c_master_byte_ctrl byte_controller (
  .clk      (clk),
  .rst      (rst),
  .nReset   (1),
  .ena      (core_en),
  .clk_cnt  (clock_divider),
  .start    (start),
  .stop     (stop),
  .read     (read),
  .write    (write),
  .ack_in   (ack),
  .din      (transmit),
  .cmd_ack  (done),
  .ack_out  (irxack),
  .dout     (receive),
  .i2c_busy (i2c_busy),
  .i2c_al   (i2c_al),
  .scl_i    (scl),
  .scl_o    (scl_out),
  .scl_oen  (scl_oen),
  .sda_i    (sda),
  .sda_o    (sda_out),
  .sda_oen  (sda_oen)
);

//blocks
always @ (posedge clk) begin
  if (rst) begin
    wbs_dat_o         <= 32'h0;
    wbs_ack_o         <= 0;
    wbs_int_o         <= 0;

    clock_divider     <=  `CLK_DIVIDE_100KHZ;
    control           <=  8'h01;
    transmit          <=  8'h00;
    command           <=  8'h00;

    al                <=  0;
    rxack             <=  0;
    tip               <=  0;
    irq_flag          <=  0;
    iack              <=  0;

  end
  else begin
    iack                      <=  0;
    
    //when the master acks our ack, then put our ack down
    if (wbs_ack_o & ~ wbs_stb_i)begin
      wbs_ack_o       <=  0;
      //clear IRQ ACK bit
      command[0]      <=  0;
    end

    if (wbs_stb_i & wbs_cyc_i) begin
      //master is requesting something
      wbs_int_o         <=  0;
      //acknowledge an interrupt
      iack              <=  1;
      if (wbs_we_i) begin
        //write request
        case (wbs_adr_i) 
          ADDR_CONTROL: begin
            control           <=  wbs_dat_i[7:0];
          end
          ADDR_CLOCK_DIVIDER: begin
            clock_divider         <=  wbs_dat_i[15:0];
          end
          ADDR_COMMAND: begin
            command           <=  wbs_dat_i[7:0];
          end
          ADDR_TRANSMIT: begin
            transmit          <=  wbs_dat_i[7:0];
          end
          default: begin
          end
        endcase
      end

      else begin 
        //reset the interrupt when the user reads anything
        //read request
        case (wbs_adr_i)
          ADDR_CONTROL: begin
            wbs_dat_o         <=  {24'h000000, control};
          end
          ADDR_STATUS: begin
            wbs_dat_o         <=  {24'h000000, status};
          end
          ADDR_CLOCK_RATE: begin
            wbs_dat_o         <=  `CLOCK_RATE;
          end
          ADDR_CLOCK_DIVIDER: begin
            wbs_dat_o         <=  {16'h0000, clock_divider};
          end
          ADDR_COMMAND: begin
            wbs_dat_o         <=  {24'h000000, command};
          end
          ADDR_TRANSMIT: begin
            wbs_dat_o         <=  {24'h000000, transmit};
          end
          ADDR_RECEIVE: begin
            wbs_dat_o         <=  {24'h000000, receive};
          end
          default: begin
            wbs_dat_o         <=  32'h0000000;
          end
        endcase
      end
      wbs_ack_o <= 1;
    end

    //clear the reserved bits
    command[7:5]              <=  2'b00; 

    if (set_100khz) begin
      clock_divider     <= `CLK_DIVIDE_100KHZ; 
      //reset the control so they don't keep firing off
      control[2]    <=  0; 
      control[3]    <=  0;
    end
    if (set_400khz) begin
      //reset the control so they don't keep firing off
      clock_divider     <= `CLK_DIVIDE_400KHZ;
      control[2]    <=  0; 
      control[3]    <=  0;
    end



    //control/status
    al                        <=  i2c_al | (al & ~start);
    rxack                     <=  irxack;
    tip                       <=  (read | write);

	  irq_flag <= (done | i2c_al | irq_flag) & ~iack; // interrupt request flag is always generated

    if (irq_flag && ien) begin
      //interrupt enable and irq_flag fired off
      wbs_int_o       <=  1;
    end
    //Handle Status/Control oneshots
    if (done | i2c_al) begin
      command[3:0]    <=  4'h0;
    end
  end
end


endmodule
