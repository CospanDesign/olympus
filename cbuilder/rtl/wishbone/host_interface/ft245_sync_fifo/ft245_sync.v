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


output wire [7:0]  debug;


reg [7:0] debug_r;
wire [7:0]  debug_w;

//assign debug = {debug_w[5:0], debug_r[1:0]};
assign debug = debug_w; 


wire    [7:0]   data_out;

assign          ftdi_data  = (ftdi_oe_n) ? (out_cache_valid ? out_cache: data_out) : 8'hZ;
//assign          ftdi_data  = (ftdi_oe_n) ? data_out : 8'hZ;

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
reg     [7:0]   out_cache;
reg             out_cache_valid;
reg             data_valid;
reg             local_sof;
//reg             finish_flag;


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
parameter                   FIFO_WAIT       = 4'h3;


assign debug_w[1:0] = rstate;
assign debug_w[2] = start_of_frame;
assign debug_w[3] = in_fifo_wr;
assign debug_w[4] = in_fifo_full;
assign debug_w[5] = in_fifo_empty;
assign debug_w[6] = in_fifo_rd;
assign debug_w[7] = (in_fifo_data == 7'h08); 
//assign debug_w[2] = out_fifo_empty;
//assign debug_w[3] = out_fifo_rd;
//assign debug_w[4] = out_cache_valid;
//assign debug_w[5] = out_fifo_full;


reg [7:0]                   current_byte;
reg [7:0]                   next_byte;

always @ (posedge ftdi_clk) begin

  if (rst) begin
    output_enable         <=  0;
    read_enable           <=  0;
    rstate                 <=  IDLE;

    start_of_frame        <=  0;

    in_fifo_wr            <=  0;
    data_in               <=  0;
    local_sof             <=  0;
    cache_data            <=  8'h00;
    data_valid            <=  0;

    current_byte          <=  8'h0;
    next_byte             <=  8'h0;

    end
  else begin
    in_fifo_wr                <=  0;
    case (rstate)
      IDLE: begin
        output_enable         <=  0;
        read_enable           <=  0;

        start_of_frame        <=  0;

        if (receive_available && !in_fifo_full &&!write_busy) begin
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
        if (receive_available && !in_fifo_full) begin
          //output enable has been low for one clock cycle so start reading
          read_enable         <=  1;
          rstate               <=  READ;
        end
        else begin
          //receive available is not ready, go to IDLE
          rstate               <=  IDLE;
        end
      end
      READ: begin
        //save the current data just in case the in FIFO is full
        cache_data            <=  data_in;
        data_in               <=  ftdi_data;
//XXX: There can be a nicer way to do this
        local_sof             <=  start_of_frame;
        start_of_frame        <=  0;
        if (!receive_available) begin
          //FT245 has no more data
          data_valid          <=  0;
          output_enable       <=  0;
          rstate               <=  IDLE;
        end
        else begin
          if (in_fifo_full) begin
            data_valid        <=  1;
            read_enable       <=  0;
            rstate             <=  FIFO_WAIT;
          end
          else begin
            //Contine reading
            in_fifo_wr        <=  1;
            data_valid        <=  0;
            read_enable       <=  1;
          end
        end
      end
      FIFO_WAIT: begin
        //more data an be put into the incomming FIFO
        if (!in_fifo_full) begin
          if (data_valid) begin
            //data stored in the cache can be written to the FIFO
            in_fifo_wr      <=  1;
            data_in         <=  cache_data;
            data_valid      <=  0;
          end
          if (receive_available) begin
            //more data to read so go back to the read rstate
            rstate           <=  READ;
          end
          else begin
            //there is n more data and hte FIFO is not full anymore
            rstate           <=  IDLE;
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


reg                         prev_transmit_ready;
wire t_ready_sync;
assign  t_ready_sync      =  (transmit_ready && prev_transmit_ready);

parameter                   WRITE               = 4'h1;
parameter                   FT245_WAIT          = 4'h2;
parameter                   FT245_WAIT_FINISH   = 4'h3;
//assign debug_w[1:0] = wstate[1:0];

always @ (posedge ftdi_clk) begin
  if (rst) begin
    wstate                <=  IDLE;
    write_enable          <=  0;
    send_immediately      <=  0;
    out_fifo_rd           <=  0;
    out_cache             <=  8'h00;
    out_cache_valid       <=  0;
    //finish_flag           <=  0;
    debug_r                 <=  3'h0;
    prev_transmit_ready   <=  0;
    

  end
  else begin
//XXX: should I reset the out_fifo_rd?
    out_fifo_rd               <=  0;
    send_immediately          <=  0;
    write_enable              <=  0;

    case (wstate)
      IDLE: begin
        if (t_ready_sync && !out_fifo_empty) begin
          //Writing to the host

          //it takes 1 clock cycle to get data from the host
          out_fifo_rd         <=  1;
          wstate               <=  WRITE;
        end
      end
      WRITE: begin
        if (transmit_ready) begin
          if (out_fifo_empty) begin
debug_r[0]  <=  ~debug_r[0];
            //Transmitter is ready but there is no data in the FIFO
            out_fifo_rd       <=  0;
//XXX: There might be data in here from the previous read, but there is no data for the NEXT read
            write_enable      <=  0;
            wstate             <=  IDLE;
//XXX: This is the last data sent
            //debug_r[0]          <=  ~debug_r[0];
          end
          else begin
            //FT245 is ready and the FIFO is ready and not empty
//XXX: This happens so often that I don't need this
            out_fifo_rd       <=  1;
            write_enable      <=  1;
          end
        end
        else begin //trasmitter is not ready
//***This is where all the problems start

          //the write FIFO data is ready to transmit
          out_fifo_rd         <=  0;
          //disable writing to the output FIFO
          write_enable        <=  0;
          out_cache           <=  data_out;
          out_cache_valid     <=  1;
          if (out_fifo_empty) begin
 //           finish_flag       <=  1;
            wstate            <=  FT245_WAIT_FINISH;
          end
          else begin
            wstate            <=  FT245_WAIT;
          end
        end
      end
      FT245_WAIT: begin
//***Problems happen in here
        write_enable  <=  0;
        if (t_ready_sync) begin
          //transmitter is ready again
          write_enable        <=  1;
          if (write_enable) begin
            out_cache_valid <= 0;
debug_r[1]  <=  ~debug_r[1];
            if (out_fifo_empty) begin
//XXX: this doesn't seem to ever happen but it could happen that after the
//cache is empty the out_fifo could be empty
              write_enable  <=  0;
                
              wstate         <=  IDLE;
            end
            else begin
//THIS HAPPENS A LOT!
//              
              out_fifo_rd   <=  0;
              wstate         <=  IDLE;
            end
          end
        end
      end
      FT245_WAIT_FINISH: begin
        write_enable  <=  0;
        if (t_ready_sync) begin
          //transmitter is ready again
          write_enable        <=  1;
          if (write_enable) begin
            out_cache_valid <= 0;

//MAYBE THIS GETS THING ONE STEP BEHND??

//XXX: I think this is where something might go wrong
//SOMETIMES  when I'm in here I don't write out data

            write_enable  <= 0;
            //finish_flag   <= 0;
//this got passed 254

//when I changed this to go into WRITE it broke :(
            wstate         <=  IDLE;
              
//***: It doesn't ever seem to go to "out_fifo_empty" here


//                if (out_fifo_empty) begin
//XXX: this doesn't seem to happen
//                  
//                  debug_r[0]      <=  ~debug_r[0];
//                end
//                else begin
//                  debug_r[1]      <=  ~debug_r[1];
//                end
          end
        end
      end

      default: begin
        wstate  <=  IDLE;
      end
    endcase
    prev_transmit_ready <=  transmit_ready;
  end
end

endmodule
