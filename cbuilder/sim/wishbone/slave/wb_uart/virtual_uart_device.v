`include "project_defines.v"
`define BAUD_RATE 9600
`define PRESCALER 8 

`define CLOCK_DIVIDE `CLOCK_RATE / (`BAUD_RATE * `PRESCALER)

`define HALF_PERIOD (`PRESCALER / 2 * `CLOCK_DIVIDE)
`define FULL_PERIOD (`PRESCALER * `CLOCK_DIVIDE)


reg [3:0]   bit_index = 0;

task  read_from_uart;
  input in_bit;
  output reg  [7:0] in_byte;

  begin

    $display ("Full Period: %d", `FULL_PERIOD);
    $display ("Half Period: %d", `FULL_PERIOD);
    #`FULL_PERIOD;
    #`FULL_PERIOD;
    in_byte[0]  <=  in_bit;
    #`FULL_PERIOD;
    in_byte[1]  <=  in_bit;
    #`FULL_PERIOD
    in_byte[2]  <=  in_bit;
    #`FULL_PERIOD;
    in_byte[3]  <=  in_bit;
    #`FULL_PERIOD;
    in_byte[4]  <=  in_bit;
    #`FULL_PERIOD;
    in_byte[5]  <=  in_bit;
    #`FULL_PERIOD;
    in_byte[6]  <=  in_bit;
    #`FULL_PERIOD;
    in_byte[7]  <=  in_bit;
    #`FULL_PERIOD;
    end
endtask

//input a read and send out the data one byte at a time
task write_to_uart;
  input [7:0] out_byte;
  output reg  out_bit;

  begin

    $display ("Full Period: %d", `FULL_PERIOD);
    $display ("Half Period: %d", `HALF_PERIOD);
    $display ("Out byte: %h", out_byte);
    out_bit   <=  1;
    #`FULL_PERIOD
    $display ("Start bit goes low");

    bit_index <=  0;

    //set the RX line low
    out_bit   <=  0;
    #`FULL_PERIOD
    #`HALF_PERIOD


    //send seventh bit
    $display ("7th...");
    out_bit             <=  out_byte[bit_index];
    #`FULL_PERIOD
    $display ("out_bit: %h", out_bit);
    bit_index           <=  bit_index + 1;
    #`HALF_PERIOD

    //send sixth bit
    $display ("6th...");
    out_bit             <=  out_byte[bit_index];
    #`FULL_PERIOD
    $display ("out_bit: %h", out_bit);
    bit_index           <=  bit_index + 1;
    #`HALF_PERIOD

    //send 5th bit
    $display ("5th...");
    out_bit             <=  out_byte[bit_index];
    #`FULL_PERIOD
    $display ("out_bit: %h", out_bit);
    bit_index           <=  bit_index + 1;
    #`HALF_PERIOD

    //send 4th bit
    $display ("4th...");
    out_bit             <=  out_byte[bit_index];
    #`FULL_PERIOD
    $display ("out_bit: %h", out_bit);
    bit_index           <=  bit_index + 1;
    #`HALF_PERIOD

    //send 3rd bit
    $display ("3rd...");
    out_bit             <=  out_byte[bit_index];
    #`FULL_PERIOD
    $display ("out_bit: %h", out_bit);
    bit_index           <=  bit_index + 1;
    #`HALF_PERIOD

    //send 2nd bit
    $display ("2nd...");
    out_bit             <=  out_byte[bit_index];
    #`FULL_PERIOD
    $display ("out_bit: %h", out_bit);
    bit_index           <=  bit_index + 1;
    #`HALF_PERIOD

    //send 1st bit
    $display ("1st...");
    out_bit             <=  out_byte[bit_index];
    #`FULL_PERIOD
    $display ("out_bit: %h", out_bit);
    bit_index           <=  bit_index + 1;
    #`HALF_PERIOD

    //send 0th bit
    $display ("0th...");
    out_bit             <=  out_byte[bit_index];
    #`FULL_PERIOD
    $display ("out_bit: %h", out_bit);
    bit_index           <=  bit_index + 1;
    #`HALF_PERIOD

    //wait 1 stop bit
    $display ("stop bit");
    out_bit                  <= 1;
    #`FULL_PERIOD
    #`HALF_PERIOD
    out_bit                  <=  1;

  
    wait(received == 0);
  end
//Virtual UART
endtask
