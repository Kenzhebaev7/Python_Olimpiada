#!/usr/bin/env node
'use strict';

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const mobileRoot = path.resolve(__dirname, '..', '..', 'mobile');
const expoCli = path.join(mobileRoot, 'node_modules', 'expo', 'bin', 'cli');

if (!fs.existsSync(expoCli)) {
  console.error('Expo is not installed in mobile/. Run: npm install --prefix mobile');
  process.exit(1);
}

const args = process.argv.slice(2);
const hasHost = args.some(
  (arg) =>
    arg === '--lan' ||
    arg === '--localhost' ||
    arg === '--tunnel' ||
    arg === '--host' ||
    arg.startsWith('--host='),
);
const forwarded = args[0] === 'start' && !hasHost ? [...args, '--lan'] : args;

const child = spawn(process.execPath, [expoCli, ...forwarded], {
  cwd: mobileRoot,
  stdio: 'inherit',
  env: process.env,
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code == null ? 1 : code);
});
