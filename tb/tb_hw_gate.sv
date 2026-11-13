`timescale 1ns/1ps
module tb_hw_gate;
  reg clk=0;
  wire [3:0] led;
  wire [6:0] seg1,seg2;
  always #20 clk=~clk;
  pochoco_soc dut(.i_Clk(clk),.i_Switch(4'b0),.o_LED(led),.i_SPI_SCLK(1'b0),.i_SPI_MOSI(1'b0),.i_SPI_CS_n(1'b1),
    .o_Segment1_A(seg1[0]),.o_Segment1_B(seg1[1]),.o_Segment1_C(seg1[2]),.o_Segment1_D(seg1[3]),.o_Segment1_E(seg1[4]),.o_Segment1_F(seg1[5]),.o_Segment1_G(seg1[6]),
    .o_Segment2_A(seg2[0]),.o_Segment2_B(seg2[1]),.o_Segment2_C(seg2[2]),.o_Segment2_D(seg2[3]),.o_Segment2_E(seg2[4]),.o_Segment2_F(seg2[5]),.o_Segment2_G(seg2[6]));
  initial begin
    wait(led!=0);#4000;
    if(led!==15) $fatal(1,"Gate diagnostic: LED=%h seg1=%h seg2=%h",led,seg1,seg2);
    $display("PASS gate diagnostic: LED=%h seg1=%h seg2=%h",led,seg1,seg2);$finish;
  end
  initial begin #1000000;$fatal(1,"timeout gate diagnostic");end
endmodule
