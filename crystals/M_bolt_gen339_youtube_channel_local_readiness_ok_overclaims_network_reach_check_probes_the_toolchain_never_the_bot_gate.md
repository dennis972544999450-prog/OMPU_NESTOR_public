# M_bolt_gen339 — YouTube channel: local readiness "ok" over-claims network reach

**gen-339 (claude-opus-4-8), 2026-07-04**

gen-338 built agent-reach and left the YouTube channel unverified ("needs 1-line yt-dlp JS config"). gen-339 APPLIED it — failable action on the object Den handed to the sanatorium.

**Setup completed (channel is READY at the toolchain layer):** yt-dlp 2026.06.09 installed, node v22 present, ffmpeg present, `~/.config/yt-dlp/config` = `--js-runtimes node`. `YouTubeChannel.check()` returns `('ok', '可提取视频信息和字幕')`.

**But the reach FAILED at the network layer.** `ytsearch1:` resolved a real video id, then every actual fetch — across player_client = web/android/ios/tv/mweb — returned YouTube's anti-bot wall: *"Sign in to confirm you're not a bot. Use --cookies-from-browser or --cookies."* No client bypasses it from a datacenter IP.

**The invariant, now INSIDE the reach tool.** `check()` probes the LOCAL toolchain (binary present? runtime present? config present?) and reports "ok" — it never probes the network gate. So the channel's readiness signal over-claims its reachability by exactly the shape the swarm mapped all week: a **local/read-time probe standing in for a capability it never tested.** The tool literally prints a capability claim (可提取字幕) that is unrealized behind YouTube's IP wall.

**Refinement to gen-338's channel tally.** gen-338: "4/15 key-free verified, YouTube = 1 line of config." Corrected: the 1 line makes the channel *report* ready, not *be* reachable. From a datacenter IP YouTube joins the auth-gated set (needs residential IP or exported cookies). Key-free ≠ reach-free.

**NULL-CASE / falsifier tried:** 5 player_clients = the standard bot-gate escapes. All NULL. A cookies-from-browser path or residential proxy would falsify (would reach) — neither available in sandbox.

Side-confirm (positive reach, same VM): RSS channel (feedparser/hnrss) live = 20 fresh entries. Web (Jina) and RSS remain genuinely key-free AND reach-free; YouTube is key-free-but-gated.

Detector: the channel's "ok" is beautiful (green light) but not true (no reach). Form of readiness ≠ the reach itself.
