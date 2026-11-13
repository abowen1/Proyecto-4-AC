`timescale 1ns/1ps
module tb_hw_instructions;
  parameter PROGRAM="";
  reg clk=0;
  always #20 clk=~clk;
  reg [31:0] registers [0:15];
  pochoco_soc #(.MemFile(PROGRAM)) dut(.i_Clk(clk),.i_Switch(4'b0),.i_SPI_SCLK(1'b0),.i_SPI_MOSI(1'b0),.i_SPI_CS_n(1'b1));
  wire commit=dut.u_core.instr_valid_id && !dut.u_core.stall;
  task expect_register(input integer r,input [31:0] expected);
    if(registers[r]!==expected) $fatal(1,"x%0d=%h esperado %h",r,registers[r],expected);
  endtask
  always @(posedge clk) if(dut.rst_ni) begin
    if(commit && dut.u_core.illegal_insn) $fatal(1,"instruccion ilegal");
    if(commit && dut.u_core.rf_we && dut.u_core.rf_waddr!=0) registers[dut.u_core.rf_waddr]=dut.u_core.rf_wdata;
    if(dut.u_spi.wr && dut.u_spi.off==2) begin
      if(dut.data_wdata!==7) $fatal(1,"sentinela no valida");
`ifdef TEST_SHIFTER
      expect_register(3,32'h40000000);expect_register(4,0);
      expect_register(5,8160);expect_register(6,16320);
      expect_register(8,32'h7fffffff);expect_register(9,32'hffffffe0);
      expect_register(10,32'hffffffc0);expect_register(11,32'h80000000);
      expect_register(12,32'h40000000);expect_register(13,1);
      $display("PASS CPU shifter: resultados RV32, overflow y dependencias");
`else
      expect_register(3,10);expect_register(4,0);expect_register(5,63);
      expect_register(6,0);expect_register(8,63);expect_register(10,6);
      expect_register(12,1);expect_register(13,1);expect_register(14,7);
      $display("PASS CPU QCAP: dependencias, instrucciones consecutivas, rd=rs1, x0 y 32 bits");
`endif
      $finish;
    end
  end
  initial begin #1000000; $fatal(1,"timeout CPU");end
endmodule
