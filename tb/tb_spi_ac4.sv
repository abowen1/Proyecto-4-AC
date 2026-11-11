`timescale 1ns/1ps
module tb_spi_ac4;
`ifdef DIAGNOSTIC
  localparam PROGRAM = "sw/spi_diagnostic.hex";
  localparam DIAG = 1;
`else
  localparam PROGRAM = "sw/trade.hex";
  localparam DIAG = 0;
`endif
  reg clk=0, sclk=0, mosi=0, cs_n=1;
  wire miso;
  always #20 clk=~clk;
  pochoco_soc #(.MemFile(PROGRAM)) dut (
    .i_Clk(clk), .i_Switch(4'b0), .o_LED(),
    .i_SPI_SCLK(sclk), .i_SPI_MOSI(mosi), .i_SPI_CS_n(cs_n), .o_SPI_MISO(miso));
  integer period=100000, cycle=0, arrivals=0, reads=0, writes=0;
  integer start_cycle=0, ic=0, max_cycles=0, max_ic=0, fd;
  integer expected_price=0, current_tick=-1, n, budget;
  reg pending=0, saw_price=0;
  reg [7:0] received, previous=0;
  wire commit = dut.u_core.instr_valid_id && !dut.u_core.stall;
  always @(posedge clk) begin
    cycle=cycle+1;
    if (dut.rst_ni) begin
      if (dut.u_core.illegal_insn === 1'b1 && dut.u_core.instr_valid_id)
        $fatal(1,"instrucción ilegal");
      if (dut.u_spi.byte_done) begin
        if(pending || dut.u_spi.new_price_q) $fatal(1,"precio anterior pendiente");
        arrivals=arrivals+1; pending=1; saw_price=0; start_cycle=cycle; ic=0;
      end
      if (pending && commit) ic=ic+1;
      if (pending && commit && dut.u_core.rf_we && dut.u_core.rf_waddr==3) begin
        if (!saw_price) begin
          if (dut.u_core.rf_wdata !== expected_price)
            $fatal(1,"PRICE CPU incorrecto: esperado %0d recibido %h",expected_price,dut.u_core.rf_wdata);
          saw_price=1; reads=reads+1;
        end
      end
      if(dut.u_spi.wr && dut.u_spi.off==2 && current_tick>=0) begin
        if(!pending || !saw_price) $fatal(1,"decisión repetida o sin lectura");
        if(dut.data_wdata[7:0] !== (DIAG ? (expected_price & 63) : 0))
          $fatal(1,"DECISION incorrecta");
        if(cycle-start_cycle >= budget) $fatal(1,"deadline incumplido");
        if(cycle-start_cycle>max_cycles) max_cycles=cycle-start_cycle;
        if(ic>max_ic) max_ic=ic;
        $fdisplay(fd,"%0d,%0d,%0d,%0d,%0d,%0f,%0d",current_tick,expected_price,dut.data_wdata[7:0],ic,cycle-start_cycle,real'(cycle-start_cycle)/ic,(cycle-start_cycle)*40);
        writes=writes+1; pending=0;
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
  function integer price_at(input integer i);
    case(i%6)
      0: price_at=1; 1: price_at=255; 2: price_at=128;
      3: price_at=64; 4: price_at=63; default: price_at=151;
    endcase
  endfunction
  initial begin
    if(!$value$plusargs("PERIOD=%d",period)) period=100000;
    budget=(period-9500)/40;
    fd=$fopen($sformatf("build/spi_metrics_%0d_%0d.csv",period,DIAG),"w");
    if(!fd) $fatal(1,"no se pudo abrir salida");
    $fdisplay(fd,"tick,price,decision,instructions,cycles,cpi,latency_ns");
    #4013;
    if(dut.u_spi.tx_hold!==0) $fatal(1,"arranque no mantiene");
    for(n=0;n<12;n=n+1) begin
      current_tick=n; expected_price=price_at(n);
      spi(expected_price,received);
      if(received !== previous) $fatal(1,"MISO no es decisión anterior: %h != %h",received,previous);
      #(period-9500);
      if(pending || writes!=n+1 || reads!=n+1 || dut.u_spi.new_price_q!==0)
        $fatal(1,"falta respuesta o consumo en tick %0d",n);
      previous=DIAG ? (expected_price & 63) : 0;
    end
    $fclose(fd);
    if(arrivals!=12 || writes!=12 || reads!=12) $fatal(1,"conteos distintos");
    $display("PASS SPI diag=%0d T=%0d ns: 12 precios y respuestas; max=%0d ciclos (%0d ns), max_IC=%0d; presupuesto=%0d",DIAG,period,max_cycles,max_cycles*40,max_ic,budget);
    $finish;
  end
  initial begin #130000000; $fatal(1,"timeout global SPI"); end
endmodule
