# Connecting pfSense with Symantec Cloud SWG using DDNS and IPsec IKEv2

For organizations requiring flexible and secure network connectivity, seamlessly integrating on-premises networks with cloud services is crucial. This article provides a detailed guide on how to establish a reliable VPN connection between your pfSense firewall and Symantec Cloud Security Gateway (SWG) using Dynamic DNS (DDNS) and the IPsec IKEv2 protocol.

------

## Why Choose DDNS?

**Dynamic DNS (DDNS)**: DDNS is an ideal solution for users without a fixed public IP address. It allows your pfSense firewall to automatically update its domain name resolution when its IP address changes, ensuring continuous VPN connectivity.

------

## Before You Start: DDNS Configuration

I’ve already established my DDNS setup, using a custom method like the one detailed in **[Keep Your Dynamic IP Online: NameSilo DDNS Auto-Update Guide](https://lihaifeng.net/?p=1473)**. This means my chosen DDNS service (such as Namesilo) is already actively keeping my domain name updated with my pfSense’s public IP.

For this guide, we’ll focus on the IPsec configuration. pfSense provides a convenient, built-in Dynamic DNS client that supports many popular services (such as DynDNS or No-IP). This integrated approach offers simplicity, tight integration, and robust WAN IP change detection directly on your firewall. However, pfSense is also quite flexible and allows for custom DDNS providers, enabling compatibility with services that require specific API calls or scripting. If your DDNS service is one that pfSense natively supports, **I highly recommend** leveraging its built-in functionality.

## Prerequisites

Before you begin the configuration, ensure you have the following information:

- **pfSense Installation**: If you haven’t already installed pfSense, you can refer to this guide: [**Installing pfSense on ESXi**](https://lihaifeng.net/?p=1365)
- **pfSense Public IP Address**: This is the public IP address of your pfSense firewall’s WAN interface.
- **Symantec Cloud SWG Data Center IP Address**: You’ll need to choose Symantec Cloud SWG data center IP addresse closest to you to act as tunnel destination. Symantec Cloud SWG provides a list of Ingress IP addresses. You can reference the official documentation for these addresses here: [**Cloud SWG (formerly WSS) Ingress and Egress IP addresses**](https://knowledge.broadcom.com/external/article?legacyId=TECH242979)
- **Functional DDNS Setup**: My chosen DDNS service is actively updating my chosen hostname (e.g., `mypfsenseddns.mydomain.com`) with my pfSense WAN’s public IP address.

------

## Symantec Cloud SWG Portal Configuration

1. Add Location
    - Log in to the Symantec Cloud SWG administration portal.
    - Navigate to **Connectivity > Locations**.
    - Click **Add Location**.
    - **Name**: Give your location a descriptive name, such as “Office Name VPN”.
    - **Access Method**: Select **FQDN IKEv2 Firewall**.
    - **FQDN Address**: Enter your DDNS domain name.
    - **Authentication Key**: Enter your **Pre-Shared Key (PSK)**. This key will be used to authenticate communication between the SWG and firewall.
    - **Estimated Users**: Select the range of users sending web requests through this gateway interface.
    - **Timezone**: Select the time zone.
    - Click **Save**.
2. **(Optional) Configure Dual Tunnels for Failover**: Symantec recommends configuring two tunnels (primary and secondary) to ensure high availability. You’ll need to repeat the above steps for a second Symantec Cloud SWG data center IP address to create another Location.

![img](./assets/pfsense_ipsec_ddns_swg_location.jpg)

------

## pfSense IPsec Configuration

Based on the pfSense configuration snippet, here are the detailed steps:

In the pfSense web interface, navigate to **VPN > IPsec > Tunnels**.

### Phase 1 Configuration (IKE)

Click **Add P1** or edit an existing Phase 1 entry.

- IKE Endpoint Configuration
    - Key Exchange Version: IKEv2 
    - Internet Protocol: IPv4
    - Interface: WAN(or your internet-facing interface)
    - **Remote gateway**: Your Symantec Cloud SWG data center IP address.

![img](./assets/pfsense_ipsec_ddns_swg_phase1_ike_endpoint_configuration-1024x291.jpg)

- Phase 1 Proposal (Authentication)
    - Authentication Method: Mutual PSK(Pre-Shared Key)
    - My identifie: Fully qualified domain name or Dynamic DNS (your DDNS domain name).
    - Peer identifier: IP address(Your Symantec Cloud SWG data center IP).
    - Pre-Shared Key: Your secure password(must match the Authentication Key configured in the Symantec Cloud SWG Portal).

![img](./assets/pfsense_ipsec_ddns_swg_phase1_proposal_auth-1024x271.jpg)

- Phase 1 Proposal (Algorithms)
    - Encryption Algorithm: AES 256 bits
    - Hash Algorithm: SHA256
    - DH Group: 14 (2048 bit)

![img](./assets/pfsense_ipsec_ddns_swg_phase1_proposal_encryption-1024x177.jpg)

Click **Save** to apply the Phase 1 configuration.

### Phase 2 Configuration (IPsec)

Under the Phase 1 configuration page, click **Show Phase 2 Entries**, then click **Add P2**. Ensure the new Phase 2 entry is associated with the Phase 1 you just created.

- General Information
    - Mode: Tunnel IPv4

![img](./assets/pfsense_ipsec_phase2_general-1024x250-1755670552734-5.jpg)

- Networks

    - Local Network: LAN subnet

        (or the specific internal network subnet whose traffic you want to send through the tunnel).

    - Remote Network: 0.0.0.0/0

         (This means all traffic will be sent through the tunnel to Cloud SWG, which is typical for web proxy routing).

![img](./assets/pfsense_ipsec_phase2_networks-1024x287-1755670552734-7.jpg)

- Phase 2 Proposal (Algorithms)
    - Protocol: ESP
    - Encryption Algorithms: AES256-GCM 128 bits
    - Hash Algorithms: Blank
    - PFS Key Group: 14 (2048 bit)

![img](./assets/pfsense_ipsec_ddns_swg_phase2_proposal_algorithms-1024x412.jpg)

Click **Save** to apply the Phase 2 configuration.

------

## Firewall Rule Configuration (pfSense)

After configuring the IPsec tunnel, you’ll need to add appropriate firewall rules on pfSense to allow traffic through the IPsec tunnel.

1. Navigate to Firewall > Rules > LAN

    - Add Rule

        : This rule allows your LAN traffic to exit the LAN interface and be routed.

        - Action: Pass

        - Interface: LAN

        - Address Family: IPv4

        - Protocol: any

        - Source: LAN subnet

             (or the specific IP address/subnet of your internal network).

        - Destination: any

        - Description: Allow all LAN outbound traffic

        - Click **Save**, then **Apply Changes**.

2. Navigate to Firewall > Rules > IPsec

    - Add Rule: This rule allows traffic that has been routed into the IPsec tunnel to pass through.

        - Action: Pass

        - Interface: IPsec

        - Address Family: IPv4

        - Protocol: any

            (or restrict to TCP with destination ports 80, 443 if preferred).

        - Source: LAN subnet

            (or the specific IP address/subnet from your local network).

        - Destination: any

            (since all web traffic will be routed through SWG).

        - Description: Allow LAN to Cloud SWG through IPsec tunnel

        - Click **Save**, then **Apply Changes**.

------

## Verifying the Connection

Once configured, you can verify the IPsec connection using the following methods:

- **pfSense**: Navigate to **Status > IPsec**. Check the connection status of both Phase 1 and Phase 2 tunnels. If configured correctly, they should show as **connected**.
- Client Test: From a device on your internal network, try accessing an external website. Then, check your Symantec Cloud SWG reports to confirm that the traffic is being proxied and filtered through SWG.
    - **Important:** For your client devices on the LAN to send traffic through pfSense and the IPsec tunnel, **ensure pfSense is configured as their default gateway.** This is typically done via your DHCP server settings on pfSense (Services > DHCP Server > LAN) or manually on static IP clients.

![img](./assets/pfsense_ipsec_ddns_swg_phase2_ipsec_connected-1024x409.jpg)

------

## Troubleshooting Tips

- **Check Logs**: pfSense system logs (**Status > System Logs > IPsec**) are an invaluable tool for troubleshooting IPsec connection issues.
- **Confirm IP Addresses and PSK**: Ensure that the **IP addresses** and **Pre-Shared Key** are an exact match on both pfSense and Symantec Cloud SWG.
- **Firewall Rules**: Carefully review all relevant firewall rules to ensure none are blocking IPsec traffic. Both the **LAN** and **IPsec** interface rules are critical.
- **Algorithm Compatibility**: Ensure that the **encryption, hashing, and DH group algorithms** configured on pfSense for both Phase 1 and Phase 2 are **supported by Symantec Cloud SWG**.
- **DNS Resolution:** From any device capable of performing a DNS lookup (e.g., your computer’s command prompt, or a public DNS lookup tool online), try to `ping` or perform a DNS lookup for your DDNS hostname (e.g., `yourpfsenseddns.yourdomain.com`). Ensure it resolves to the **current public IP address** of your pfSense WAN interface. If it resolves to an old IP or doesn’t resolve at all, your DDNS update mechanism is likely failing, preventing pfSense from identifying itself correctly to the SWG.

By following these steps, you should be able to successfully establish an IPsec VPN tunnel between your pfSense firewall and Symantec Cloud SWG, enabling secure web traffic management. If you encounter any issues, remember to systematically check each configuration step and consult the logs.