PYTHON ?= python3
BUILD_DIR := build
ROM := $(BUILD_DIR)/librekick-m2.rom

.PHONY: all check clean m0 m1 qualify-m1 qualify-m2

all: $(ROM)

$(ROM): tools/make_m2_rom.py
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_rom.py $@

check: $(ROM)
	$(PYTHON) tools/check_m2.py $(ROM)

qualify-m2: check
	fs-uae configs/fs-uae/a500-m2.fs-uae

qualify-m1:
	bash tools/qualify_m1_fsuae.sh

m1:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m1_rom.py $(BUILD_DIR)/librekick-m1.rom
	$(PYTHON) tools/check_m1.py $(BUILD_DIR)/librekick-m1.rom

m0:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m0_rom.py $(BUILD_DIR)/librekick-m0.rom
	$(PYTHON) tools/check_m0.py $(BUILD_DIR)/librekick-m0.rom

clean:
	rm -rf $(BUILD_DIR)
