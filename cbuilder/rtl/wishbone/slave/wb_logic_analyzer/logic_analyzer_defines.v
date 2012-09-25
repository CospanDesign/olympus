`ifndef __LA_DEFINES__
`define __LA_DEFINES__

`define CAP_DAT_WIDTH 32
`define CAP_MEM_SIZE  12
`define TRIG          32'h00000000

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
`define CARRIAGE_RETURN       8'h0D
`define LINE_FEED             8'h0A

`define LA_PING               (0 + `HEX_0)
//ID:                   'W'
//Command:              '0'
//CR:                   '\n'

//Response ID:          'R'
//Response Status:      'S' = Success, 'X' = Fail
//LF:                   '\r'
//CR:                   '\n'

`define LA_WRITE_SETTINGS     (1 + `HEX_0)
//write setting structure
//ID:                   'W'
//Command:              '1'
//Trigger:              'W' 'W' 'W' 'W' 'W' 'W' 'W' 'W'
//Trigger Mask:         'X' 'X' 'X' 'X' 'X' 'X' 'X' 'X'
//Trigger After:        'Y' 'Y' 'Y' 'Y' 'Y' 'Y' 'Y' 'Y'
//Repeat Count:         'Z' 'Z' 'Z' 'Z' 'Z' 'Z' 'Z' 'Z'
//CR:                   '\n'

//Response ID:          'R'
//Response Status:      'S' = Success, 'X' = Fail
//LF:                   '\r'
//CR:                   '\n'

`define LA_SET_ENABLE         (2 + `HEX_0)
//set enable structure
//ID:                   'W'
//Command:              '2'
//Enabled:              '0' = Disable, '1' = Enable
//CR:                   '\n'

//Response ID:          'R'
//Response Status:      'S' = Success, 'X' = Fail
//LF:                   '\r'
//CR:                   '\n'


`define LA_GET_ENABLE         (3 + `HEX_0)
//get enable structure
//ID:                   'W'
//Command:              '3'
//CR:                   '\n'

//Response ID:          'R'
//Response Status:      '0' = Disabled '1' = Enabled 
//LF:                   '\r'
//CR:                   '\n'

`define LA_GET_SIZE           (4 + `HEX_0)
//get the size of a read * 4 * bytes
//ID:                   'W'
//Command:              '4'
//CR:                   '\n'

//Response ID:          'R'
//Response Status       'V' 'V' 'V' 'V' 'V' 'V' 'V' 'V'
//LF:                   '\r'
//CR:                   '\n'

`endif

