# Stage 1: Builder
FROM registry.ci.openshift.org/ocp/builder:rhel-9-golang-1.21-openshift-4.16 AS builder

# Stage 2: Final Image
FROM registry.ci.openshift.org/ocp/4.16:cli

# Set environment variables
ENV OPERATOR=/usr/local/bin/ansible-operator \
    USER_UID=1001 \
    USER_NAME=ansible-operator \
    HOME=/opt/ansible

# Ensure system is updated before installation
RUN yum clean all && yum update -y

# Install necessary dependencies
RUN yum install -y \
      glibc-langpack-en \
      git \
      make \
      python3 \
      python3-devel \
      python3-pip \
      python3-setuptools \
      gcc \
      jq  \
  && python3 -m pip install --no-cache-dir --upgrade pip \
  && python3 -m pip install --no-cache-dir ansible \
  && yum clean all \
  && rm -rf /var/cache/yum

# Create user and directories
RUN echo "${USER_NAME}:x:${USER_UID}:0:${USER_NAME} user:${HOME}:/sbin/nologin" >> /etc/passwd \
 && mkdir -p "${HOME}/.ansible/tmp" \
 && chown -R "${USER_UID}:0" "${HOME}" \
 && chmod -R ug+rwX "${HOME}" \
 && mkdir /go \
 && chown -R "${USER_UID}:0" /go \
 && chmod -R ug+rwX /go

# Copy application files (must be separate from RUN)
COPY . /opt/ansible

# Set working directory
WORKDIR /opt/ansible

# Switch to non-root user
USER ${USER_UID}

# Set default entrypoint
CMD ["sh"]
