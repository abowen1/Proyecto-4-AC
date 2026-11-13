`timescale 1ns/1ps
module tb_shifter_unit;
  reg [31:0] a,b,instruction;
  reg [3:0] op;
  wire [31:0] result;
  wire cmp,illegal;
  integer tests=0,seed=23;
  espino_alu alu(op,a,b,result,cmp);
  espino_decoder dec(.instr_i(instruction),.illegal_insn_o(illegal));
  task check(input [31:0] value,input integer shift,input bit left);
    reg [31:0] expected;
    begin
      a=value;b=shift;op=left?5:6;expected=left ? value<<shift : value>>shift;
      instruction=(shift<<20)|(left?32'h00001013:32'h00005013);#1;
      if(illegal || result!==expected) $fatal(1,"shift incorrecto a=%h n=%0d izq=%0d",value,shift,left);
      tests++;
    end
  endtask
  initial begin
    for(integer i=0;i<4096;i++) begin
      check($urandom(seed),1,1);check($urandom(seed),5,1);
      check($urandom(seed),6,1);check($urandom(seed),1,0);
    end
    check(32'h80000000,1,0);check(32'hffffffff,6,1);check(32'hffffffff,1,0);
    for(integer n=0;n<32;n++) begin
      instruction=(n<<20)|32'h1013;#1;
      if(illegal !== (n!=1 && n!=5 && n!=6)) $fatal(1,"aceptacion incorrecta SLLI %0d",n);
      instruction=(n<<20)|32'h5013;#1;
      if(illegal !== (n!=1)) $fatal(1,"aceptacion incorrecta SRLI %0d",n);
    end
    instruction=32'h40005013;#1;if(!illegal) $fatal(1,"SRAI no rechazado");
    instruction=32'h00001033;#1;if(!illegal) $fatal(1,"SLL registro no rechazado");
    instruction=32'h00005033;#1;if(!illegal) $fatal(1,"SRL registro no rechazado");
    $display("PASS shifter: %0d operaciones RV32 exactas, decoder y restricciones",tests);$finish;
  end
endmodule
