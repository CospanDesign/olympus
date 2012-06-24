//ft_host_interface.v

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
input				rst;
input				clk;

input				master_ready;
output reg			ih_ready;
output reg      ih_reset;

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
output  reg [7:0]   debug;

//fifo interface
wire				fifo_rst;
reg					in_fifo_rst;
assign	fifo_rst	=	rst | in_fifo_rst;

reg					in_fifo_rd;
wire				in_fifo_empty;
wire	[7:0]		in_fifo_data;

reg					out_fifo_wr;
wire				out_fifo_full;	
reg		[7:0]		out_fifo_data;

reg		[7:0]		next_read_state;
reg		[7:0]		process_state;
reg		[7:0]		next_write_state;

reg		[31:0]		temp_data;
wire          sof;

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
	.ftdi_suspend_n(ftdi_suspend_n)

);
parameter	IDLE				    =	8'h0;


parameter	READ_WAIT_1			=	8'h1;
parameter	READ_WAIT_2			=	8'h2;			

parameter	WRITE_ID			  =	8'h1;

parameter	READ_DW_WAIT_1	=	8'h11;
parameter	READ_DW_WAIT_2	=	8'h12;
parameter	READ_DW				  =	8'h10;
parameter	PROCESS_ID			=	8'h13;
parameter	PROCESS_CMD			=	8'h14;
parameter	PROCESS_ADDRESS	=	8'h15;
parameter	PROCESS_DATA		=	8'h16;

parameter	NOTIFY_MASTER		=	8'h17;

parameter	READ_D4				  =	8'hA;
parameter	RESET_DELAY			=	8'hB;
parameter	BAD_ID				  =	8'hC;

parameter	WAIT_FIFO			  =	8'hD;

parameter	WRITE_COMMAND		=	8'h3;
parameter	WRITE_ADDR			=	8'h4;
parameter	WRITE_DATA			=	8'h5;
parameter	WAIT_FOR_MASTER	=	8'h6;



reg [31:0]	          read_count;
reg [1:0]	            read_byte_count;
reg			              prev_rd;
reg	[31:0]	          local_data_count;


reg	[7:0]	            read_state	=	IDLE;
reg	[7:0]	            write_state	=	IDLE;

//input handler
always @ (posedge clk) begin
	if (rst) begin
		$display ("FT_HI: in reset");
		in_command		  <=	32'h0;
		in_address		  <=	32'h0;
		in_data			    <=	32'h0;
		in_data_count	  <= 	32'h0;
	
		ih_ready		    <=	0;
    ih_reset        <=  0;
		read_count		  <=	0;
		read_state		  <=	IDLE;
		in_fifo_rd		  <= 	0;
		in_fifo_rst		  <=	1;

		read_byte_count	<=	0;
		next_read_state	<= 	IDLE;
		prev_rd			    <=	0;

		process_state	  <= IDLE;
		temp_data		    <= 0;

    //debug data
    debug           <= 8'h00;
	end
	else begin
		//read should only be pulsed
		prev_rd			    <=	in_fifo_rd;
		in_fifo_rd		  <=	0;
		ih_ready		    <=	0;
    ih_reset        <=  0;
		in_fifo_rst		  <=	0;

		case (read_state)
			IDLE: begin
				if (~in_fifo_empty) begin
					$display ("FT_HI: Found data in the FIFO!");
					read_state	    <= READ_WAIT_2; 
					read_byte_count	<= 3;

					in_fifo_rd	    <= 1;
					process_state	  <= PROCESS_ID; 
//					read_state	<= READ_DW;
					read_state	    <= READ_DW_WAIT_2;
					temp_data	      <= 0;
				end
			end

//			READ_DW_WAIT_1: begin
				//this state is entered when
				//the in_fifo_empty is lowered
