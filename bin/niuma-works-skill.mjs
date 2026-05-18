#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const packageRoot = path.resolve(__dirname, "..");
const DEFAULT_NAME = "niuma-works-agent";

function usage() {
  console.log(`NIUMA WORKS Skill CLI

Usage:
  npx github:wyalei14-cell/NIUMA-WORKS-SKILL install
  npx niuma-works-agent-skill install

Options:
  --dest <dir>     Skills directory. Defaults to %CODEX_HOME%/skills or ~/.codex/skills
  --name <name>    Installed skill folder name. Defaults to ${DEFAULT_NAME}
  --force          Replace an existing installed skill
  --dry-run        Print the install plan without copying files
  -h, --help       Show this help
`);
}

function parseArgs(argv) {
  const first = argv[2] || "install";
  const args = {
    command: first.startsWith("-") ? "install" : first,
    name: DEFAULT_NAME,
    force: false,
    dryRun: false,
  };
  const start = first.startsWith("-") ? 2 : 3;
  for (let i = start; i < argv.length; i += 1) {
    const item = argv[i];
    if (item === "--dest") args.dest = argv[++i];
    else if (item === "--name") args.name = argv[++i];
    else if (item === "--force") args.force = true;
    else if (item === "--dry-run") args.dryRun = true;
    else if (item === "-h" || item === "--help") args.help = true;
    else throw new Error(`Unknown option: ${item}`);
  }
  return args;
}

function defaultSkillsDir() {
  const codexHome = process.env.CODEX_HOME || path.join(os.homedir(), ".codex");
  return path.join(codexHome, "skills");
}

function shouldSkip(name) {
  return new Set([
    ".git",
    "node_modules",
    "deliverables",
    "review-reports",
    "__pycache__",
    ".niuma-agent-state.json",
    ".niuma-agent.env",
  ]).has(name);
}

function copyRecursive(src, dest) {
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    fs.mkdirSync(dest, { recursive: true });
    for (const entry of fs.readdirSync(src)) {
      if (shouldSkip(entry)) continue;
      copyRecursive(path.join(src, entry), path.join(dest, entry));
    }
    return;
  }
  fs.copyFileSync(src, dest);
}

function assertSkillRoot(root) {
  const skillPath = path.join(root, "SKILL.md");
  if (!fs.existsSync(skillPath)) {
    throw new Error(`SKILL.md not found at package root: ${root}`);
  }
}

function install(args) {
  assertSkillRoot(packageRoot);
  const skillsDir = path.resolve(args.dest || defaultSkillsDir());
  const target = path.join(skillsDir, args.name);
  const plan = { source: packageRoot, skillsDir, target, force: args.force, dryRun: args.dryRun };

  if (args.dryRun) {
    console.log(JSON.stringify({ ok: true, action: "install-plan", ...plan }, null, 2));
    return;
  }

  fs.mkdirSync(skillsDir, { recursive: true });
  if (fs.existsSync(target)) {
    if (!args.force) {
      throw new Error(`Skill already exists: ${target}. Re-run with --force to replace it.`);
    }
    fs.rmSync(target, { recursive: true, force: true });
  }
  copyRecursive(packageRoot, target);
  console.log(`Installed ${args.name} to ${target}`);
  console.log("Restart your agent runtime to pick up the new skill.");
}

try {
  const args = parseArgs(process.argv);
  if (args.help || args.command === "help") {
    usage();
  } else if (args.command === "install") {
    install(args);
  } else {
    throw new Error(`Unknown command: ${args.command}`);
  }
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}
