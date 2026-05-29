#!/usr/bin/env bash

set -euo pipefail

# Load helper functions
# shellcheck source=/functions.sh
source /functions.sh

# Create results directories
mkdir -p "${TESTS_RESULTS_DIR}"

rm -rf "${TMP_RESULTS_DIR}"
mkdir -p "${TMP_RESULTS_DIR}"

log_section() {
  echo -e "\n* $1...\n"
}

require_var() {
  local var_name="$1"

  if [[ -z "${!var_name:-}" ]]; then
    echo "ERROR: ${var_name} not set."
    exit 1
  fi
}

cleanup() {
  if [[ "${THROTTLE_ENABLE:-no}" == "yes" ]]; then
    if ! throttle --stop; then
      echo "ERROR: Cannot stop throttle."
      exit 1
    fi
  fi
}

trap cleanup EXIT

# Enable throttle
if [[ "${THROTTLE_ENABLE:-no}" == "yes" ]]; then
  echo
  enable_throttle
  echo
fi

# Download tests
if [[ "${DOWNLOAD_TEST_ENABLE:-no}" == "yes" ]]; then
  log_section "Starting download tests"

  do_download_test

  log_section "Download tests completed"
fi

# Upload tests
if [[ "${UPLOAD_TEST_ENABLE:-no}" == "yes" ]]; then

  require_var "UPLOAD_TEST_FILE"
  require_var "UPLOAD_TEST_HOST"
  require_var "UPLOAD_TEST_USER"
  require_var "UPLOAD_TEST_PASSWORD"

  log_section "Starting upload tests"

  do_upload_test

  log_section "Upload tests completed"
fi

# Ping tests
if [[ "${PING_TEST_ENABLE:-no}" == "yes" ]]; then
  log_section "Starting ping tests"

  do_ping_test

  log_section "Ping tests completed"
fi

# Compress results
if [[ "${COMPRESS_RESULTS:-no}" == "yes" ]]; then
  compress_results
fi

# Email results
if [[ "${SEND_RESULTS_EMAIL:-no}" == "yes" ]]; then
  email_results
fi