//				read_state	<= READ_DW_WAIT_2;
//			end
			READ_DW_WAIT_2: begin
				//this state is entered after WAIT_1;
				if (~in_fifo_empty) begin
					read_state	    <= READ_DW;
					in_fifo_rd	    <= 1;
				end
			end

			READ_DW: begin
				$display ("Reading: %h", in_fifo_data);
        if (sof) begin 
          //start of a packet of data
          debug[0] <= ~debug[0];
        end

				temp_data	<= {temp_data[23:0], in_fifo_data};	
				if (read_byte_count == 3) begin
					//go to a process state
					read_state	<= process_state;
					$display("Done reading... Process!");
				end
				else begin
					if (~in_fifo_empty) begin
						in_fifo_rd	<= 1;
					end
					else begin
						read_state	<= READ_DW_WAIT_2;	
					end
				end
				read_byte_count <= read_byte_count + 1;
			end

			PROCESS_ID: begin
				if (temp_data[7:0] == 8'hCD) begin
					$display("ID good get the command");
					process_state	  <= PROCESS_CMD;
					read_state	    <= READ_DW_WAIT_2;
				end
				else begin
					read_state	    <= BAD_ID;
				end
				read_byte_count   <= 0;
			end
			PROCESS_CMD: begin
				in_command[19:16] <= temp_data[31:28];
				in_command[3:0]	  <=	temp_data[27:24];
				in_data_count	    <= {8'h0, temp_data[23:0]};
				local_data_count	<= temp_data[23:0];
				if (temp_data[23:0] > 0) begin
//XXX: if we are reading -1 the count... this is a bit hacky :( need to change the write protocol
					if (temp_data[27:24] == 1) begin
						in_data_count	    <= {8'h0, temp_data[23:0]} - 1;
						local_data_count	<= temp_data[23:0] - 1;
					end
					else begin
						in_data_count	    <= {8'h0, temp_data[23:0]};
						local_data_count	<= temp_data[23:0];
					end
				end
				if (temp_data[27:24] == 0) begin
			//		$display ("PING");
					//we're done!
					read_state	<= NOTIFY_MASTER;
				end
				else if (temp_data[27:24] == 1) begin
					$display ("WRITE");
					//get the address
					process_state	    <= PROCESS_ADDRESS;
					read_state	      <= READ_DW_WAIT_2;
				end
				else if (temp_data[27:24] == 2) begin
					$display ("READ");
					//get the address
					process_state	    <= PROCESS_ADDRESS;
					read_state	      <= READ_DW_WAIT_2;
				end
        else if (temp_data[27:24] == 3) begin
          $display ("RESET");
          ih_reset          <=  1;
          in_fifo_rst       <=  1;
          in_data_count     <=  32'h0000;
          local_data_count  <=  24'h000;
          read_state        <=  IDLE;
        end
				else begin
					$display ("ILLEGAL COMMAND: %h", temp_data[27:23]);
					read_state	      <= READ_D4;
				end
				read_byte_count     <= 0;
			end
			PROCESS_ADDRESS: begin
				in_address	        <= temp_data;
				//we only have two choices cause PROCESS_CMD
				//already weeded out PING and illegals
				if (in_command[3:0]	==	1) begin
					//write
					process_state	    <= PROCESS_DATA;
					read_state	      <= READ_DW_WAIT_2;
				end
				else begin
					//read
					read_state	      <= NOTIFY_MASTER;
				end
				read_byte_count     <= 0;
			end
			PROCESS_DATA: begin
				in_data	            <= temp_data;
				read_state	        <= NOTIFY_MASTER;
				read_byte_count     <= 0;
			end
			NOTIFY_MASTER: begin
				$display("NOTIFY MASTER");
				if (master_ready) begin
					ih_ready	        <= 1;
					if (in_command[3:0] == 0) begin
						
						//ping
						read_state	    <= READ_D4;
					end
					else if (in_command[3:0] == 1) begin
						if (local_data_count == 0) begin
							//were done!
							read_state	  <= READ_D4;
						end
						else begin
							local_data_count <= local_data_count - 1;
							read_state	  <= READ_DW_WAIT_2;
							process_state	<= PROCESS_DATA;
						end
					end
					else if (in_command[3:0] == 2) begin
						//read
						read_state	    <= READ_D4;
					end
				end
			end
			READ_D4: begin
				in_fifo_rst	        <= 1;
				if (ftdi_rde_n) begin
					read_state		    <=	RESET_DELAY;
				end	
			end
			RESET_DELAY: begin
				in_fifo_rst	        <= 1;
				read_state			    <= IDLE;
			end
			BAD_ID: begin
				in_fifo_rst	        <= 1;
				//need to wait unilt the rde_n goes low
				$display ("FT_HI: BAD ID, I should send a response to the host that something went wrong here"); 
				read_state	        <=	READ_D4;
			end
			default: begin
				$display ("FT_HI: How did we get here!?");
				read_state	        <= IDLE;
			end

		endcase
		
	end
end


//output handler
reg	[31:0]	write_count;

reg [1:0]	write_byte_count;

reg	[31:0]	local_status;
reg [31:0]	local_address;
reg	[31:0]	local_data;


always @ (posedge clk) begin
	if (rst) begin
		oh_ready			<=	0;
		write_count			<=	0;
		write_byte_count	<=	0;
		out_fifo_wr			<=	0;
		next_write_state	<=	0;

		local_status		<=	0;
		local_address		<=	0;
		local_data			<=	0;

	end
	else begin
		out_fifo_wr			<= 	0;
		case (write_state)
			IDLE: begin
				oh_ready	<= 1;
				if (oh_en) begin
					oh_ready	<= 0;

					$display ("FT_OH: Send the identification byte");
					out_fifo_data	<= 8'hDC;
					write_byte_count <= 0;
					
					$display ("FT_OH: Master sending data");
					$display ("FT_OH: out_status: %h", out_status[7:0]);
					//tell the master to kick back for a sec
					write_count	<= out_data_count;
	//				out_fifo_data	<= {out_status[7:0], out_data_count[23:0]};
					if (out_status[3:0] == 4'hF) begin
						local_status	<= {out_status[7:0], 24'h0};
					end
					else begin
						local_status		<= {out_status[7:0], out_data_count[23:0]} + 1;
					end

					local_address		<= out_address;
					local_data			<= out_data;

					write_state	<= WRITE_ID;

				end
			end
			WRITE_ID: begin
				if (~out_fifo_full)	begin
					out_fifo_wr	<= 1;
					write_state	<= WRITE_COMMAND;
					write_byte_count	<= 0;
				end
			end
			WRITE_COMMAND: begin
				if (~out_fifo_full) begin
					out_fifo_data	<= local_status[31:24];
					local_status	<= {local_status[23:0], 8'h0};
					out_fifo_wr 	<= 1;
					if (write_byte_count == 3) begin
						if (out_status[3:0] == 4'hF) begin
							write_state <= IDLE;
						end
						else begin
							write_state <= WRITE_ADDR;
						end
					end
					//the write byte count should roll over to 0
					write_byte_count <= write_byte_count + 1;
				end
			end
			WRITE_ADDR: begin
				if (~out_fifo_full) begin
					out_fifo_data	<= local_address[31:24];
					local_address	<= {local_address[23:0], 8'h0};
					out_fifo_wr		<= 1;
					if (write_byte_count == 3) begin
						if (out_status[3:0] == 4'hD) begin
							//write
							write_state		<= WRITE_DATA;
						end
						else begin
							//read
							write_state	<= IDLE;
						end
					end
					write_byte_count <=	write_byte_count + 1;
				end
			end
			WRITE_DATA: begin
				if (~out_fifo_full) begin
					out_fifo_wr		<= 1;
					out_fifo_data	<= local_data[31:24];
					local_data	<= {local_data[23:0], 8'h0};
					if (write_byte_count == 3) begin
						oh_ready <= 1;
						if (write_count > 0) begin
							write_count <= write_count - 1;
							write_state <= WAIT_FOR_MASTER;
						end
						else begin
							write_state	<= IDLE;
						end
					end
					write_byte_count <= write_byte_count + 1;
				end
			end
			WAIT_FOR_MASTER: begin
				oh_ready <= 1;
				if (oh_en) begin
					//another 32 bit word to read
					write_state	<= WRITE_DATA;
					write_byte_count <= 0;
					oh_ready <= 0;
					local_data	<= out_data;
				end
				//probably need a timeout
			end
			default: begin
				write_state	<= IDLE;
			end
		endcase
	end
end


endmodule
