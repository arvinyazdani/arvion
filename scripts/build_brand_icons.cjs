// Asset compilation only. Uses a development copy of sharp, never a runtime dependency.
const path = require('node:path');
const sharp = require('sharp');
const icons = path.resolve(__dirname, '../core/static/core/icons');
async function build() {
  for (const [name, size] of [['icon-192.png', 192], ['icon-512.png', 512], ['apple-touch-icon.png', 180]]) {
    await sharp(path.join(icons, 'app-icon-maskable.svg'))
      .resize(size, size).removeAlpha().png({compressionLevel: 9}).toFile(path.join(icons, name));
    console.log(`${name}: ${size}x${size}`);
  }
}
build().catch(error => { console.error(error.message); process.exitCode = 1; });
