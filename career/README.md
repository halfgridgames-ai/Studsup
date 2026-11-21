# Career (World Tour) map art

- `paint.js` paints a stand-in backdrop for each region in code.
- `zone1.webp` … `zone6.webp` are the Midjourney backdrops (1200×800 WebP), listed in `WT_ART` in index.html.


## Trophies

- `trophies/1.webp` … `trophies/6.webp` are the region trophies (Ice Cap … Space Finals), `trophies/champions.webp` the World Champions cup. Midjourney art cut out on a clear background, 520 px tall.
- `WT_CUP` in index.html names each one and picks its win animation (`fx`) and glow colour. `wtCelebrate(z)` plays the trophy lift for region `z` (0–5) or the champions cup (`z = 6`); `tlFx` draws its particles.
- `wallet.cups` remembers every trophy won (bit 6 = champions), so they stay on the map after PLAY AGAIN.
