PYTHON ?= python3
BUILD_DIR := build
ROM := $(BUILD_DIR)/librekick-m2_3.rom

.PHONY: all check clean m0 m1 m2 m2_1 m2_2 qualify-m1 qualify-m2 qualify-m2_1 qualify-m2_2 qualify-m2_3

all: $(ROM)

$(ROM): tools/make_m2_3_rom.py
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_3_rom.py $@

check: $(ROM)
	$(PYTHON) tools/check_m2_3.py $(ROM)

qualify-m2_3: check
	fs-uae configs/fs-uae/a500-m2_3.fs-uae

qualify-m2_2:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_2_rom.py $(BUILD_DIR)/librekick-m2_2.rom
	$(PYTHON) tools/check_m2_2.py $(BUILD_DIR)/librekick-m2_2.rom
	fs-uae configs/fs-uae/a500-m2_2.fs-uae

qualify-m2_1:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_1_rom.py $(BUILD_DIR)/librekick-m2_1.rom
	$(PYTHON) tools/check_m2_1.py $(BUILD_DIR)/librekick-m2_1.rom
	fs-uae configs/fs-uae/a500-m2_1.fs-uae

qualify-m2:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_rom.py $(BUILD_DIR)/librekick-m2.rom
	$(PYTHON) tools/check_m2.py $(BUILD_DIR)/librekick-m2.rom
	fs-uae configs/fs-uae/a500-m2.fs-uae

qualify-m1:
	bash tools/qualify_m1_fsuae.sh

m2_2:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_2_rom.py $(BUILD_DIR)/librekick-m2_2.rom
	$(PYTHON) tools/check_m2_2.py $(BUILD_DIR)/librekick-m2_2.rom

m2_1:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_1_rom.py $(BUILD_DIR)/librekick-m2_1.rom
	$(PYTHON) tools/check_m2_1.py $(BUILD_DIR)/librekick-m2_1.rom

m2:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_rom.py $(BUILD_DIR)/librekick-m2.rom
	$(PYTHON) tools/check_m2.py $(BUILD_DIR)/librekick-m2.rom

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
