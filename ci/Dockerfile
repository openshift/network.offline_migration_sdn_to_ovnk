# Stage 1: Builder
FROM registry.ci.openshift.org/ocp/builder:rhel-9-golang-1.23-openshift-4.19 AS builder

# Stage 2: Final Image
FROM registry.ci.openshift.org/ocp/4.19:cli

# Set environment variables
ENV OPERATOR=/usr/local/bin/ansible-operator \
    USER_UID=1001 \
    USER_NAME=ansible-operator \
    HOME=/opt/ansible

# Ensure system is updated before installation
#RUN yum clean all && yum update -y

RUN dnf -y upgrade --refresh && dnf clean all

# Install necessary dependencies
RUN dnf install -y \
      glibc-langpack-en \
      git \
      make \
      python3.12 \
      python3.12-pip \
      gcc \
      jq  \
  && python3.12 -m pip install --no-cache-dir --upgrade pip \
  && python3.12 -m pip install --no-cache-dir ansible-core==2.18.1 \
  && python3.12 -m pip install --no-cache-dir ansible-lint==25.4.0 \
  && python3.12 -m pip install --no-cache-dir  jmespath \
  #&& dnf clean all \
  && rm -rf /var/cache/dnf

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

RUN chown -R ${USER_UID}:0 /opt/ansible

# Switch to non-root user
USER ${USER_UID}

# Set default entrypoint
CMD ["sh"]
