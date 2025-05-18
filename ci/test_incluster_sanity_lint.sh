#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# USER CONFIG (adapt to your environment)
###############################################################################
NAMESPACE="default"
IMAGE="${ANSIBLE_TEST_IMAGE}"

###############################################################################
# INTERNALS – no change required below here
###############################################################################
JOB=ansible-collection-ci
SECRET=kubeconfig-secret
LOG_VOL=logs
LOG_PATH=/logs/collection_ci.log          # must match CI script
SCRIPT=/opt/ansible/ci/ansible_sanity_test.sh   # path **inside** the image
TIMEOUT="30"                         # overall time-limit

echo "🔑  Checking namespace '$NAMESPACE'…"
oc get ns "$NAMESPACE" 2>/dev/null || oc create ns "$NAMESPACE"
oc project "$NAMESPACE"

echo "🔑  Creating/renewing secret '$SECRET' with your kubeconfig"
oc create secret generic "$SECRET" \
      --from-file=kubeconfig="$KUBECONFIG" \
      --dry-run=client -o yaml | oc apply -f -

echo "🧹  Deleting old Job (if any)"
oc delete job "$JOB" --ignore-not-found --wait

echo "🚀  Creating Job '$JOB'"
cat <<EOF | oc apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: ${JOB}
spec:
  backoffLimit: 1
  template:
    spec:
      #backoffLimit: 0
      restartPolicy: Never
      containers:
        - name: collection-ci
          image: ${IMAGE}
          imagePullPolicy: IfNotPresent
          command: ["/bin/bash","-c"]
          # Run the CI script that is baked into the image
          args:
            - |
              export KUBECONFIG=/kubeconfig/kubeconfig
              export LOGFILE=${LOG_PATH}
              ${SCRIPT}
          env:
            - name: KUBECONFIG
              value: /kubeconfig/kubeconfig
          volumeMounts:
            - name: kubeconf
              mountPath: /kubeconfig
              readOnly: true
            - name: ${LOG_VOL}
              mountPath: ${LOG_PATH%/*}
      volumes:
        - name: kubeconf
          secret:
            secretName: ${SECRET}
        - name: ${LOG_VOL}
          emptyDir: {}
EOF

###############################################################################
# Helper functions                                                           #
###############################################################################

# Return "<succeeded>,<failed>" counters (keeps it tiny and fast)
get_job_state () {
  oc get job "$JOB" -n "$NAMESPACE" \
     -o jsonpath='{.status.succeeded}{","}{.status.failed}' 2>/dev/null || echo ","
}

# Job finished OK?
check_success () {
  if [[ $(get_job_state) == 1,* ]]; then
    oc logs -n "$NAMESPACE" job/"$JOB"
    echo "✅ Job succeeded"
    return 0
  fi
  return 1
}

# Job failed at least once?
check_failure () {
  if [[ $(get_job_state) == *,[1-9]* ]]; then
    oc logs -n "$NAMESPACE" job/"$JOB"
    echo "❌ Job failed – see logs above"
    return 0
  fi
  return 1
}

###############################################################################
# Wait loop                                                                  #
###############################################################################

if [[ "$(uname)" == "Darwin" ]]; then
  endtime=$(date -v+"${TIMEOUT}"M +%s)
else
  endtime=$(date -ud "+${TIMEOUT} minutes" +%s)
fi

echo "⏳  Waiting for Job to finish (max ${TIMEOUT} min)…"
while [[ $(date -u +%s) -le $endtime ]]; do
  if check_success; then
    exit 0
  elif check_failure; then
    exit 1
  fi
  sleep 10
done

# timed-out
oc logs -n "$NAMESPACE" job/"$JOB"
echo "❌ Timed out waiting for the Job to finish"
exit 1

