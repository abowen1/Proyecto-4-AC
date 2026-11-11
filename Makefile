# Copyright 2026 Universidad de los Andes.
# Licensed under the Solderpad Hardware License, Version 0.51 (the "License");
# you may not use this file except in compliance with the License.
# SPDX-License-Identifier: SHL-0.51
#
# Course: Arquitectura de Computadores (2026)
# 
# Authors:
# - Nicolás Villegas <navillegas@miuandes.cl>

PYTHON ?= python3
SRC := $(wildcard rtl/*.v rtl/espino_core/*.v)
ICE40_CELLS ?= $(shell yosys-config --datdir)/ice40/cells_sim.v
.DEFAULT_GOAL := help
.PHONY: compare test-market
.PHONY: compare-reversion
.PHONY: compare-protections
compare-protections:
	$(PYTHON) tools/compare_protections.py
compare-reversion:
	$(PYTHON) tools/compare_reversion.py
compare:
	$(PYTHON) tools/backtest.py
	$(PYTHON) tools/verify_market.py
test-market:
	$(PYTHON) -B -m unittest discover -s tests -p 'test_backtest.py' -v
.PHONY: help assemble test test-spi test-canvas build program
help:
	@echo "make test: ensamblador y SPI en tres rondas; make test-canvas: ejemplo oficial"
	@echo "make build: bitstream a 25 MHz; make program: cargar placa explícitamente"
assemble: sw/trade.hex sw/spi_diagnostic.hex
sw/%.hex: sw/%.s tools/assembler.py
	$(PYTHON) tools/assembler.py $< -o $@
test: assemble
	$(PYTHON) -B -m unittest discover -s tests -v
	$(MAKE) test-spi
test-spi: assemble
	mkdir -p build
	iverilog -g2012 -DNO_ICE40_DEFAULT_ASSIGNMENTS -s tb_spi_ac4 -o build/tb_spi $(ICE40_CELLS) $(SRC) tb/tb_spi_ac4.sv
	iverilog -g2012 -DNO_ICE40_DEFAULT_ASSIGNMENTS -DDIAGNOSTIC -s tb_spi_ac4 -o build/tb_spi_diag $(ICE40_CELLS) $(SRC) tb/tb_spi_ac4.sv
	@for period in 10000000 1000000 100000; do vvp -n build/tb_spi +PERIOD=$$period || exit 1; vvp -n build/tb_spi_diag +PERIOD=$$period || exit 1; done
test-canvas: assemble
	mkdir -p build
	iverilog -g2012 -DNO_ICE40_DEFAULT_ASSIGNMENTS -s tb_proyecto_4 -o build/tb_canvas $(ICE40_CELLS) $(SRC) tb/tb_proyecto_4.sv
	vvp -n build/tb_canvas
build: build/ac4.bin
build/ac4.json: $(SRC) sw/trade.hex Makefile
	mkdir -p build
	yosys -l build/synthesis.log -p 'read_verilog $(SRC); chparam -set MemFile "sw/trade.hex" pochoco_soc; synth_ice40 -top pochoco_soc -json $@; stat'
build/ac4.asc: build/ac4.json goboard.pcf Makefile
	nextpnr-ice40 --hx1k --package vq100 --json $< --pcf goboard.pcf --asc $@ --freq 25 --report build/timing.json --log build/place_route.log
build/ac4.bin: build/ac4.asc
	icepack $< $@
program: build/ac4.bin
	iceprog $<
