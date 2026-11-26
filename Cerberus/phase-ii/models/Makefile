BUILD := build
FPC ?= fpc

.PHONY: all test clean
all: $(BUILD)/gate $(BUILD)/Frame.class $(BUILD)/frame-pascal

$(BUILD):
	mkdir -p $@

$(BUILD)/gate.o: gate.s | $(BUILD)
	as --64 -o $@ $<

$(BUILD)/gate: $(BUILD)/gate.o
	ld -o $@ $<

$(BUILD)/Frame.class: Frame.java | $(BUILD)
	javac --release 17 -d $(BUILD) $<

$(BUILD)/frame-pascal: frame.pas | $(BUILD)
	$(FPC) -FU$(BUILD) -o$@ $<

test: all
	python3 -m unittest -v test_contract

clean:
	rm -rf -- $(BUILD)
