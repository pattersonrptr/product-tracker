#!/bin/bash
# Example script showing how to call create_superuser.py with parameters
# Useful for automation, CI/CD, or initialization scripts

echo "Creating superusers programmatically..."
echo ""

# Example 1: Create default admin user (skip if exists)
echo "1. Creating 'admin' user..."
python3 src/scripts/create_superuser.py \
    --username admin \
    --email admin@example.com \
    --password admin \
    --skip-if-exists

echo ""

# Example 2: Create another superuser
echo "2. Creating 'developer' user..."
python3 src/scripts/create_superuser.py \
    --username developer \
    --email developer@example.com \
    --password dev123 \
    --skip-if-exists

echo ""

# Example 3: Create with quiet mode (no output)
echo "3. Creating 'tester' user (quiet mode)..."
python3 src/scripts/create_superuser.py \
    --username tester \
    --email tester@example.com \
    --password test123 \
    --skip-if-exists \
    --quiet

echo ""
echo "✓ All users created/checked!"
