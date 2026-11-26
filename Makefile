PYTHON ?= python3
SRC := $(wildcard rtl/*.v rtl/espino_core/*.v)
ICE40_CELLS ?= $(shell yosys-config --datdir)/ice40/cells_sim.v
.DEFAULT_GOAL := help
.PHONY: help assemble test test-unit test-spi test-final test-integration test-hardware test-equivalence measure compare-implementations build build-final program program-final
help:
	@echo "assemble | test | test-equivalence | measure | compare-implementations | build-final | program-final"
assemble: sw/trade.hex sw/trade_m105_225.hex sw/hold.hex sw/spi_diagnostic.hex
sw/%.hex: sw/%.s tools/assembler.py
	$(PYTHON) tools/assembler.py $< -o $@
test-unit:
	$(PYTHON) -B -m unittest discover -s tests -v
test-spi: assemble
	mkdir -p build
	iverilog -g2012 -DNO_ICE40_DEFAULT_ASSIGNMENTS -s tb_spi_ac4 -o build/tb_spi $(ICE40_CELLS) $(SRC) tb/tb_spi_ac4.sv
	iverilog -g2012 -DNO_ICE40_DEFAULT_ASSIGNMENTS -DDIAGNOSTIC -s tb_spi_ac4 -o build/tb_spi_diag $(ICE40_CELLS) $(SRC) tb/tb_spi_ac4.sv
	@for period in 10000000 1000000 100000; do vvp -n build/tb_spi +PERIOD=$$period || exit 1; vvp -n build/tb_spi_diag +PERIOD=$$period || exit 1; done
test-final: assemble
	$(PYTHON) tools/verify_canvas_m105_225.py --program sw/trade.s --variant software --ticks 2000 --engine verilator
test-integration:
	$(PYTHON) tools/test_m105_225_optimized_integration.py --case soft --fixed
test-hardware:
	$(PYTHON) tools/test_hardware.py
test: assemble test-unit test-spi test-hardware test-final test-integration
test-equivalence:
	$(PYTHON) tools/compare_m105_225_implementations.py --cases soft --workers 2
measure:
	$(PYTHON) tools/measure_m105_225.py --program sw/trade.s --variant software
compare-implementations:
	$(PYTHON) tools/compare_m105_225_implementations.py --workers 2
build: build-final
build-final:
	$(PYTHON) tools/build_m105_225_final.py
# Programa la imagen verificada incluida; no regenera ni selecciona otra variante.
program: program-final
program-final:
	iceprog docs/estrategia/M105_225_optimizacion/imagen/M105_225.bin
