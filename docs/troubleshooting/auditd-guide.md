# Monitoring File Activities with Linux Auditd

The Linux audit subsystem (`auditd`) is a powerful way to track what happens on your system at the syscall level. Security teams, system administrators, and incident responders often need to know *who created or deleted a file, when it happened, and under which privileges*. This guide shows how to use `auditd` for these purposes with simple, hands-on examples.

---

## 1. What is Auditd?

- **auditd**: the user-space daemon that receives audit events from the kernel and writes them to `/var/log/audit/audit.log`.  
- **auditctl**: tool to configure audit rules dynamically.  
- **ausearch**: tool to search and filter audit logs.  

Together, they let you monitor sensitive paths and understand exactly who is touching files.

---

## 2. Installing and Starting Auditd

On RHEL, CentOS, or Fedora:

```bash
sudo dnf install -y audit
sudo systemctl enable --now auditd
```

Check that it is running:

```bash
sudo systemctl status auditd
```

---

## 3. Adding a Simple Watch Rule

To monitor file creation and deletion under `/tmp`:

```bash
sudo auditctl -w /tmp -p wa -k filewatch
```

Explanation:
- `-w /tmp` → watch the `/tmp` directory  
- `-p wa` → watch for **write** and **attribute changes** (includes create and delete)  
- `-k filewatch` → tag the events with a keyword for easy searching  

---

## 4. Generating Some Activity

Now test it:

```bash
touch /tmp/testfile
rm /tmp/testfile
```

Auditd will capture both the creation and deletion events.

---

## 5. Searching the Logs

Use `ausearch` with your keyword:

```bash
sudo ausearch -k filewatch -i
```

`-i` tells ausearch to convert numeric IDs into readable usernames, group names, and syscall names.

You will see multiple records for the same event, including:

- **SYSCALL** → who performed the action, which system call, whether it succeeded  
- **PATH** → the file path and its owner  
- **CWD** → current working directory of the process  
- **PROCTITLE** → the process command line  

---

## 6. Reading the Key Fields

Let’s break down an example deletion:

```
type=SYSCALL msg=audit(...): syscall=87 success=yes ...
uid=0 euid=0 comm="sisamddaemon" exe="/opt/Symantec/.../sisamddaemon"
type=PATH ... name="/tmp/eicar" nametype=DELETE ouid=1002
```

- `syscall=87` → `unlink()` (delete file)  
- `success=yes` → the deletion succeeded  
- `uid=0 euid=0` → performed with **root privileges**  
- `comm="sisamddaemon"` → process name  
- `exe=...sisamddaemon` → full path to the binary  
- `PATH name="/tmp/eicar" nametype=DELETE` → the file removed  
- `ouid=1002` → the file originally belonged to user with UID 1002  

👉 Interpretation: **The SEP daemon `sisamddaemon` (running as root) deleted the file `/tmp/eicar`, which was originally owned by UID 1002.**

---

## 7. Detecting Failed Attempts

Auditd also records *failed* operations. For example:

```
type=SYSCALL ... syscall=87 success=no exit=-13 comm="rm"
```

- `success=no` → the action failed  
- `exit=-13` → error code `EPERM` (permission denied)  

This way, you not only know when a file was deleted, but also when someone *tried* to delete it and was blocked.

---

## 8. Cleaning Up

When testing, you may want to reset:

```bash
# Remove all rules
sudo auditctl -D

# Rotate or clear the log file
sudo service auditd rotate
sudo truncate -s 0 /var/log/audit/audit.log
```

---

## 9. Summary

- **Add a rule**: `auditctl -w /path -p wa -k mykey`  
- **Trigger actions**: create/delete files  
- **Search logs**: `ausearch -k mykey -i`  
- **Interpret events**: combine `SYSCALL` (who/what) with `PATH` (which file)  
- **Check failures**: look for `success=no` and negative `exit` codes  

Auditd provides fine-grained visibility into file activity. With just a few commands, you can reliably answer the question: *Who deleted this file, and under what authority?*
