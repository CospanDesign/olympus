//mg_defines.v

// defines for the miracle grow project

`ifndef __MG_DEFINES__
`define __MG_DEFINES__

`define COMMAND_PING 		32'h00000000
`define COMMAND_WRITE 		32'h00000001
`define COMMAND_READ		32'h00000002
`define COMMAND_WSTREAM_C 	32'h00000003
`define COMMAND_WSTREAM		32'h00000004
`define COMMAND_RSTREAM_C	32'h00000005
`define COMMAND_RSTREAM		32'h00000006
`define COMMAND_RW_FLAGS	32'h00000007
`define COMMAND_INTERRUPT	32'h00000008

`endif //__MG_DEFINES__
