// Rebuild couchpotato/static/scripts/combined.*.min.js from their sources.
//
// Byte-for-byte the same output as the old Gruntfile's uglify task (mangle off, compress off,
// beautify on, files in the Gruntfile's order), without Grunt 0.4 or Ruby/Compass.
//
//   cd tools/jsbuild && npm ci && node build.js            # rewrite the bundles
//   node build.js --check                                  # exit 1 if a bundle is out of date
const fs = require('fs'), path = require('path'), UglifyJS = require('uglify-js');

const root = path.resolve(__dirname, '..', '..');
const check = process.argv.includes('--check');
const scripts = path.join(root, 'couchpotato/static/scripts');

const gruntfile = fs.readFileSync(path.join(root, 'Gruntfile.js'), 'utf8');
const list = name => gruntfile.split('var ' + name + ' = [')[1].split('];')[0]
  .match(/'([^']+)'/g).map(s => path.join(root, s.slice(1, -1)));

function walk(dir, out) {
  for (const f of fs.readdirSync(dir).sort()) {
    const p = path.join(dir, f);
    if (fs.statSync(p).isDirectory()) walk(p, out);
    else if (p.endsWith('.js')) out.push(p);
  }
  return out;
}

const bundles = {
  'combined.vendor.min.js': list('vendor_scripts_files'),
  'combined.base.min.js': list('scripts_files'),
  'combined.plugins.min.js': walk(path.join(root, 'couchpotato/core'), []),
};

let stale = 0;
for (const [name, files] of Object.entries(bundles)) {
  const code = UglifyJS.minify(files, {
    mangle: false, compress: false, output: { beautify: true, screw_ie8: true }, screw_ie8: true,
  }).code + '\n';
  const dest = path.join(scripts, name);
  if (check) {
    if (fs.readFileSync(dest, 'utf8') !== code) {
      console.error(name + ' is out of date: run `node tools/jsbuild/build.js` and commit it');
      stale++;
    }
  } else {
    fs.writeFileSync(dest, code);
    console.log('wrote ' + name + ' (' + files.length + ' files)');
  }
}
process.exit(stale ? 1 : 0);
