'use strict';

const fs = require('fs');
const path = require('path');

function usage() {
  console.error('Usage: node render-template.js <templatePath> <outputPath> <jsonMapping>');
  console.error('Example: node render-template.js in.tpl out.json \'{"BUCKET_DOMAIN":"bucket.s3.us-east-1.amazonaws.com"}\'');
  process.exit(1);
}

function replaceAll(haystack, needle, replacement) {
  return haystack.split(needle).join(replacement);
}

const args = process.argv.slice(2);
const templatePath = args[0];
const outputPath = args[1];
const mappingJson = args[2];

if (!templatePath || !outputPath) usage();

let variables = {};
if (mappingJson) {
  try {
    variables = JSON.parse(mappingJson);
  } catch (e) {
    console.error('Failed to parse mapping JSON:', e.message);
    process.exit(1);
  }
}

// Optionally allow env vars to provide values if not provided in mapping JSON
const envKeys = ['BUCKET_DOMAIN','MP_DOMAIN','MP_ORIGIN_PATH','LIVE_FN_ARN','CALLER_REF','BUCKET_NAME'];
for (const k of envKeys) {
  if (variables[k] === undefined && process.env[k]) {
    variables[k] = process.env[k];
  }
}

const template = fs.readFileSync(templatePath, 'utf8');
let rendered = template;
for (const [k, v] of Object.entries(variables)) {
  const token = `__${k}__`;
  rendered = replaceAll(rendered, token, String(v));
}

// Detect unresolved placeholders like __SOMETHING__
const unresolved = [];
const re = /__([A-Z0-9_]+)__/g;
let m;
while ((m = re.exec(rendered)) !== null) {
  unresolved.push(m[0]);
}
if (unresolved.length > 0) {
  console.error('Unresolved placeholders remain:', Array.from(new Set(unresolved)).join(', '));
  process.exit(2);
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, rendered, 'utf8');
console.log('Wrote', outputPath);