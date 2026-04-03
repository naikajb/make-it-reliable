#!/bin/bash

# clean up anything from last time
ip netns del ns_client 2>/dev/null
ip netns del ns_server 2>/dev/null
ip link del veth_server 2>/dev/null

# create two namespaces
ip netns add ns_server
ip netns add ns_client

# virtual cable between the two namespaces
ip link add veth_server type veth peer name veth_client

# put each end in its namespace
ip link set veth_server netns ns_server
ip link set veth_client netns ns_client

# assign IPs
ip netns exec ns_server ip addr add 10.0.0.1/24 dev veth_server
ip netns exec ns_client ip addr add 10.0.0.2/24 dev veth_client

# bring interfaces up
ip netns exec ns_server ip link set veth_server up
ip netns exec ns_client ip link set veth_client up
ip netns exec ns_server ip link set lo up
ip netns exec ns_client ip link set lo up

echo "network ready. server=10.0.0.1  client=10.0.0.2"