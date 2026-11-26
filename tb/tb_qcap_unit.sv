`timescale 1ns/1ps
module tb_qcap_unit;
  reg clk=0,rst=0,start=0,clear=0;
  reg [31:0] budget=0;
  reg [7:0] price=0;
  wire busy,done;
  wire [5:0] result;
  integer tests=0,seed=42;
  always #20 clk=~clk;
  espino_qcap dut(clk,rst,start,clear,budget,price,busy,done,result);
  task check(input [31:0] cash,input [7:0] p);
    reg [31:0] expected;
    integer waited;
    begin
      expected=p==0 ? 0 : cash/p;
      if(expected>63) expected=63;
      @(negedge clk); budget=cash;price=p;start=1;
      @(negedge clk);start=0; waited=0;
      while(!done && waited<9) begin @(negedge clk);waited++;end
      if(!done || busy || result!==expected[5:0]) $fatal(1,"QCAP %0d/%0d: %0d esperado %0d",cash,p,result,expected);
      repeat(3) begin @(negedge clk); if(!done || result!==expected[5:0]) $fatal(1,"resultado no se conserva hasta clear");end
      clear=1;@(negedge clk);clear=0;
      if(done || busy) $fatal(1,"clear no libera unidad");
      tests++;
    end
  endtask
  initial begin
    repeat(2) @(negedge clk);rst=1;
    check(0,0);check(32'hffffffff,0);
    for(integer p=1;p<=255;p++) begin
      check(0,p);check(p-1,p);check(p,p);check(p+1,p);
      check(63*p-1,p);check(63*p,p);check(63*p+1,p);
      check(16383,p);check(16384,p);check(32'hffffffff,p);
    end
    for(integer i=0;i<4096;i++) begin
      if(i%2==0) check($urandom(seed)&32'h3fff,$urandom(seed));
      else check($urandom(seed),$urandom(seed));
    end
    // Reset interrumpe una operacion en vuelo y no deja una respuesta vieja.
    @(negedge clk);budget=1000;price=17;start=1;
    @(negedge clk);start=0;rst=0;
    @(negedge clk);if(done || busy) $fatal(1,"reset no limpia unidad");rst=1;
    check(1000,17);
    $display("PASS QCAP: %0d casos, fronteras, aleatorios, retencion y reset",tests);$finish;
  end
endmodule
