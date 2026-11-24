// M105-225: CPU y SPI reales, referencia Python por tick y plazo de respuesta.
`timescale 1ns/1ps
module tb_m105_225_profile;
  parameter PROGRAM = "sw/trade_m105_225.hex";
  reg clk=0, sclk=0, mosi=0, cs_n=1;
  wire miso;
  always #20 clk=~clk;
  pochoco_soc #(.MemFile(PROGRAM)) dut (
    .i_Clk(clk), .i_Switch(4'b0), .o_LED(),
    .i_SPI_SCLK(sclk), .i_SPI_MOSI(mosi), .i_SPI_CS_n(cs_n), .o_SPI_MISO(miso));
  reg [191:0] reference [0:19999]; // estado, presupuesto restante, caja, acciones, orden siguiente, precio
  string reference_path, output_path;
  integer ticks, period=100000, fast=0, tick=-1, cycle=0, start_cycle=0;
  integer arrivals=0, responses=0, reads=0, max_cycles=0, budget, fd;
  reg [31:0] cash=0, shares=0, state=0, remaining=0;
  reg pending=0;
  reg [7:0] received, previous=0;
  integer ic=0, last_pc=0, pfd;
  integer pc_cycles[0:511], pc_ic[0:511];
  wire commit = dut.u_core.instr_valid_id && !dut.u_core.stall;
  always @(posedge clk) begin
    cycle=cycle+1;
    if(dut.rst_ni) begin
      if(commit && dut.u_core.illegal_insn !== 1'b0) $fatal(1,"instruccion ilegal");
      if(commit && dut.u_core.rf_we) begin
        case(dut.u_core.rf_waddr)
          3: cash=dut.u_core.rf_wdata;
          4: shares=dut.u_core.rf_wdata;
          6: state=dut.u_core.rf_wdata;
          7: remaining=dut.u_core.rf_wdata;
        endcase
      end
      if(dut.u_spi.byte_done) begin
        if(pending || dut.u_spi.new_price_q) $fatal(1,"precio perdido tick %0d",tick);
        arrivals=arrivals+1;pending=1;start_cycle=cycle;ic=0;last_pc=0;
      end
      if(pending) begin
        if(dut.u_core.instr_valid_id)last_pc=dut.u_core.pc_id/4;
        if(last_pc<0 || last_pc>511)$fatal(1,"PC fuera de RAM");
        if(!dut.u_spi.byte_done)pc_cycles[last_pc]=pc_cycles[last_pc]+1;
        if(commit)begin ic=ic+1;pc_ic[last_pc]=pc_ic[last_pc]+1;end
      end
      if(dut.u_spi.price_read) reads=reads+1;
      if(dut.u_spi.wr && dut.u_spi.off==2 && tick>=0) begin
        if(!pending) $fatal(1,"respuesta duplicada");
        if(dut.data_wdata !== reference[tick][63:32]) $fatal(1,"orden tick %0d: %h != %h",tick,dut.data_wdata,reference[tick][63:32]);
        if(cash !== reference[tick][127:96] || shares !== reference[tick][95:64])
          $fatal(1,"contabilidad tick %0d caja %0d/%0d inventario %0d/%0d",tick,cash,reference[tick][127:96],shares,reference[tick][95:64]);
        if(state !== reference[tick][191:160] || remaining !== reference[tick][159:128])
          $fatal(1,"politica tick %0d estado %0d/%0d presupuesto %0d/%0d",tick,state,reference[tick][191:160],remaining,reference[tick][159:128]);
        if(cycle-start_cycle >= budget) $fatal(1,"deadline tick %0d: %0d >= %0d",tick,cycle-start_cycle,budget);
        if(cycle-start_cycle>max_cycles)max_cycles=cycle-start_cycle;
        $fdisplay(fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",tick,reference[tick][31:0],dut.data_wdata,cash,shares,state,remaining,cycle-start_cycle,ic);
        pending=0;responses=responses+1;
      end
    end
  end
  task spi(input [7:0] price, output [7:0] response);
    begin
      cs_n=0;#1000;
      for(integer b=7;b>=0;b=b-1) begin
        mosi=price[b];#500;sclk=1;
        if(miso!==1'b0 && miso!==1'b1)$fatal(1,"MISO desconocido");
        response[b]=miso;#500;sclk=0;
      end
      #500;cs_n=1;
    end
  endtask
  initial begin
    if(!$value$plusargs("TICKS=%d",ticks) || ticks<1 || ticks>20000)$fatal(1,"TICKS invalido");
    if(!$value$plusargs("PERIOD=%d",period))period=100000;
    if(!$value$plusargs("FAST=%d",fast))fast=0;
    budget=(period-9500)/40;
    if(!$value$plusargs("REF=%s",reference_path))$fatal(1,"falta REF");
    if(!$value$plusargs("OUT=%s",output_path))$fatal(1,"falta OUT");
    $readmemh(reference_path,reference,0,ticks-1);
    fd=$fopen(output_path,"w");if(!fd)$fatal(1,"no se abre OUT");
    $fdisplay(fd,"tick,price,next_decision,cash,shares,state,remaining,cycles,instructions");
    for(integer p=0;p<512;p=p+1)begin pc_cycles[p]=0;pc_ic[p]=0;end
    #4013;
    for(integer n=0;n<ticks;n=n+1) begin
      tick=n;spi(reference[n][7:0],received);
      if(received !== previous)$fatal(1,"MISO tick %0d %h != %h",n,received,previous);
      if(fast!=0) begin
        fork : await_response
          begin wait(responses==n+1);#1000;end
          begin #(period-9500);$fatal(1,"timeout tick %0d",n);end
        join_any
        disable await_response;
      end else #(period-9500);
      if(pending || responses!=n+1 || reads!=n+1 || dut.u_spi.new_price_q!==0)$fatal(1,"falta lectura/respuesta tick %0d",n);
      previous=reference[n][39:32];
    end
    if(arrivals!=ticks)$fatal(1,"conteo de llegadas");
    $fclose(fd);
    pfd=$fopen({output_path,".pc.csv"},"w");
    $fdisplay(pfd,"pc,cycles,instructions");
    for(integer p=0;p<512;p=p+1)
      if(pc_cycles[p]!=0 || pc_ic[p]!=0)$fdisplay(pfd,"%0d,%0d,%0d",p*4,pc_cycles[p],pc_ic[p]);
    $fclose(pfd);
    $display("PASS M105-225: %0d ticks, decisiones/caja/inventario/estado/presupuesto/MISO exactos; deadline %0d < %0d",ticks,max_cycles,budget);
    $finish;
  end
endmodule
