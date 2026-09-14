PYTHON ?= python3
BUILD_DIR := build
ROM := $(BUILD_DIR)/librekick-m2_43.rom
A500_PROFILE_ROM := $(BUILD_DIR)/a500/librekick-m2_43-a500.rom
A500PLUS_PROFILE_ROM := $(BUILD_DIR)/a500plus/librekick-m2_43-a500plus.rom

.PHONY: all check clean m0 m1 m2 qualify-m1 qualify-m2 qualify-m2_43 m2_43 profile-a500 qualify-profile-a500 profile-a500plus qualify-profile-a500plus

all: $(ROM)

$(ROM): tools/make_m2_43_rom.py
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_43_rom.py $@

check: $(ROM)
	$(PYTHON) tools/check_m2_43.py $(ROM)

qualify-m2_43: check
	fs-uae configs/fs-uae/a500-m2_43.fs-uae

m2_43:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/make_m2_43_rom.py $(BUILD_DIR)/librekick-m2_43.rom
	$(PYTHON) tools/check_m2_43.py $(BUILD_DIR)/librekick-m2_43.rom

# Retained machine-profile builds. These are model-explicit artifacts and must
# remain available as additional Amiga profiles are introduced.
profile-a500:
	$(PYTHON) tools/build_profile.py a500

qualify-profile-a500: profile-a500
	fs-uae configs/fs-uae/a500-current.fs-uae

profile-a500plus:
	$(PYTHON) tools/build_profile.py a500plus

qualify-profile-a500plus: profile-a500plus
	fs-uae configs/fs-uae/a500plus-current.fs-uae

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
