PYTHON ?= python3
BUILD_DIR := build
ROM := $(BUILD_DIR)/librekick-m2_11.rom

.PHONY: all check clean m0 m1 m2 m2_1 m2_2 m2_3 m2_4 m2_6 m2_7 m2_8 m2_9 m2_10 m2_11 qualify-m1 qualify-m2 qualify-m2_1 qualify-m2_2 qualify-m2_3 qualify-m2_4 qualify-m2_5 qualify-m2_6 qualify-m2_7 qualify-m2_8 qualify-m2_9 qualify-m2_10 qualify-m2_11

all: $(ROM)

$(ROM): tools/make_m2_11_rom.py
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_11_rom.py $@

check: $(ROM)
	$(PYTHON) tools/check_m2_11.py $(ROM)

qualify-m2_11: check
	fs-uae configs/fs-uae/a500-m2_11.fs-uae

m2_11:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_11_rom.py $(BUILD_DIR)/librekick-m2_11.rom
	$(PYTHON) tools/check_m2_11.py $(BUILD_DIR)/librekick-m2_11.rom

qualify-m2_10:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_10_rom.py $(BUILD_DIR)/librekick-m2_10.rom
	$(PYTHON) tools/check_m2_10.py $(BUILD_DIR)/librekick-m2_10.rom
	fs-uae configs/fs-uae/a500-m2_10.fs-uae

m2_10:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_10_rom.py $(BUILD_DIR)/librekick-m2_10.rom
	$(PYTHON) tools/check_m2_10.py $(BUILD_DIR)/librekick-m2_10.rom

qualify-m2_9:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_9_rom.py $(BUILD_DIR)/librekick-m2_9.rom
	$(PYTHON) tools/check_m2_9.py $(BUILD_DIR)/librekick-m2_9.rom
	fs-uae configs/fs-uae/a500-m2_9.fs-uae

m2_9:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_9_rom.py $(BUILD_DIR)/librekick-m2_9.rom
	$(PYTHON) tools/check_m2_9.py $(BUILD_DIR)/librekick-m2_9.rom

qualify-m2_8:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_8_rom.py $(BUILD_DIR)/librekick-m2_8.rom
	$(PYTHON) tools/check_m2_8.py $(BUILD_DIR)/librekick-m2_8.rom
	fs-uae configs/fs-uae/a500-m2_8.fs-uae

m2_8:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_8_rom.py $(BUILD_DIR)/librekick-m2_8.rom
	$(PYTHON) tools/check_m2_8.py $(BUILD_DIR)/librekick-m2_8.rom

qualify-m2_7:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_7_rom.py $(BUILD_DIR)/librekick-m2_7.rom
	$(PYTHON) tools/check_m2_7.py $(BUILD_DIR)/librekick-m2_7.rom
	fs-uae configs/fs-uae/a500-m2_7.fs-uae

m2_7:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_7_rom.py $(BUILD_DIR)/librekick-m2_7.rom
	$(PYTHON) tools/check_m2_7.py $(BUILD_DIR)/librekick-m2_7.rom

qualify-m2_6:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_6_rom.py $(BUILD_DIR)/librekick-m2_6.rom
	$(PYTHON) tools/check_m2_6.py $(BUILD_DIR)/librekick-m2_6.rom
	fs-uae configs/fs-uae/a500-m2_6.fs-uae

m2_6:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_6_rom.py $(BUILD_DIR)/librekick-m2_6.rom
	$(PYTHON) tools/check_m2_6.py $(BUILD_DIR)/librekick-m2_6.rom

qualify-m2_5:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_5_rom.py $(BUILD_DIR)/librekick-m2_5.rom
	$(PYTHON) tools/check_m2_5.py $(BUILD_DIR)/librekick-m2_5.rom
	fs-uae configs/fs-uae/a500-m2_5.fs-uae

qualify-m2_4:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_4_rom.py $(BUILD_DIR)/librekick-m2_4.rom
	$(PYTHON) tools/check_m2_4.py $(BUILD_DIR)/librekick-m2_4.rom
	fs-uae configs/fs-uae/a500-m2_4.fs-uae

qualify-m2_3:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_3_rom.py $(BUILD_DIR)/librekick-m2_3.rom
	$(PYTHON) tools/check_m2_3.py $(BUILD_DIR)/librekick-m2_3.rom
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

m2_4:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_4_rom.py $(BUILD_DIR)/librekick-m2_4.rom
	$(PYTHON) tools/check_m2_4.py $(BUILD_DIR)/librekick-m2_4.rom

m2_3:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_3_rom.py $(BUILD_DIR)/librekick-m2_3.rom
	$(PYTHON) tools/check_m2_3.py $(BUILD_DIR)/librekick-m2_3.rom

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
