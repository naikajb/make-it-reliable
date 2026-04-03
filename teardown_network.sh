#!/bin/bash

# remove the namespaces we created
ip netns del ns_client 2>/dev/null
ip netns del ns_server 2>/dev/null

echo "namespaces removed."