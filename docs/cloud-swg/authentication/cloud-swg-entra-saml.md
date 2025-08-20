# Integrating Symantec Cloud SWG with Azure Entra ID (SAML SSO)

## Introduction

Symantec Cloud SWG (formerly Web Security Service, WSS) provides cloud-based secure web gateway functionality, enforcing traffic inspection and access policies.  
Azure Entra ID (formerly Azure Active Directory) is Microsoft’s identity platform that supports SAML 2.0.  

By integrating Cloud SWG with Entra ID, organizations can enable **Single Sign-On (SSO)** for secure web access, centralize identity management, and improve user experience.  

---

## Prerequisites

Before starting, make sure you have:  

- Admin access to **Azure Entra ID**  
- Admin access to the **Cloud SWG portal**  
- A **custom domain that you own and can manage** (e.g., `yourdomain.com`)  
- Explicit Proxy/VPN or agent connectivity to Cloud SWG (not covered in this tutorial)  

---

## Verify a Custom Domain

If you want users to log in with `user@yourdomain.com`, you must verify your domain in Entra ID:  

- Go to **Azure Portal → Entra ID → Custom domain names**  
- Select **+ Add custom domain**  
- Enter your domain, e.g., `lihaifeng.net`  
- Copy the **TXT record(or MX)** provided by Microsoft and add it to your DNS provider 

![image-20250820101407813](.\assets\image-20250820101407813.png) 

- Once DNS propagation is complete, return to the portal and select **Verify**  
- After verification, the domain will be available for user UPNs  

> ⚠️ Without domain verification, Entra ID accounts can only use the `onmicrosoft.com` suffix.  

---

## Azure Entra ID Configuration

- Sign in to Azure Portal → **Entra ID → Enterprise applications**  
- Select **New application → Create application**  
  - Search for **Symantec Web Security Service (WSS)**  
  - Create the application  

![image-20250820100638773](.\assets\image-20250820100638773.png)

- In the application page → **Single sign-on** → choose **SAML**  

![image-20250820100846702](.\assets\image-20250820100846702.png)

- Configure the basic parameters:  
  - **Identifier (Entity ID):** `https://saml.threatpulse.net:8443/saml/saml_realm`  
  - **Reply URL (ACS URL):** `https://saml.threatpulse.net:8443/saml/saml_realm/bcsamlpost`  

![image-20250820100923698](.\assets\image-20250820100923698.png)

- Under **SAML Certificates**, download the **Federation Metadata XML** for later use  

![image-20250820101025355](.\assets\image-20250820101025355.png)

---

## User and Group Assignment

- In Entra ID → **Groups**, create a new group  
  - Ensure the **Group type** is set to **Security**  

![image-20250820101241918](.\assets\image-20250820101241918.png)

- Go to the **Users** tab → create a new user  
  - Choose the verified domain as the UPN suffix  

  ![image-20250820100457930](.\assets\image-20250820100457930.png)

  - Assign the user to the group created earlier  

  ![image-20250820100527610](.\assets\image-20250820100527610.png)
- In the application **Symantec Web Security Service (WSS) → Users and groups**  
  - Select **+ Add user/group**  
  - Add the created user  
  - Alternatively, assign the security group so that all members gain access (requires a higher plan level)  

  ![image-20250820101131431](.\assets\image-20250820101131431.png)
- For testing purposes, disable two-step verification:  
  - Entra ID → **Properties → Manage security defaults**  
  - Set to **No** and save  

![image-20250820101942591](.\assets\image-20250820101942591.png)

---

## Configure Cloud SWG with Entra ID as IdP

- Log in to the Cloud SWG portal → **Locations** → create a location  

  ![image-20250820095007467](.\assets\image-20250820095007467.png)

  > (This guide focuses on authentication; VPN configuration steps are omitted. Once VPN connectivity is established, the status should show as connected.)  

  ![image-20250820095041295](.\assets\image-20250820095041295.png)

- In the Cloud SWG portal → **Identity → SAML and SCIM Authentication**  

- Upload the **Federation Metadata XML** downloaded from Entra ID  
  - The certificate and related settings will be configured automatically  
  
  ![image-20250820095154442](.\assets\image-20250820095154442.png)
  
- Save the configuration  

- If necessary, configure SSL Intercept and upload certificates, or define other policies (not covered in this guide)  

---

## Adjust Authentication Policies

- Ensure Azure AD endpoints are bypassed from authentication to avoid SSO loops:  
  
  <pre>
   `login.microsoftonline.com`
   `secure.aadcdn.microsoftonline-p.com`
   `aadcdn.msauth.net`
   `*.msauth.net`
   `*.msauthimages.net`
   `*.microsoftonline.com`
   `*.azureedge.net`
   `sts.windows.net`
  </pre>
  
  ![image-20250820095533861](.\assets\image-20250820095533861.png)
  
  ![image-20250820095736830](.\assets\image-20250820095736830.png)
  
- In **Authentication policy**, create an authentication rule:  
  
  - Apply to your test location  
  - Require **SAML authentication**  
  - For testing, you can use **cookie-based sessions**  
  
  ![image-20250820095804724](.\assets\image-20250820095804724.png)

---

## Test the Integration

- Connect your client through Cloud SWG (via agent, PAC, or VPN)  
- Open a browser and attempt to access an external website  
- You should be redirected to the Microsoft login page  
- Sign in with your Entra ID account (`user@yourdomain.com`)  

![image-20250820101536934](.\assets\image-20250820101536934.png)

- After successful authentication, access should be granted through Cloud SWG  
- In the **Cloud SWG portal → Reports**, confirm that events are logged  

![image-20250820101626150](.\assets\image-20250820101626150.png)

---

## Conclusion

By integrating Symantec Cloud SWG with Azure Entra ID using SAML, you can centralize identity management, enforce authentication consistently, and improve the end-user experience.  

---

