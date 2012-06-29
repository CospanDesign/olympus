//ft245_sync_fifo.v


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
wire    [7:0]   data_in;

assign          ftdi_data  = (ftdi_oe_n) ? (out_cache_available) ? out_cache_data : data_out:8'hZ;
assign          data_in = (in_cache_available) ? in_cache_data : ftdi_data;


//wires

reg             start_of_frame;
reg             in_fifo_wr;
wire            in_fifo_full;

wire            out_fifo_full;
wire            out_fifo_empty;
reg             out_fifo_rd;
wire            out_fifo_wr;

//data that will be read from the FTDI chip (in)
afifo #(    
   .DATA_WIDTH(9),
   .ADDRESS_WIDTH(8)
  )
fifo_in (
  .rst(in_fifo_rst),

  .din_clk(ftdi_clk),
  .dout_clk(clk),

  .data_in({start_of_frame, data_in}),
  .data_out({sof, in_fifo_data}),
  .full(in_fifo_full),
  .empty(in_fifo_empty),

  .wr_en(in_fifo_wr),
  .rd_en(in_fifo_rd)

);
//data that will be sent to the FTDI chip (out)
afifo 
  #(    
    .DATA_WIDTH(8),
    .ADDRESS_WIDTH(8)
  )
  fifo_out (
  .rst(rst),

  .din_clk(clk),  
  .dout_clk(ftdi_clk),

  .data_in(out_fifo_data),
  .data_out(data_out),
  .full(out_fifo_full),
  .empty(out_fifo_empty),

  .wr_en(out_fifo_wr),
  .rd_en(out_fifo_rd)
);

parameter                   IDLE            = 4'h0;
parameter                   EMPTY_IN_CACHE  = 4'h1;
parameter                   ENABLE_READING  = 4'h2;
parameter                   READ            = 4'h3;
parameter                   GET_FIFO_DATA   = 4'h4;
parameter                   WRITE           = 4'h5;

reg [3:0]                   state; 

wire                        recieve_available;
wire                        transmit_ready;
reg                         output_enable;
reg                         read_enable;
reg                         write_enable;
reg                         send_immediately;

reg   [7:0]                 out_cache_data;
reg                         out_cache_available;

reg   [7:0]                 in_cache_data;
reg                         in_cache_available;

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
    out_cache_available   <=  0;
    out_cache_data        <=  8'h0;
    in_cache_available    <=  0;
    in_cache_data         <=  8'h0;
    state                 <=  IDLE;

    start_of_frame        <=  0;

    in_fifo_wr            <=  0;
    out_fifo_rd           <=  0;
    
  end
  else begin
    //pulses 
    in_fifo_wr            <= 0;
    out_fifo_rd           <= 0;

    case (state)
      IDLE: begin
        output_enable     <=  0;
        write_enable      <=  0;
        read_enable       <=  0;
        send_immediately  <=  0;

        start_of_frame    <=  0;

        if (in_cache_available && !in_fifo_full) begin
          //empty out data that is in the cache
          state           <=  EMPTY_IN_CACHE; 
          in_fifo_wr      <=  1;
        end
        else if (receive_available && !in_fifo_full) begin
          //Reading from the host
          output_enable   <=  1;
          start_of_frame  <=  1;
          state           <=  ENABLE_READING;
        end
        else if (transmit_ready  && ~out_fifo_empty) begin
          //Writing to the host
          out_fifo_rd     <=  1;
          if (out_cache_available) begin
            //left over data from a previous write
            state         <=  WRITE;
          end
          else begin
            state         <=  GET_FIFO_DATA;
          end
          //it takes 1 clock cycle to start reading from the FIFO
        end
      end
      EMPTY_IN_CACHE: begin
        in_cache_available  <=  0;
        state               <=  IDLE;
      end
      ENABLE_READING: begin
//XXX: Should I start writing here?
        in_fifo_wr        <=  1;
        read_enable       <=  1;
        state             <=  READ;
      end
      READ: begin
        start_of_frame    <=  0;
        if (!receive_available || in_fifo_full) begin
          if (in_fifo_full) begin
            //this data won't be written to the in fifo until
            //the in fifo is not full
            in_cache_data     <=  data_in;
            in_cache_available<=  1;
          end
          //finished
          output_enable   <=  0;
          read_enable     <=  0;
          state           <=  IDLE;
        end
        else begin
          //continue reading
          read_enable     <=  1;
          in_fifo_wr      <=  1;
        end
      end
      GET_FIFO_DATA: begin
        //need to wait a clock cyle to get the data
        if (!out_fifo_empty) begin
          out_fifo_rd   <=  1;
        end
        write_enable    <=  1;
        state           <=  WRITE;
      end
      WRITE: begin
        if (transmit_ready) begin
          write_enable            <=  1;
          //the writing of cache or regular data is handled above by an assign
          out_cache_available     <=  0;
          if (~out_fifo_empty) begin
            //continue reading from the output buffer
            out_fifo_rd           <=  1;
          end
          else begin
            //empty out whats in the FTDI buffer
            //send_immediately      <=  1;
            state                 <=  IDLE;
          end
        end
        else begin
          //still have data to send out from the last time
          //need to store that somewhere
          out_cache_data          <=  data_out;
          out_cache_available     <=  1;
          write_enable            <=  0;
          state                   <=  IDLE;
        end
      end
      default: begin
        state <=  IDLE;
      end
    endcase
  end
end

endmodule

