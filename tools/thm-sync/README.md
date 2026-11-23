# thm-sync: live TryHackMe stats on the profile

TryHackMe's old badge image stopped updating in 2024, and its profile data is
behind a bot checkpoint that only lets real browsers in. So the stats come from
my own browser, while I'm on TryHackMe:

```text
tryhackme.com tab in Brave
  └─ extension/  reads my public profile stats every few minutes
       └─ thm-sync  (this computer, 127.0.0.1:27150) saves them to data/thm.json, pushes
            └─ GitHub Actions rebuilds the profile (data/** changed) → new badge in ~1 minute
```

- The extension runs only on tryhackme.com, only while a TryHackMe tab is in
  front, and makes at most one request every 2.5 minutes: the same request the
  profile page itself makes.
- `thm-sync` accepts stats only from a browser extension (not from websites),
  only for the username in `data/thm.json`, and keeps only the numbers it shows.
  It pushes only when something changed.

## Setup

1. Start the helper, now and at every login:

   ```bash
   systemctl --user enable --now ~/src/DAGMON-Z/tools/thm-sync/thm-sync.service
   ```

2. Load the extension in Brave: open `brave://extensions`, turn on
   **Developer mode** (top right), click **Load unpacked** and choose
   `~/src/DAGMON-Z/tools/thm-sync/extension`.
3. Open tryhackme.com. Within a few seconds the stats are pushed.

## Check

```bash
systemctl --user status thm-sync     # is it running?
journalctl --user -u thm-sync -n 20  # "pushed: 14 rooms, rank ..." lines
```
