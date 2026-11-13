// Temporary debug UART: magic 55 aa 12 34 + snapshot little endian, repeated.
module ac4_trace_uart(input wire clk,rst,valid,input wire [31:0] data,output wire tx);
  reg locked, captured;
  reg [31:0] word;
  reg [7:0] divider;
  reg [9:0] frame;
  reg [3:0] remaining;
  reg [2:0] byte_index;
  reg [7:0] next_byte;
  assign tx=frame[0];
  always @* begin
    case(byte_index)
      0:next_byte=8'haa;
      1:next_byte=8'h12;
      2:next_byte=8'h34;
      7:next_byte=8'h55;
      default:next_byte=word[7:0];
    endcase
  end
  always @(posedge clk or negedge rst) begin
    if(!rst) begin locked<=0;captured<=0;word<=0;divider<=0;frame<=10'h3ff;remaining<=10;byte_index<=0;end
    else if(valid && !captured) begin
      captured<=1;locked<=1;word<=data;divider<=0;
      frame<={1'b1,8'h55,1'b0};remaining<=10;byte_index<=0;
    end else if(!locked) begin
      if(valid || divider==255) begin
        locked<=1;word<=valid?data:32'hdeadbeef;divider<=0;
        frame<={1'b1,8'h55,1'b0};remaining<=10;byte_index<=0;
      end else divider<=divider+1;
    end else if(divider==216) begin
      divider<=0;
      if(remaining==1) begin
        remaining<=10;frame<={1'b1,next_byte,1'b0};byte_index<=byte_index+1;
        if(byte_index>=3 && byte_index<=6) word<={word[7:0],word[31:8]};
      end else begin frame<={1'b1,frame[9:1]};remaining<=remaining-1;end
    end else divider<=divider+1;
  end
endmodule
