// Equivalencia completa por SPI real contra la referencia Python D.
`timescale 1ns/1ps
module tb_strategy_d;
  reg clk=0, sclk=0, mosi=0, cs_n=1;
  wire miso;
  always #20 clk=~clk;
  pochoco_soc #(.MemFile("sw/trade.hex")) dut (
    .i_Clk(clk), .i_Switch(4'b0), .o_LED(),
    .i_SPI_SCLK(sclk), .i_SPI_MOSI(mosi), .i_SPI_CS_n(cs_n), .o_SPI_MISO(miso));
  reg [127:0] reference [0:99999]; // caja, acciones, orden siguiente, precio
  string reference_path, metrics_path;
  integer ticks, period, fast=0, tick=-1, cycle=0, start_cycle, instructions=0;
  integer arrivals=0, responses=0, reads=0, max_cycles=0, max_instructions=0;
  integer cash=0, shares=0, fd, budget;
  reg pending=0;
  reg [7:0] received, previous=0;
  wire commit = dut.u_core.instr_valid_id && !dut.u_core.stall;
  always @(posedge clk) begin
    cycle=cycle+1;
    if(dut.rst_ni) begin
      if(commit && dut.u_core.illegal_insn !== 1'b0)
        $fatal(1,"instruccion ilegal/desconocida");
      if(commit && dut.u_core.rf_we) begin
        if(dut.u_core.rf_waddr==3) cash=dut.u_core.rf_wdata;
        if(dut.u_core.rf_waddr==4) shares=dut.u_core.rf_wdata;
      end
      if(dut.u_spi.byte_done) begin
        if(pending || dut.u_spi.new_price_q) $fatal(1,"precio perdido en %0d",tick);
        arrivals=arrivals+1; pending=1; start_cycle=cycle; instructions=0;
      end
      if(pending && commit) instructions=instructions+1;
      if(dut.u_spi.price_read) reads=reads+1;
      if(dut.u_spi.wr && dut.u_spi.off==2 && tick>=0) begin
        if(!pending) $fatal(1,"respuesta duplicada en %0d",tick);
        if(dut.data_wdata !== reference[tick][63:32])
          $fatal(1,"orden tick %0d: %h esperado %h",tick,dut.data_wdata,reference[tick][63:32]);
        if(cash !== reference[tick][127:96] || shares !== reference[tick][95:64])
          $fatal(1,"contabilidad tick %0d: caja %0d/%0d acciones %0d/%0d",tick,cash,reference[tick][127:96],shares,reference[tick][95:64]);
        if(cycle-start_cycle >= budget) $fatal(1,"deadline tick %0d: %0d >= %0d",tick,cycle-start_cycle,budget);
        if(cycle-start_cycle>max_cycles) max_cycles=cycle-start_cycle;
        if(instructions>max_instructions) max_instructions=instructions;
        $fdisplay(fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d",tick,reference[tick][31:0],dut.data_wdata,cash,shares,instructions,cycle-start_cycle);
        pending=0; responses=responses+1;
      end
    end
  end
  task spi(input [7:0] price, output [7:0] response);
    begin
      cs_n=0; #1000;
      for(integer b=7;b>=0;b=b-1) begin
        mosi=price[b]; #500; sclk=1;
        if(miso!==1'b0 && miso!==1'b1) $fatal(1,"MISO desconocido");
        response[b]=miso; #500; sclk=0;
      end
      #500; cs_n=1;
    end
  endtask
  initial begin
    if(!$value$plusargs("TICKS=%d",ticks) || ticks<1 || ticks>100000) $fatal(1,"TICKS invalido");
    if(!$value$plusargs("PERIOD=%d",period)) period=100000;
    if(!$value$plusargs("FAST=%d",fast)) fast=0;
    budget=(period-9500)/40;
    if(!$value$plusargs("REF=%s",reference_path)) $fatal(1,"falta REF");
    if(!$value$plusargs("METRICS=%s",metrics_path)) $fatal(1,"falta METRICS");
    $readmemh(reference_path,reference,0,ticks-1);
    fd=$fopen(metrics_path,"w");
    if(!fd) $fatal(1,"no se pudo abrir METRICS");
    $fdisplay(fd,"tick,price,next_decision,cash,shares,instructions,cycles");
    #4013;
    for(integer n=0;n<ticks;n=n+1) begin
      tick=n;
      spi(reference[n][7:0],received);
      if(received !== previous) $fatal(1,"MISO tick %0d: %h esperado %h",n,received,previous);
      if(fast!=0) begin
        // Solo prueba funcional: omite la espera ociosa entre precios.
        // CPU a 25 MHz y SPI a 1 MHz; deadline conserva el presupuesto oficial.
        fork : await_response
          begin wait(responses==n+1); #1000; end
          begin #(period-9500); $fatal(1,"timeout de respuesta en %0d",n); end
        join_any
        disable await_response;
      end else begin
        #(period-9500);
      end
      if(pending || responses!=n+1 || reads!=n+1 || dut.u_spi.new_price_q!==0)
        $fatal(1,"falta lectura/respuesta en %0d",n);
      previous=reference[n][39:32];
      if((n+1)%2000==0) $display("D: %0d/%0d ticks verificados",n+1,ticks);
    end
    if(arrivals!=ticks) $fatal(1,"conteo de llegadas incorrecto");
    $fclose(fd);
    $display("PASS D: %0d ticks; ordenes, caja, inventario y MISO exactos; max %0d ciclos, %0d instrucciones; presupuesto %0d",ticks,max_cycles,max_instructions,budget);
    $finish;
  end
endmodule
