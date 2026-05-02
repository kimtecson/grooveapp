#!/bin/bash
# Usage: ./switch-backend.sh [local|ecs|lambda]

LOCAL="http://localhost:5001"
EC2="http://54.175.223.18"
ECS="http://44.204.115.75"
LAMBDA="https://pfysrpnf81.execute-api.us-east-1.amazonaws.com/prod"

FILES="fronend/login.html fronend/register.html fronend/main.html"

case "$1" in
  local)  NEW=$LOCAL  ;;
  ec2)    NEW=$EC2    ;;
  ecs)    NEW=$ECS    ;;
  lambda) NEW=$LAMBDA ;;
  *)
    echo "Usage: ./switch-backend.sh [local|ec2|ecs|lambda]"
    echo "  local  → $LOCAL"
    echo "  ec2    → $EC2"
    echo "  ecs    → $ECS"
    echo "  lambda → $LAMBDA"
    exit 1
    ;;
esac

# Replace whichever URL is currently set with the new one
for OLD in "$LOCAL" "$EC2" "$ECS" "$LAMBDA"; do
  [ "$OLD" = "$NEW" ] && continue
  sed -i '' "s|$OLD|$NEW|g" $FILES
done

echo "Switched to: $NEW"
