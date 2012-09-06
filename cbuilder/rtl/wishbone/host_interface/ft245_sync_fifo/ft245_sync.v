//ft245_sync_fifo.v

`timescale 1ns/1ps

module ft245_sync_fifo (
  rst,
  clk,

  //in fifo
  in_fifo_rst,
  in_fifo_rd,
  in_fifo_empty,
  in_fifo_data,
  sof,

  //out fifo
  out_fifo_wr,
  out_fifo_full,
  out_fifo_data,


  //phy interface
  ftdi_clk,
  ftdi_data,
  ftdi_txe_n,
  ftdi_wr_n,
  ftdi_rde_n,
  ftdi_rd_n,
  ftdi_oe_n,
  ftdi_suspend_n,
  ftdi_siwu,

  debug,


);
//host interface
input           clk;
input           rst;

//in fifo
input           in_fifo_rst;
input           in_fifo_rd;
output wire     in_fifo_empty;
output  [7:0]   in_fifo_data;
output          sof;

//out fifo
input           out_fifo_wr;
output          out_fifo_full;
input   [7:0]   out_fifo_data;

//ftdi
input           ftdi_clk;
inout   [7:0]   ftdi_data;
input           ftdi_txe_n;
output wire     ftdi_wr_n;
input           ftdi_rde_n;
output wire     ftdi_rd_n;
output wire     ftdi_oe_n;
output wire     ftdi_siwu;
input           ftdi_suspend_n;


output wire [15:0]          debug;


reg [15:0]                  debug_r;
wire [15:0]                 debug_w;

//assign debug = {debug_w[5:0], debug_r[1:0]};
assign                      debug = debug_w; 
//assign  debug = debug_r;


wire    [7:0]               data_out;

assign                      ftdi_data  = ftdi_oe_n ? data_out : 8'hZ;
//assign          ftdi_data  = (ftdi_oe_n) ? data_out : 8'hZ;

//wires

reg                         start_of_frame;
reg                         in_fifo_wr;
wire                        in_fifo_full;

wire                        out_fifo_full;
wire                        out_fifo_empty;
reg                         out_fifo_rd;
wire                        out_fifo_wr;



reg     [7:0]               data_in;
reg     [7:0]               out_cache;
reg                         out_cache_valid;
reg                         local_sof;
//reg                         finish_flag;


reg [2:0]                   rstate; 
reg [1:0]                   wstate; 

wire                        recieve_available;
wire                        transmit_ready;
reg                         output_enable;
reg                         read_enable;
reg                         write_enable;
reg                         send_immediately;
reg                         prev_receive_available;

assign  ftdi_oe_n         = ~output_enable;
assign  ftdi_rd_n         = ~read_enable;
assign  ftdi_wr_n         = ~write_enable;
assign  receive_available = ~ftdi_rde_n;
assign  transmit_ready    = ~ftdi_txe_n;
assign  ftdi_siwu         = ~send_immediately;

wire    write_busy        = (wstate != IDLE) || (!out_fifo_empty);
wire    read_busy         = (rstate != IDLE);

`define TEST

afifo #(
  .DATA_WIDTH(9),
`ifndef TEST
  .ADDRESS_WIDTH(10)
`else
  .ADDRESS_WIDTH(10)
