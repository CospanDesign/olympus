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


wire    [7:0]   data_out;

assign          ftdi_data  = (ftdi_oe_n) ? data_out : 8'hZ;


//wires

reg             start_of_frame;
reg             in_fifo_wr;
wire            in_fifo_full;

wire            out_fifo_full;
wire            out_fifo_empty;
reg             out_fifo_rd;
wire            out_fifo_wr;

reg     [7:0]   data_in;
reg     [7:0]   cache_data;
reg             data_valid;
reg             local_sof;


afifo #(
  .DATA_WIDTH(9),
  .ADDRESS_WIDTH(10)
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
    .rd_en(out_fifo_rd),
    .empty(out_fifo_empty),

    .din_clk(clk),
    .data_in(out_fifo_data),
    .wr_en(out_fifo_wr),
    .full(out_fifo_full)
);


parameter                   IDLE            = 4'h0;
parameter                   EMPTY_IN_CACHE  = 4'h1;
parameter                   ENABLE_READING  = 4'h2;
parameter                   READ            = 4'h3;
parameter                   FIFO_WAIT       = 4'h4;
parameter                   FT245_WAIT      = 4'h5;
parameter                   WRITE           = 4'h6;


reg [3:0]                   state; 

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


always @ (posedge ftdi_clk) begin
  
  if (rst) begin
    output_enable         <=  0;
    read_enable           <=  0;
    write_enable          <=  0;
    send_immediately      <=  0;
    state                 <=  IDLE;

    start_of_frame        <=  0;

    in_fifo_wr            <=  0;
    out_fifo_rd           <=  0;
    data_in               <=  0;
    local_sof             <=  0;
    cache_data            <=  8'h00;
    data_valid            <=  0;
    
  end
  else begin
    //pulses 
    in_fifo_wr            <=  0;
    out_fifo_rd           <=  0;

    case (state)
      IDLE: begin
        output_enable     <=  0;
        write_enable      <=  0;
        read_enable       <=  0;
        send_immediately  <=  0;

        start_of_frame    <=  0;

       if (receive_available && !in_fifo_full) begin
          //Reading from the host
          output_enable   <=  1;
          if (!prev_receive_available) begin
            //the start of frame is the beginning of a transition
            start_of_frame  <=  1;
          end
          state           <=  ENABLE_READING;
        end
        else if (transmit_ready  && !out_fifo_empty) begin
          //Writing to the host
          out_fifo_rd     <=  1;
          state           <= WRITE;
          //it takes 1 clock cycle to start reading from the FIFO
        end
      end
      ENABLE_READING: begin
        if (receive_available && !in_fifo_full) begin
          read_enable     <=  1;
          state           <=  READ;
        end
        else begin
          state           <=  IDLE;
        end
      end
      READ: begin
        cache_data        <=  data_in;
        data_in           <=  ftdi_data;
//XXX:  There can be a nicer way to do this
        local_sof         <=  start_of_frame;

        start_of_frame    <=  0;
        if (!receive_available) begin
          data_valid      <=  0;
          state           <=  IDLE;
          output_enable   <=  0;
        end
        else begin
          if (in_fifo_full) begin
            //just put down read_enable until the fifo is ready again
            data_valid      <=  1;
            state           <=  FIFO_WAIT;
            read_enable     <=  0;
          end
          else begin
            //continue reading
            in_fifo_wr      <=  1;
            data_valid      <=  0;
            read_enable     <=  1;
          end
        end
      end
      FIFO_WAIT: begin
        if (!in_fifo_full) begin
          if (data_valid) begin
            in_fifo_wr        <=  1;
            data_in           <=  cache_data;
            data_valid        <=  0;
          end
          if (receive_available) begin
            state             <=  READ;
          end
          else begin
            state             <=  IDLE;
          end
        end
      end
      FT245_WAIT: begin
        if (transmit_ready) begin
          write_enable        <=  1;
          //out_fifo_rd         <=  1;
          state               <=  WRITE;
        end
      end
      WRITE: begin
        if (transmit_ready) begin
          if (out_fifo_empty) begin
            out_fifo_rd       <=  0;
            write_enable      <=  0;
            state             <=  IDLE;
          end
          else begin
            out_fifo_rd       <=  1;
            write_enable      <=  1;
          end
        end
        else begin //transmitter is not ready
          out_fifo_rd         <=  0;
          write_enable        <=  0;
          if (out_fifo_empty) begin
            state             <=  IDLE;
          end
          else begin
            state             <=  FT245_WAIT;
          end
          
        end
      end
      default: begin
        state <=  IDLE;
      end
    endcase
  end
  prev_receive_available   <=  receive_available;
end

endmodule

