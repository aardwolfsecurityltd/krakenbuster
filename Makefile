BINARY_NAME := krakenbuster
INSTALL_DIR := /usr/local/bin
GO := go

.PHONY: build install clean

build:
	$(GO) build -o $(BINARY_NAME) .

install: build
	cp $(BINARY_NAME) $(INSTALL_DIR)/$(BINARY_NAME)
	chmod +x $(INSTALL_DIR)/$(BINARY_NAME)

clean:
	rm -f $(BINARY_NAME)
	$(GO) clean
