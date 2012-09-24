`ifndef __LA_DEFINES__
`define __LA_DEFINES__

`define DEFAULT_CAP_DAT_WIDTH 32
`define DEFAULT_CAP_MEM_SIZE  10
`define DEFAULT_TRIG          32'h00000000

//UART Interface
`define HEX_0                 8'h30
//W = Write (start)
`define START_ID              8'h57
//R = Read (Response)
`define RESPONSE_ID           8'h52

`define RESPONSE_SUCCESS      8'h53
`define RESPONSE_FAIL         8'h5A
`define RESPONSE_ENABLE       8'h65
`define RESPONSE_DISABLE      8'h66

`define LA_PING               (0 + `HEX_0)
//ID:                   'W'
//Command:              '0'

//Response ID:          'R'
//Response Status:      'S' = Success, 'X' = Fail

`define LA_WRITE_SETTINGS     (1 + `HEX_0)
//write setting structure
//ID:                   'W'
//Command:              '1'
//Trigger:              'W' 'W' 'W' 'W' 'W' 'W' 'W' 'W'
//Trigger Mask:         'X' 'X' 'X' 'X' 'X' 'X' 'X' 'X'
//Trigger After:        'Y' 'Y' 'Y' 'Y' 'Y' 'Y' 'Y' 'Y'
//Repeat Count:         'Z' 'Z' 'Z' 'Z' 'Z' 'Z' 'Z' 'Z'

//Response ID:          'R'
//Response Status:      'S' = Success, 'X' = Fail

`define LA_SET_ENABLE         (2 + `HEX_0)
//set enable structure
//ID:                   'W'
//Command:              '2'
//Enabled:              '0' = Disable, '1' = Enable

//Response ID:          'R'
//Response Status:      'S' = Success, 'X' = Fail


`define LA_GET_ENABLE         (3 + `HEX_0)
//get enable structure
//ID:                   'W'
//Command:              '3'

//Response ID:          'R'
//Response Status:      '0' = Disabled '1' = Enabled 

`endif

