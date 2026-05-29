#!/usr/bin/env bash

set -euo pipefail

# Load environment variables
# shellcheck source=/.env
source /.env

DATE="$(date '+%F_%H-%M')"
MONTH="$(
  LC_ALL="${LC_ALL:-C}" date +%B |
    sed 's/.*/\u&/'
)"
YEAR="$(LC_ALL="${LC_ALL:-C}" date +%Y)"

# Defaults
SILENT_TEST="${SILENT_TEST:-no}"
DOWNLOAD_TEST_ENABLE="${DOWNLOAD_TEST_ENABLE:-no}"
UPLOAD_TEST_ENABLE="${UPLOAD_TEST_ENABLE:-no}"
PING_TEST_ENABLE="${PING_TEST_ENABLE:-no}"
THROTTLE_ENABLE="${THROTTLE_ENABLE:-no}"
SEND_RESULTS_EMAIL="${SEND_RESULTS_EMAIL:-no}"

TESTS_RESULTS_DIR="${TESTS_RESULTS_DIR:-/test_results}"
TMP_RESULTS_DIR="${TMP_RESULTS_DIR:-/tmp/network-tests}"

COMPRESS_RESULTS="${COMPRESS_RESULTS:-yes}"

COMPRESSED_RESULTS_FILE="${COMPRESSED_RESULTS_FILE:-${TESTS_RESULTS_DIR}/network-tests-${DATE}.zip}"

# Download test
DOWNLOAD_TEST_COUNT="${DOWNLOAD_TEST_COUNT:-1}"
DOWNLOAD_TEST_LOCATION="${DOWNLOAD_TEST_LOCATION:-use}"
DOWNLOAD_TEST_OUTFILE="${DOWNLOAD_TEST_OUTFILE:-download-test-${DATE}.csv}"
DOWNLOAD_TEST_SILENT="${SILENT_TEST}"

# Upload test
UPLOAD_TEST_COUNT="${UPLOAD_TEST_COUNT:-1}"
UPLOAD_TEST_OUTFILE="${UPLOAD_TEST_OUTFILE:-upload-test-${DATE}.csv}"
UPLOAD_TEST_SILENT="${SILENT_TEST}"
UPLOAD_TEST_PASSIVE="${UPLOAD_TEST_PASSIVE:-no}"

# Ping test
PING_TEST_COUNT="${PING_TEST_COUNT:-1}"
PING_TEST_FILE="${PING_TEST_FILE:-/opt/network-tests-${VERSION}/ping/hosts.txt}"
PING_TEST_OUTFILE="${PING_TEST_OUTFILE:-ping-test-${DATE}.csv}"
PING_TEST_SILENT="${SILENT_TEST}"

# Email
TEMPLATE_FILE="${TEMPLATE_FILE:-/templates/network-tests_results}"
SMTP_SERVER="${SMTP_SERVER:-postfix}"

SMTP_SUBJECT="${SMTP_SUBJECT:-Network-tests: Performance Results for ${MONTH} of ${YEAR}}"

log() {
  echo -e "$1"
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: Required command not found: $1"
    exit 1
  }
}

enable_throttle() {
  local args=()

  [[ -n "${THROTTLE_DOWN_SPEED:-}" ]] &&
    args+=(--down "${THROTTLE_DOWN_SPEED}")

  [[ -n "${THROTTLE_UP_SPEED:-}" ]] &&
    args+=(--up "${THROTTLE_UP_SPEED}")

  [[ -n "${THROTTLE_RTT:-}" ]] &&
    args+=(--rtt "${THROTTLE_RTT}")

  if [[ -n "${THROTTLE_PROFILE:-}" ]]; then
    throttle --profile "${THROTTLE_PROFILE}"
  else
    throttle "${args[@]}"
  fi
}

do_download_test() {
  local args=(
    -c "${DOWNLOAD_TEST_COUNT}"
    -l "${DOWNLOAD_TEST_LOCATION}"
    -o "${TMP_RESULTS_DIR}/${DOWNLOAD_TEST_OUTFILE}"
  )

  [[ -n "${DOWNLOAD_TEST_URL:-}" ]] &&
    args+=(-u "${DOWNLOAD_TEST_URL}")

  [[ "${DOWNLOAD_TEST_SILENT}" == "yes" ]] &&
    args+=(-s)

  download-tester "${args[@]}"
}

do_upload_test() {
  local args=(
    -c "${UPLOAD_TEST_COUNT}"
    -f "${UPLOAD_TEST_FILE}"
    -o "${TMP_RESULTS_DIR}/${UPLOAD_TEST_OUTFILE}"
    -l "${UPLOAD_TEST_HOST}"
    -u "${UPLOAD_TEST_USER}"
    -p "${UPLOAD_TEST_PASSWORD}"
  )

  [[ "${UPLOAD_TEST_PASSIVE}" == "yes" ]] &&
    args+=(-P yes)

  [[ "${UPLOAD_TEST_SILENT}" == "yes" ]] &&
    args+=(-s)

  upload-tester "${args[@]}"
}

do_ping_test() {
  local args=(
    -c "${PING_TEST_COUNT}"
    -f "${PING_TEST_FILE}"
    -o "${TMP_RESULTS_DIR}/${PING_TEST_OUTFILE}"
  )

  [[ -n "${PING_TEST_INTERFACE:-}" ]] &&
    args+=(-I "${PING_TEST_INTERFACE}")

  [[ "${PING_TEST_SILENT}" == "yes" ]] &&
    args+=(-s)

  ping-tester "${args[@]}"
}

compress_results() {
  log "\n* Compressing test results...\n"

  (
    cd "${TMP_RESULTS_DIR}" || exit 1
    zip -r "${COMPRESSED_RESULTS_FILE}" .
  )

  log "\n* Done.\n"
}

email_results() {
  require_command sendEmail

  log "Sending results by email to: ${SMTP_TO}"

  if [[ ! -f "${COMPRESSED_RESULTS_FILE}" ]]; then

    log "ERROR: File to attach not found."

    sendEmail \
      -f "${SMTP_FROM}" \
      -t "${SMTP_FROM}" \
      -u "Warning: Cannot find test results file !!" \
      -s "${SMTP_SERVER}" \
      -o message-charset=utf8 \
      -m "Could not find test results at: ${COMPRESSED_RESULTS_FILE}"

    exit 1
  fi

  local content

  content="$(
    sed \
      -e "s/\${SMTP_TO_NAME}/${SMTP_TO_NAME}/g" \
      -e "s/\${MONTH}/${MONTH}/g" \
      -e "s/\${YEAR}/${YEAR}/g" \
      "${TEMPLATE_FILE}"
  )"

  sendEmail \
    -f "${SMTP_FROM}" \
    -t "${SMTP_TO}" \
    -bcc "${SMTP_BCC:-}" \
    -u "${SMTP_SUBJECT}" \
    -s "${SMTP_SERVER}" \
    -a "${COMPRESSED_RESULTS_FILE}" \
    -m "${content}" \
    -o message-charset=utf8
}

remove_quotes() {
  local temp="${1%\"}"
  temp="${temp#\"}"

  echo "${temp}"
}
