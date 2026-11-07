# Reelspan for Dify

A [Dify](https://dify.ai) tool plugin for [Reelspan](https://reelspan.com). Let agents, chatflows and workflows publish
videos, photos, text and PDFs to TikTok, YouTube, Instagram, Facebook, X, Threads, LinkedIn, Pinterest, Bluesky,
Reddit and 12 more networks, then check results and read analytics.

## Install

- **Marketplace:** Plugins → Marketplace → search "Reelspan".
- **From a package:** download `reelspan-<version>.difypkg` from
  [Releases](https://github.com/Reelspan/reelspan-dify/releases), then Plugins → Install plugin → Local package file.
- **From GitHub:** Plugins → Install plugin → GitHub → `Reelspan/reelspan-dify`.

Then open the plugin, choose **Authorize**, and paste an API key from the Reelspan dashboard
(**API keys**). It is checked against Reelspan before it is saved.

## Tools

| Tool | |
|---|---|
| Publish text | X, Threads, LinkedIn, Bluesky, Facebook, Mastodon, Discord, Telegram…; long text becomes a thread |
| Publish video | From a file uploaded in Dify or a public URL (Drive and Dropbox links work) |
| Publish photos | One photo or a carousel, from files or URLs, with alt text |
| Publish document | A PDF as a swipeable LinkedIn document |
| Get post status | Each network's result and link |
| Retry failed networks | Resend only what failed |
| List profiles | Profiles and their connected networks |
| Get post history | Recent posts |
| Get analytics | Profile numbers, day-by-day history, or one post |
| List scheduled posts / Cancel scheduled post | The schedule |
| Write captions | A caption for each network (one Reelspan AI credit) |

Publishing tools take a schedule time and timezone, the queue, a first comment, and **Network settings (JSON)** for
any other API field (`{"privacy_level": "PUBLIC_TO_EVERYONE", "reddit_subreddit": "videos"}`; Upload-Post field names
work too). By default they wait until every network has finished and return each result.

## Example: a chatflow that posts what the user uploads

1. Start node with a file input.
2. LLM node writes the caption.
3. Reelspan **Publish video** with `video` = the file, `caption` = the LLM output, `platforms` = `tiktok, youtube, instagram`.
4. Answer node shows the links from the result.

## Develop

```bash
pip install -r requirements.txt pytest pyyaml
pytest -q tests
python scripts/generate_tools.py      # tools/*.yaml and tools/*.py come from one spec
dify-plugin plugin package . -o reelspan.difypkg
```

Privacy: see [PRIVACY.md](PRIVACY.md). MIT licensed. Security reports: see [SECURITY.md](SECURITY.md).
