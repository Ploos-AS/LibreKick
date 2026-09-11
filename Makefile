PYTHON ?= python3
BUILD_DIR := build
ROM := $(BUILD_DIR)/librekick-m2_14.rom

.PHONY: all check clean m0 m1 m2 qualify-m1 qualify-m2 qualify-m2_14 m2_14

all: $(ROM)

$(ROM): tools/make_m2_14_rom.py
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_14_rom.py $@

check: $(ROM)
	$(PYTHON) tools/check_m2_14.py $(ROM)

qualify-m2_14: check
	fs-uae configs/fs-uae/a500-m2_14.fs-uae

m2_14:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_14_rom.py $(BUILD_DIR)/librekick-m2_14.rom
	$(PYTHON) tools/check_m2_14.py $(BUILD_DIR)/librekick-m2_14.rom

# Generic historical M2.x build/qualification targets.
m2_%:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_$*_rom.py $(BUILD_DIR)/librekick-m2_$*.rom
	$(PYTHON) tools/check_m2_$*.py $(BUILD_DIR)/librekick-m2_$*.rom

qualify-m2_%:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_$*_rom.py $(BUILD_DIR)/librekick-m2_$*.rom
	$(PYTHON) tools/check_m2_$*.py $(BUILD_DIR)/librekick-m2_$*.rom
	fs-uae configs/fs-uae/a500-m2_$*.fs-uae

qualify-m2:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_rom.py $(BUILD_DIR)/librekick-m2.rom
	$(PYTHON) tools/check_m2.py $(BUILD_DIR)/librekick-m2.rom
	fs-uae configs/fs-uae/a500-m2.fs-uae

m2:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_rom.py $(BUILD_DIR)/librekick-m2.rom
	$(PYTHON) tools/check_m2.py $(BUILD_DIR)/librekick-m2.rom

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
