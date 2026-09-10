PYTHON ?= python3
BUILD_DIR := build
ROM := $(BUILD_DIR)/librekick-m1.rom

.PHONY: all check clean m0

all: $(ROM)

$(ROM): tools/make_m1_rom.py
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m1_rom.py $@

check: $(ROM)
	$(PYTHON) tools/check_m1.py $(ROM)

m0:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m0_rom.py $(BUILD_DIR)/librekick-m0.rom
	$(PYTHON) tools/check_m0.py $(BUILD_DIR)/librekick-m0.rom

clean:
	rm -rf $(BUILD_DIR)
