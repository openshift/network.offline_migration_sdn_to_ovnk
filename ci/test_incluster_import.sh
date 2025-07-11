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
JOB=galaxy-import-ci            # <─ unique job name
SECRET=kubeconfig-secret
LOG_VOL=logs
LOG_PATH=/logs/collection_ci.log
SCRIPT=/opt/ansible/ci/galaxy_import_test.sh   # <─ script inside the image
TIMEOUT="30"                    # minutes

echo "🏷️  Using image: $IMAGE"
echo "🔍  Checking namespace '$NAMESPACE'…"
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
# Wait loop
###############################################################################
get_job_state() {
  oc get job "$JOB" -n "$NAMESPACE" \
     -o jsonpath='{.status.succeeded}{","}{.status.failed}' 2>/dev/null || echo ","
}
check_success() {
  [[ "$(get_job_state)" == 1,* ]]
}
check_failure() {
  [[ "$(get_job_state)" == *,[1-9]* ]]
}

if [[ "$(uname)" == "Darwin" ]]; then
  endtime=$(date -v+"${TIMEOUT}"M +%s)
else
  endtime=$(date -ud "+${TIMEOUT} minutes" +%s)
fi
echo "⏳ Waiting for Job to finish (max ${TIMEOUT} min)…"
while [[ $(date -u +%s) -le $endtime ]]; do
  if check_success;   then oc logs -n "$NAMESPACE" job/"$JOB"; echo "✅ Job succeeded"; exit 0
  elif check_failure; then oc logs -n "$NAMESPACE" job/"$JOB"; echo "❌ Job failed";   exit 1
  fi
  sleep 10
done

oc logs -n "$NAMESPACE" job/"$JOB"
echo "❌ Timed out waiting for the Job to finish"
exit 1
