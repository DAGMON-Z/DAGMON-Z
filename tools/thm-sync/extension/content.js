// Runs on tryhackme.com pages. Every few minutes (only while the tab is in
// front), it reads your public profile stats, the same data your profile page
// shows, and passes them to background.js, which sends them to thm-sync.

const USER = "DAGMON"; // your TryHackMe username
const EVERY = 3 * 60 * 1000; // 3 minutes

async function sync() {
  if (document.visibilityState !== "visible") return;
  // Only one request per few minutes, even with many TryHackMe tabs open
  const allowed = await chrome.runtime.sendMessage({ type: "may-sync" });
  if (!allowed) return;
  try {
    const res = await fetch(`/api/v2/public-profile?username=${encodeURIComponent(USER)}`, {
      credentials: "same-origin",
      headers: { accept: "application/json" },
    });
    if (!res.ok) return;
    const json = await res.json();
    chrome.runtime.sendMessage({ type: "stats", json });
  } catch (e) {
    // offline, or TryHackMe changed something: try again next time
  }
}

sync();
setInterval(sync, EVERY);
document.addEventListener("visibilitychange", sync);
