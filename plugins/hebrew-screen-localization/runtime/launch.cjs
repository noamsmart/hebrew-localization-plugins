'use strict';
const fs = require('node:fs');
const path = require('node:path');
const {spawn, spawnSync} = require('node:child_process');

function realFile(candidate) {
  try { return !/WindowsApps/i.test(candidate) && fs.statSync(candidate).isFile(); }
  catch { return false; }
}
function compatible(candidate) {
  if (!realFile(candidate)) return false;
  const probe = spawnSync(candidate, ['-c', 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'], {timeout: 4000, windowsHide: true, stdio: 'ignore'});
  return probe.status === 0;
}
function findPython() {
  const configured = process.env.HEBREW_LOCALIZATION_PYTHON;
  if (configured) {
    if (!compatible(configured)) throw new Error('HEBREW_LOCALIZATION_PYTHON must identify an installed Python 3.10+ executable.');
    return configured;
  }
  for (const folder of (process.env.PATH || '').split(path.delimiter)) {
    if (!folder || /WindowsApps/i.test(folder)) continue;
    for (const filename of process.platform === 'win32' ? ['python.exe', 'python3.exe'] : ['python3', 'python']) {
      const candidate = path.join(folder, filename);
      if (compatible(candidate)) return candidate;
    }
  }
  throw new Error('Python 3.10+ is required. Install it locally or set HEBREW_LOCALIZATION_PYTHON to its executable path.');
}
try {
  const child = spawn(findPython(), ['-X', 'utf8', '-u', path.join(__dirname, 'server.py'), ...process.argv.slice(2)], {
    stdio: 'inherit', windowsHide: true,
    env: {...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1', PYTHONUNBUFFERED: '1'}
  });
  child.on('error', error => { process.stderr.write(`Local localization tools: ${error.message}\n`); process.exitCode = 1; });
  child.on('exit', (code, signal) => { process.exitCode = code === null ? 1 : code; });
  for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
} catch (error) {
  process.stderr.write(`Local localization tools: ${error.message}\n`);
  process.exitCode = 1;
}
