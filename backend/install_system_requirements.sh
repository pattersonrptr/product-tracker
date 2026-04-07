#!/bin/bash

apt-get update && apt-get install -y \
  curl \
  gawk \
  wget \
  python3 \
  python3-pip \
  netcat-traditional \
  && apt-get install --fix-missing \
  && rm -rf /var/lib/apt/lists/*
