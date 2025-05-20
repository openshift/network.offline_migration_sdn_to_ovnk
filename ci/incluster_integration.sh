#!/bin/bash -eu

set -x

NAMESPACE=${NAMESPACE:-default}

if [[ -n "${ANSIBLE_TEST_IMAGE}" ]]; then
  IMAGE="${ANSIBLE_TEST_IMAGE}"
else
  IMAGE="${IMAGE_FORMAT}"
fi

PULL_POLICY=${PULL_POLICY:-IfNotPresent}

if ! oc get namespace "$NAMESPACE"; then
  oc create namespace "$NAMESPACE"
fi

oc project "$NAMESPACE"
oc adm policy add-cluster-role-to-user cluster-admin -z default
oc adm policy who-can create projectrequests

echo "Deleting test job if it exists"
oc delete job ansible-integration-test --wait --ignore-not-found

# Fetch KUBECONFIG from environment
if [[ -z "$KUBECONFIG" ]]; then
    echo "❌ Error: KUBECONFIG environment variable is not set."
    exit 1
fi

# Verify if KUBECONFIG file exists
if [[ ! -f "$KUBECONFIG" ]]; then
    echo "❌ Error: KUBECONFIG file not found at $KUBECONFIG"
    exit 1
fi

echo "✅ Using KUBECONFIG from environment: $KUBECONFIG"

# Secret name
SECRET_NAME="kubeconfig-secret"

# Create Kubernetes secret
oc create secret generic "$SECRET_NAME" --from-file=kubeconfig="$KUBECONFIG" -n "$NAMESPACE" --dry-run=client -o yaml | oc apply -f -

echo "✅ Secret '$SECRET_NAME' created successfully in namespace '$NAMESPACE'"

echo "Creating ansible test job"
cat << EOF | oc create -f -
---
apiVersion: batch/v1
kind: Job
metadata:
  name: ansible-integration-test
spec:
  template:
    spec:
      containers:
        - name: ansible-test-runner
          image: ${IMAGE}
          imagePullPolicy: ${PULL_POLICY}
          command: ["sh", "ci/test-integration.sh"]
          args:
            - |
              export KUBECONFIG=/kubeconfig/kubeconfig
              oc get nodes
          volumeMounts:
            - name: kubeconfig-volume
              mountPath: /kubeconfig
              readOnly: true
          env:
            - name: KUBECONFIG
              value: "/kubeconfig/kubeconfig"
      volumes:
        - name: kubeconfig-volume
          secret:
            secretName: kubeconfig-secret
      restartPolicy: Never
  backoffLimit: 2
  completions: 1
  parallelism: 1
EOF

function check_success {
  oc wait --for=condition=complete job/ansible-integration-test --timeout 5s -n "$NAMESPACE" \
   && oc logs job/ansible-integration-test \
   && echo "Ansible integration tests ran successfully" \
   && return 0
  return 1
}

function check_failure {
  oc wait --for=condition=failed job/ansible-integration-test --timeout 5s -n "$NAMESPACE" \
   && oc logs job/ansible-integration-test \
   && echo "Ansible integration tests failed, see logs for more information..." \
   && return 0
  return 1
}

# Fix `date` command for macOS vs Linux
runtime="180 minutes"
if [[ "$(uname)" == "Darwin" ]]; then
    # macOS (BSD date)
    endtime=$(date -v+30M +%s)
else
    # Linux (GNU date)
    endtime=$(date -ud "$runtime" +%s)
fi

echo "Waiting for test job to complete"
while [[ $(date -u +%s) -le $endtime ]]; do
  if check_success; then
    exit 0
  elif check_failure; then
    exit 1
  fi
  sleep 10
done

oc logs job/ansible-integration-test
exit 1