`endif
  )
  fifo_in (
    .rst(rst || in_fifo_rst),

    .dout_clk(clk),
    .data_out({sof, in_fifo_data}),
    .rd_en(in_fifo_rd),
    .empty(in_fifo_empty),



    .din_clk(ftdi_clk),
    .data_in({local_sof, data_in}),
    .wr_en(in_fifo_wr),
    .full(in_fifo_full)
);


afifo #(
  .DATA_WIDTH(8),
  .ADDRESS_WIDTH(10)
  )
  fifo_out (
    .rst(rst),

    .dout_clk(ftdi_clk),
    .data_out(data_out),
//    .rd_en(out_fifo_rd && transmit_ready),
    .rd_en(out_fifo_rd),
    .empty(out_fifo_empty),

    .din_clk(clk),
    .data_in(out_fifo_data),
    .wr_en(out_fifo_wr),
    .full(out_fifo_full)
);


parameter                   IDLE            = 4'h0;
parameter                   ENABLE_READING  = 4'h1;
parameter                   READ            = 4'h2;
parameter                   SEND_TO_FIFO    = 4'h3;


assign debug_w[2:0]   = rstate;
assign debug_w[3]     = in_fifo_wr;
assign debug_w[4]     = in_fifo_full;
assign debug_w[5]     = in_fifo_rd;
assign debug_w[6]     = in_fifo_empty;
assign debug_w[7]     = sof;
assign debug_w[15:8]  = data_in;

//assign debug_w[2] = out_fifo_empty;
//assign debug_w[3] = out_fifo_rd;
//assign debug_w[4] = out_cache_valid;
//assign debug_w[5] = out_fifo_full;

reg [7:0]       ftdi_buffer;

reg             read_available;
reg             read;


reg [8:0]       fifo_read_data;

always @ (posedge ftdi_clk) begin

  if (rst) begin
    output_enable             <=  0;
    read_enable               <=  0;
    rstate                    <=  IDLE;
    start_of_frame            <=  0;
    ftdi_buffer               <=  8'h00;
    read_available            <=  0;
  end
  else begin
    case (rstate)
      IDLE: begin
        output_enable         <=  0;
        read_enable           <=  0;

        start_of_frame        <=  0;

        if (receive_available && !write_busy) begin
          //Reading from the host
          if (!prev_receive_available) begin
            start_of_frame    <=  1;
          end
          output_enable       <=  1;
          //it takes 1 clock cycle to start reading to the FIFO
          rstate               <=  ENABLE_READING;
        end
      end
      ENABLE_READING: begin
        read_enable          <=  1;
        rstate               <=  READ;
      end
      READ: begin
        read_enable           <=  0;
        fifo_read_data        <=  {start_of_frame, ftdi_data};
        start_of_frame        <=  0;
        read_enable           <=  0;
        ftdi_buffer           <=  ftdi_data;
        rstate                <=  SEND_TO_FIFO;
        read_available        <=  1;
      end
      SEND_TO_FIFO: begin
        if (read) begin
          read_available      <=  0;
          if (!receive_available) begin
            read_enable       <=  0;
            rstate            <=  IDLE;
          end
          else begin
            read_enable       <=  1;
            rstate            <=  READ;
          end
        end
      end
      default: begin
        $display ("FT245: Entered illegal rstate");
        rstate <=  IDLE;
      end
    endcase
  end
  prev_receive_available  <=  receive_available;
end


reg [1:0]                   fstate;
reg [8:0]                   fifo_buffer;

//IN FIFO CONTROLLER
parameter                   WRITE_TO_FIFO   = 4'h1;

always @ (posedge ftdi_clk) begin
  if (rst) begin
    in_fifo_wr            <=  0;
    read                  <=  0;
    data_in               <=  8'h00;
    fifo_buffer           <=  9'h000;
    local_sof             <=  0;
  end
  else begin
    in_fifo_wr            <=  0;
    read                  <=  0;
    case (fstate)
      IDLE: begin
        if (!in_fifo_full && read_available) begin
          read            <=  1;
          fifo_buffer     <=  fifo_read_data;
          fstate          <=  WRITE_TO_FIFO;
        end
      end
      WRITE_TO_FIFO: begin
        local_sof         <=  fifo_buffer[8];
        data_in           <=  fifo_buffer[7:0];
        in_fifo_wr        <=  1;
        fstate            <=  IDLE;
      end
      default: begin
        fstate            <=  IDLE;
      end
    endcase
  end
end


reg                         prev_transmit_ready;
wire t_ready_sync;
assign  t_ready_sync      =  (transmit_ready && prev_transmit_ready);

parameter                   WRITE               = 4'h1;
parameter                   GET_WRITE_DATA      = 4'h2;
parameter                   SLEEP               = 4'h3;

always @ (posedge ftdi_clk) begin
  if (rst) begin
    wstate                    <=  IDLE;
    write_enable              <=  0;
    send_immediately          <=  0;
    out_fifo_rd               <=  0;
  end
  else begin
    write_enable              <=  0;
    send_immediately          <=  0;
    out_fifo_rd               <=  0;
    case (wstate)
      IDLE: begin
        if (!read_busy && !out_fifo_empty && transmit_ready) begin
          out_fifo_rd         <=  1;
          wstate              <=  GET_WRITE_DATA;
        end
      end
      GET_WRITE_DATA: begin
        if (transmit_ready) begin
          wstate                <=  WRITE;
        end
      end
      WRITE: begin
        if (transmit_ready) begin
          write_enable          <=  1;
          wstate                <= SLEEP;
        end
      end
      SLEEP: begin
        wstate                <=  IDLE;
      end
      default: begin
        wstate                <=  IDLE;
      end
    endcase
  end
end

endmodule
