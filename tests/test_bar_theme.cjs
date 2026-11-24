const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');
const root = path.resolve(__dirname, '..');
const theme = {};
vm.createContext(theme);
vm.runInContext(fs.readFileSync(path.join(root, 'dist/omarchy/Theme.js'), 'utf8').replace('.pragma library', ''), theme);
for (const name of theme.designs.concat(['system'])) {
    assert.equal(theme.fromConfig(`theme = '${name}' # selected\n`), name);
}
assert.equal(theme.fromConfig('languages = ["French"]'), 'aurora-glass');
assert.equal(theme.fromConfig('# theme = "system"\ntheme = "AURORA-GLASS"'), 'aurora-glass');
for (const input of ['../../secret', 'https://example.com/a.svg', '<img src="x">']) {
    assert.equal(theme.fromConfig(`theme = '${input}'`), 'aurora-glass');
}
assert.equal(theme.plain('<img src="remote"> & broken'), '&lt;img src="remote"&gt; &amp; broken');
for (const name of theme.designs) {
    assert(fs.existsSync(path.join(root, 'dist/omarchy/assets/themes', name + '.svg')));
    assert.equal(fs.statSync(path.join(root, 'assets/themes', name + '.rgba')).size, 128 * 128 * 4);
}
console.log('Bar themes, artwork, config defaults and tooltip escaping: passed');
