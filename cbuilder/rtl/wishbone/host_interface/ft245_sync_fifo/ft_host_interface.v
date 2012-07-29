//ft_host_interface.v

`timescale 1ns/1ps
module ft_host_interface (
	rst,
	clk,

	//host interface
	master_ready,
	ih_ready,

  ih_reset,

	in_command,
	in_address,
	in_data_count,
	in_data,


	//outgoing data
	oh_ready,
	oh_en,

	out_status,
	out_address,
	out_data_count,
	out_data,

	//phy interface
	ftdi_clk,
	ftdi_data,
	ftdi_txe_n,
	ftdi_wr_n,
	ftdi_rde_n,
	ftdi_rd_n,
	ftdi_oe_n,
	ftdi_siwu,
	ftdi_suspend_n,


  //debug
  debug
);


//host interface
input				        rst;
input				        clk;

input				        master_ready;
output reg			    ih_ready;
output reg          ih_reset;

output reg	[31:0]	in_command;
output reg	[27:0]	in_data_count;
output reg	[31:0]	in_address;
output reg	[31:0]	in_data;

output reg			    oh_ready;
input				        oh_en;

input		[31:0]	    out_status;
input		[31:0]	    out_address;
input		[27:0]	    out_data_count;
input		[31:0]	    out_data;

//ftdi
input				        ftdi_clk;
inout	[7:0]		      ftdi_data;
input				        ftdi_txe_n;
output				      ftdi_wr_n;
input				        ftdi_rde_n;
output 				      ftdi_rd_n;
output 				      ftdi_oe_n;
output 				      ftdi_siwu;
input				        ftdi_suspend_n;

//debug
output              [15:0]  debug;

parameter   PING  = 4'h0;
parameter   WRITE = 4'h1;
parameter   READ  = 4'h2;
parameter   RESET = 4'h3;

//fifo interface
wire				fifo_rst;
reg					in_fifo_rst = 0;
assign	    fifo_rst	=	rst | in_fifo_rst;

reg					in_fifo_rd;
wire				in_fifo_empty;
wire	[7:0] in_fifo_data;

reg					out_fifo_wr;
wire				out_fifo_full;	
reg		[7:0]		out_fifo_data;

reg		[7:0]		next_read_state;
reg		[7:0]		process_state;
reg		[7:0]		next_wstate;

reg		[31:0]  temp_data;
wire          sof;

wire  [15:0]   ft_245_debug;

//instantiate the ft245_sync core
ft245_sync_fifo sync_fifo(
	.clk(clk),
	.rst(rst),

	.in_fifo_rst(fifo_rst),
	.in_fifo_rd(in_fifo_rd),
	.in_fifo_empty(in_fifo_empty),
	.in_fifo_data(in_fifo_data),
  .sof(sof),

	.out_fifo_wr(out_fifo_wr),
	.out_fifo_full(out_fifo_full),
	.out_fifo_data(out_fifo_data),

	.ftdi_clk(ftdi_clk),
	.ftdi_data(ftdi_data),
	.ftdi_txe_n(ftdi_txe_n),
	.ftdi_wr_n(ftdi_wr_n),
	.ftdi_rde_n(ftdi_rde_n),
	.ftdi_rd_n(ftdi_rd_n),
	.ftdi_oe_n(ftdi_oe_n),
	.ftdi_siwu(ftdi_siwu),
	.ftdi_suspend_n(ftdi_suspend_n),

  .debug(ft_245_debug)

);

assign  debug = ft_245_debug;

//XXX: Possible race condition
//XXX: Will the assembler hold the data for the HOST - > MASTER read path?
wire                  read_busy;
assign                read_busy = (rstate != IDLE);

wire                  write_busy;
assign                write_busy  = (wstate != IDLE);

//Host -> Master DW Assembler Register
reg                   reset_read_state;
reg [31:0]            working_dw;
reg [1:0]             byte_count;
reg                   dw_ready;
reg                   reset_assembler;
reg [31:0]            read_dw;


reg                   read_ack;

parameter             READ_FIFO = 4'h1;
parameter             ACK_WAIT  = 4'h2;

reg [1:0]             astate  = IDLE;

/*
assign debug[1:0]  = astate;
assign debug[2] = in_fifo_empty;
assign debug[3] = in_fifo_rd;
assign debug[4] = dw_ready;
assign debug[7:5] = rstate[2:0];
assign debug[15:8]  = in_fifo_data;
*/
//assign debug[4] = (in_fifo_data == 8'h08); 
//assign debug[5] = dw_ready;
//assign debug[7:6] = byte_count[1:0];

//Host -> Master DW  assembler
always @ (posedge clk) begin
  dw_ready              <=  0;

  if (rst) begin
    byte_count          <=  4'h0;
    working_dw          <=  32'h0;
    read_dw             <=  32'h0;
    in_fifo_rd          <=  0;
    astate              <=  IDLE;
  end
  else begin
    in_fifo_rd          <=  0;
//    if (!write_busy) begin
      case (astate)
        IDLE: begin
          if (!in_fifo_empty) begin
            astate          <=  READ_FIFO;
          end
        end
        READ_FIFO: begin
          if (reset_assembler) begin
            working_dw        <=  32'h0000;
            byte_count        <=  2'b00;
            dw_ready          <=  0;
            if (!in_fifo_empty) begin
              in_fifo_rd      <=  1;
            end
            else begin
              astate          <=  IDLE;
            end
          end
          else begin
            if (in_fifo_empty) begin
              astate          <=  IDLE;
              in_fifo_rd      <=  0;
              if (byte_count == 2'h3) begin
                //watch out for the condition where I just got done reading a double word
                byte_count    <=  2'h0;
                read_dw       <=  {working_dw[23:0], in_fifo_data};
                dw_ready      <=  1;
                working_dw    <=  32'h0000;
                astate        <=  ACK_WAIT;
              end
            end
            else begin
              in_fifo_rd      <=  1;
              if (in_fifo_rd) begin
                working_dw      <= {working_dw[23:0], in_fifo_data};
                if (byte_count == 2'h3) begin
                  byte_count    <=  2'h0;
                  read_dw       <=  {working_dw[23:0], in_fifo_data};
                  dw_ready      <=  1;
                  working_dw    <=  32'h0000;
                  astate        <=  ACK_WAIT;
                  in_fifo_rd    <=  0;
                end
  
                byte_count      <=  byte_count + 1;
              end
            end
          end
        end
        ACK_WAIT: begin
          if (read_ack) begin
            dw_ready          <=  0;
            astate            <=  IDLE;
            byte_count        <=  0;
          end
        end
        default: begin
          astate <=  IDLE;
        end
      endcase
//    end
  end
end

parameter	IDLE				      =	4'h0;
parameter READ_COMMAND      = 4'h1;
parameter PROCESS_COMMAND   = 4'h2;
parameter READ_ADDRESS      = 4'h3;
parameter READ_DATA         = 4'h4;
parameter	NOTIFY_MASTER		  =	4'h5;

reg	[3:0]	            rstate	=	IDLE;
reg [23:0]            read_count;

//Host to Master input path
always @ (posedge clk) begin
	if (rst) begin
		$display ("FT_HI: in reset");
		in_command		  <=	32'h0000;
		in_address		  <=	32'h0000;
		in_data			    <=	32'h0000;
		in_data_count	  <= 	32'h0000;
    read_count      <=  24'h000;
	
		ih_ready		    <=	0;
    ih_reset        <=  0;
		rstate		      <=	IDLE;
    read_ack        <=  0;

    //debug data
//    debug           <= 8'h00;
	end
	else begin
		//read should only be pulsed
		ih_ready		    <=	0;
    ih_reset        <=  0;
		in_fifo_rst		  <=	0;
    //read_ready      <=  0;
    read_ack        <=  0;

//    debug[1]        <=  (rstate != IDLE);
    //debug[1]        <=  (rstate == READ_COMMAND);
    case (rstate)
      IDLE: begin
        //if there is new data within the incomming FIFO
        reset_assembler     <=  1;
        if (sof && (astate == READ_FIFO)) begin
          if (!in_fifo_empty && (in_fifo_data == 8'hCD)) begin
//            debug[0]        <=  !debug[0];
            reset_assembler <=  0;
            $display("FT_READ: Detected start of transfer with good ID");
            rstate          <=  READ_COMMAND;
          end
          else begin
            //debug[1]        <=  !debug[1];
            $display ("FT_READ: Detected bad ID!");
          end
        end
      end
      READ_COMMAND: begin
        //detected a good ID
        if (dw_ready) begin
          read_ack          <=  1;
          rstate            <=  PROCESS_COMMAND;
          in_command        <=  {12'h000, read_dw[31:28], 12'h000 ,read_dw[27:24]};
          in_data_count     <=  {8'h00, read_dw[23:0]};
          read_count        <=  read_dw[23:0];
        end
      end
      PROCESS_COMMAND: begin
        //Now I have a command in 'in_command' 
        if (in_command[3:0] == PING) begin
          //PING command
          $display("FT_READ: PING Command");
          rstate            <=  NOTIFY_MASTER;
        end
        else if (in_command[3:0] == RESET) begin
          //RESET the state machine
          $display("FT_READ: RESET Command");
          reset_assembler   <=  1;
          ih_reset          <=  1;
          rstate            <=  IDLE;
        end
        else if (in_command[3:0] == READ || in_command[3:0] == WRITE) begin
          //READ or WRITE
          $display("FT_READ: READ/WRITE Command");
          rstate            <=  READ_ADDRESS;
        end
        else begin
          //UNSUPPORTED COMMAND
          $display ("FT_READ: Unsupported command!");
          rstate            <=  IDLE;
        end
      end
      READ_ADDRESS: begin
        //read_ready            <=  1;
        if (dw_ready) begin
          read_ack              <=  1;
          //read_ready          <=  0;
          if (in_command[3:0] == WRITE) begin
            //WRITE command
            if (dw_ready) begin
              in_address      <=  read_dw;
              rstate          <=  READ_DATA;
            end
          end
          else begin
            //READ command
            if (dw_ready) begin
              in_address      <=  read_dw;
              rstate          <=  NOTIFY_MASTER;
            end
          end
        end
      end
      READ_DATA: begin
        //read data from the host
//        debug[2]                <=  1;
        if (dw_ready) begin
          read_ack          <=  1;
//XXX: this is a possible point of error because I could wait here for ever!
//XXX: How can I tell that things are hung? What about a timeout from the master
//XXX: that will reset this state machine
          if (read_count > 0) begin
            read_count      <=  read_count - 1;
          end
          in_data           <=  read_dw;
          rstate            <=  NOTIFY_MASTER;
        end
      end
      NOTIFY_MASTER: begin
        if (master_ready) begin
          //tell the master that we are ready too
          ih_ready          <=  1;
          if (in_command[3:0] == WRITE && read_count > 0) begin
            //write is the only type of command that can send more data
            rstate          <=  READ_DATA; //read_ready      <=  1;
          end
          else begin
//            debug[2]        <=  0;
            rstate          <=  IDLE;
          end
        end
      end
      default: begin
        rstate              <=  IDLE;
      end
    endcase
  end
end




//MASTER -> HOST

//Master -> Host Dissassembler
reg [3:0]   dcount;
reg [31:0]  output_dw;
reg         write_id;
wire        dissassembler_ready;
//assign      dissassembler_ready = (!out_fifo_full && (dcount == 0) && !finish_strobe);
reg         new_output_data;
reg [31:0]  output_data;

reg [7:0]   out_cache;
reg [3:0]   dstate;

wire        dissassembly_valid;
assign      dissassembly_valid = ((dcount > 0) && !out_fifo_full);

assign      dissassembler_ready = ((dstate == IDLE) && !out_fifo_full);

parameter   DWRITE          = 4'h1;
parameter   DFIFO_CHECK     = 4'h2;
parameter   DFIFO_WAIT      = 4'h3;

always @ (posedge clk) begin
  if (rst) begin
    dcount     <=  4'h0;
    out_fifo_wr             <=  0;
    output_data             <=  32'h0000;
    out_cache               <=  8'h00;
    dstate                  <=  IDLE;
  end
  else begin
    out_fifo_wr             <=  0;
    case (dstate)
      IDLE: begin
        if (write_id) begin
          out_fifo_data     <=  8'hDC;
          out_fifo_wr       <=  1;
        end
        else if (new_output_data) begin
          dcount            <=  4'h3;
          output_data       <=  output_dw;
          dstate            <=  DWRITE;
        end
      end
      DWRITE: begin
        if (!out_fifo_full) begin
          out_fifo_data     <=  output_data[31:24];
          out_fifo_wr       <=  1;
          output_data       <=  {output_data[23:0], 8'h00};
          dcount            <=  dcount - 1;
          if (dcount == 0) begin
            out_cache       <=  output_data[31:24];
            dstate          <= DFIFO_CHECK;
          end
        end
      end
      DFIFO_CHECK: begin
        if (out_fifo_full) begin
          dstate            <=  DFIFO_WAIT;
        end
        else begin
          dstate            <=  IDLE;
        end
      end
      DFIFO_WAIT: begin
        if (!out_fifo_full) begin
          out_fifo_wr       <=  1;
          out_fifo_data     <=  out_cache;
          dstate            <=  IDLE;
        end
      end
      default: begin
        dstate  <=  IDLE;
      end
    endcase
  end

/*
    if (finish_strobe) begin
      if (out_fifo_full) begin
        cache_valid         <=  1;
      end
      else begin
        if (cache_valid) begin
          out_fifo_data     <=  out_cache; 
        end
        cache_valid         <=  0;
        finish_strobe       <=  0;
      end
    end
    if (dcount > 0 && !out_fifo_full) begin
      out_fifo_data         <=  output_data[31:24];
      out_fifo_wr           <=  1;

      if (dcount == 1) begin
        out_cache           <=  output_data[31:24];
        finish_strobe       <=  1;
      end
      output_data           <=  {output_data[23:0], 8'h00};
      dcount   <=  dcount - 1;
    end
  end
*/
end



parameter SEND_STATUS         = 4'h1;
parameter SEND_ADDRESS        = 4'h2;
parameter SEND_DATA           = 4'h3;
parameter SEND_MORE_DATA      = 4'h4;

reg	[3:0]	            wstate	=	IDLE;
reg [31:0]            master_status;
reg [31:0]            master_address;
reg [31:0]            master_data;
//reg [31:0]            master_count;

//Master -> Host Path
always @ (posedge clk) begin
  if (rst) begin
    wstate                    <=  IDLE;
    oh_ready                  <=  0;
    write_id                  <=  0;
    new_output_data           <=  0;

    master_status             <=  32'h0000;
    master_address            <=  32'h0000;
    master_data               <=  32'h0000;
//    master_count              <=  32'h0000;
  end
  else begin
    write_id                  <=  0;
    oh_ready                  <=  0;
    new_output_data           <=  0;
//    if (dissassembler_ready && !new_output_data && !read_busy) begin
    if (dissassembler_ready && !new_output_data) begin
      case (wstate)
        IDLE: begin
//XXX: There is possibly a race condition with the read PATH and write path vying for control
//XXX: of the output buffer
          oh_ready            <=  1;
          if (oh_en) begin
            write_id          <=  1;
            oh_ready          <=  0;
            master_status     <=  out_status;
            master_address    <=  out_address;
            master_data       <=  out_data;
//            master_count      <=  out_data_count;
            wstate            <=  SEND_STATUS;
          end
        end
        SEND_STATUS: begin
          if (master_status[3:0] == 4'hF) begin //PING
            //were done!
            $display ("FT_WRITE: Sending PING Response");
            output_dw         <=  {master_status[7:0], 24'h0};
            wstate            <=  IDLE;
          end
          else if (master_status[3:0] == 4'hC) begin //RESET
//XXX: does the master send something on reset?
            //Were done too!
            $display ("FT_WRITE: Sending RESET Response %h", master_status[3:0]);
            output_dw         <=  {master_status[7:0], 24'h0};
            wstate            <=  IDLE;
          end
          else if ((master_status[3:0] == 4'hE) || (master_status[3:0] == 4'hD)) begin
            $display ("FT_WRITE: Sending READ/WRIE Response");
            output_dw         <=  {master_status[7:0], out_data_count[23:0]}; 
            wstate            <=  SEND_ADDRESS;
          end
          else begin
            $display ("FT_WRITE: Sending ILLEAGLE COMMAND TO HOST %h", master_status[3:0] & PING);
//XXX: Should I send illeagle commands to the host?
            output_dw         <=  {master_status[7:0], 24'h0};
            wstate            <=  IDLE;
          end
          new_output_data     <=  1;
        end
        SEND_ADDRESS: begin
          output_dw           <=  master_address;
          new_output_data     <=  1;
          wstate              <=  SEND_DATA;
        end
        SEND_DATA: begin
          output_dw           <=  master_data;  
          new_output_data     <=  1;
          if ((master_status[3:0] == 4'hD) && (out_data_count > 0)) begin
            //the command is writing and the data count > 0
            $display ("\t\tFT_WRITE: Send more data");
            wstate            <=  SEND_MORE_DATA;
          end
          else begin
            wstate            <=  IDLE;
          end
        end
        SEND_MORE_DATA: begin
          oh_ready          <=  1;
          if (oh_en) begin
            output_dw       <=  out_data;
            oh_ready        <=  0;
            new_output_data <=  1;
            if (out_data_count == 0) begin
              wstate        <=  IDLE;
            end
          end
        end
        default: begin
          $display ("FT_WRITE: Unknown state");
          wstate              <=  IDLE;
        end
      endcase
    end
  end
end
endmodule
