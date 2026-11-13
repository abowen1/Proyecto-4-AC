`timescale 1ns/1ps
module tb_trace_uart;
  parameter PROGRAM="";
  reg clk=0,rst=0,valid=0;wire tx;
  always #20 clk=~clk;
`ifdef TEST_TRACE_SOC
  pochoco_soc #(.MemFile(PROGRAM)) dut(.i_Clk(clk),.i_Switch(4'b0),.i_SPI_SCLK(1'b0),.i_SPI_MOSI(1'b0),.i_SPI_CS_n(1'b1),.o_UART_TX(tx));
`else
  ac4_trace_uart dut(clk,rst,valid,32'h800000b7,tx);
`endif
  reg [7:0] value;
  task receive;
    begin
      @(negedge tx);#13020;
      for(integer i=0;i<8;i++) begin value[i]=tx;#8680;end
      if(tx!==1) $fatal(1,"UART stop incorrecto");
    end
  endtask
  initial begin
    repeat(2) @(negedge clk);rst=1;
    @(negedge clk);valid=1;
    for(integer n=0;n<80;n++) begin
      receive();
      case(n%8)
        0:if(value!==8'h55)$fatal(1,"header 55 %h",value);
        1:if(value!==8'haa)$fatal(1,"header aa %h",value);
        2:if(value!==8'h12)$fatal(1,"header 12 %h",value);
        3:if(value!==8'h34)$fatal(1,"header 34 %h",value);
        4:if(value!==8'hb7)$fatal(1,"dato b7 %h",value);
        5,6:if(value!==0)$fatal(1,"dato cero %h",value);
        7:if(value!==8'h80)$fatal(1,"dato 80 %h",value);
      endcase
    end
    $display("PASS trace UART: 10 paquetes completos de 8 bytes");$finish;
  end
endmodule
