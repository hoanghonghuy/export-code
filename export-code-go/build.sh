#!/bin/bash

# build.sh - Script to build export-code-go for multiple platforms

set -e # Exit immediately if a command exits with a non-zero status.

BINARY_NAME="export-code"
SOURCE_DIR="cmd/export-code"
VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "unknown")
BUILD_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)

LDFLAGS="-X main.version=${VERSION} -X main.buildTime=${BUILD_TIME}"

echo "Building ${BINARY_NAME} version ${VERSION}..."

# Build for the current platform by default
echo "Building for current platform..."
go build -ldflags="${LDFLAGS}" -o "bin/${BINARY_NAME}" "${SOURCE_DIR}"

# Optionally, build for other common platforms
# Uncomment the lines below to build for specific platforms.

# echo "Building for Linux AMD64..."
# GOOS=linux GOARCH=amd64 go build -ldflags="${LDFLAGS}" -o "bin/${BINARY_NAME}_linux_amd64" "${SOURCE_DIR}"

# echo "Building for Windows AMD64..."
# GOOS=windows GOARCH=amd64 go build -ldflags="${LDFLAGS}" -o "bin/${BINARY_NAME}_windows_amd64.exe" "${SOURCE_DIR}"

# echo "Building for macOS AMD64..."
# GOOS=darwin GOARCH=amd64 go build -ldflags="${LDFLAGS}" -o "bin/${BINARY_NAME}_darwin_amd64" "${SOURCE_DIR}"

# echo "Building for macOS ARM64..."
# GOOS=darwin GOARCH=arm64 go build -ldflags="${LDFLAGS}" -o "bin/${BINARY_NAME}_darwin_arm64" "${SOURCE_DIR}"

echo "Build complete. Binaries are in the 'bin' directory."