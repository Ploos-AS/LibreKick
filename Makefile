PYTHON ?= python3
BUILD_DIR := build
ROM := $(BUILD_DIR)/librekick-m0.rom

.PHONY: all check clean

all: $(ROM)

$(ROM): tools/make_m0_rom.py
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m0_rom.py $@

check: $(ROM)
	$(PYTHON) tools/check_m0.py $(ROM)

clean:
	rm -rf $(BUILD_DIR)
