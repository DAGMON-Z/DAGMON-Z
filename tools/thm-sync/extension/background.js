// Receives stats from content.js and sends them to thm-sync on this computer.

const GAP = 150 * 1000; // at most one profile request every 2.5 minutes

chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  if (msg.type === "may-sync") {
    chrome.storage.session.get("last").then(({ last = 0 }) => {
      const now = Date.now();
      const ok = now - last >= GAP;
      if (ok) chrome.storage.session.set({ last: now });
      reply(ok);
    });
    return true; // the answer comes later
  }
  if (msg.type === "stats") {
    fetch("http://127.0.0.1:27150/thm", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(msg.json),
    }).catch(() => {}); // thm-sync not running: nothing to do
  }
});
