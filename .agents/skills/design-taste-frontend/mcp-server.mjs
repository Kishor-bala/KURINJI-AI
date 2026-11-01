#!/usr/bin/env node
/**
 * MCP Server for Leonxlnx/taste-skill (design-taste-frontend)
 * Exposes taste-skill tools: taste_draw, taste_show, taste_lint, taste_inspect, taste_assets.
 * Pure Node.js zero-dependency stdio JSON-RPC implementation.
 */

import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { existsSync, readFileSync } from 'node:fs';
import readline from 'node:readline';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const SCRIPTS_DIR = join(__dirname, 'scripts');

const TOOLS = [
  {
    name: 'taste_draw',
    description: 'Deal anti-slop design directions, type system, palette, and section compositions distilled from 247 curated gallery sites.',
    inputSchema: {
      type: 'object',
      properties: {
        sector: {
          type: 'string',
          description: 'Sector: education, editorial, technology, culture, health, commerce, craft, food, portfolio, etc.'
        },
        brief: {
          type: 'string',
          description: 'One-line brief describing the subject and its distinct identity.'
        },
        sections: {
          type: 'string',
          description: 'Comma-separated section roles (e.g. "intro,features,showcase,proof,cta,footer").'
        },
        tone: {
          type: 'string',
          description: 'Optional tone: quiet, bold, warm, technical, playful, luxury, editorial.'
        },
        options: {
          type: 'number',
          description: 'Number of direction options to deal (e.g. 3).'
        },
        direction: {
          type: 'string',
          description: 'Chosen direction ID to finalize and save to .taste-skill/direction.json.'
        },
        app: {
          type: 'boolean',
          description: 'Set to true for app screens (dashboards, learning interfaces, tools).'
        },
        keep: {
          type: 'string',
          description: 'Pass "palette,type" to keep existing brand colors/fonts.'
        }
      },
      required: ['sector', 'brief']
    }
  },
  {
    name: 'taste_show',
    description: 'Show the currently active taste-skill design direction sheet.',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  },
  {
    name: 'taste_lint',
    description: 'Static scan of source code (CSS, JSX, TSX, HTML) for banned AI design slop patterns (gradients, glow, eyebrows, emoji UI, hairline borders, monospace tags, etc.).',
    inputSchema: {
      type: 'object',
      properties: {
        paths: {
          type: 'array',
          items: { type: 'string' },
          description: 'File or directory paths to lint (defaults to project root or current working dir).'
        },
        app: {
          type: 'boolean',
          description: 'Set to true for app screen evaluation mode.'
        },
        json: {
          type: 'boolean',
          description: 'Return output as structured JSON.'
        }
      }
    }
  },
  {
    name: 'taste_inspect',
    description: 'Render the page in a real browser via Chrome DevTools Protocol, measure layout geometry, typography hierarchy, and verify anti-slop house rules.',
    inputSchema: {
      type: 'object',
      properties: {
        url: {
          type: 'string',
          description: 'URL (e.g. http://127.0.0.1:5173/) or path to local HTML file.'
        },
        widths: {
          type: 'string',
          description: 'Comma-separated viewport widths (e.g. "1440,768,390").'
        },
        app: {
          type: 'boolean',
          description: 'Judge against app screen rules.'
        },
        film: {
          type: 'boolean',
          description: 'Capture scroll film frames.'
        }
      },
      required: ['url']
    }
  },
  {
    name: 'taste_assets',
    description: 'Search open collections (Met, Art Institute of Chicago, Wikimedia Commons, Openverse) for authentic archival imagery.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search query for open-access photographs or archival art.'
        },
        source: {
          type: 'string',
          description: 'Sources: all | openverse | commons | aic | met | museums.'
        },
        license: {
          type: 'string',
          description: 'License filter: safe | pd | all | cc0.'
        },
        limit: {
          type: 'number',
          description: 'Maximum number of items to return.'
        }
      },
      required: ['query']
    }
  }
];

function runScript(scriptName, scriptArgs, cwd = process.cwd()) {
  return new Promise((resolveResult) => {
    const scriptPath = join(SCRIPTS_DIR, scriptName);
    const proc = spawn(process.execPath, [scriptPath, ...scriptArgs], {
      cwd,
      env: { ...process.env },
      shell: false
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });

    proc.on('close', (code) => {
      resolveResult({
        exitCode: code,
        stdout: stdout.trim(),
        stderr: stderr.trim()
      });
    });

    proc.on('error', (err) => {
      resolveResult({
        exitCode: -1,
        stdout: '',
        stderr: err.message
      });
    });
  });
}

async function handleToolCall(name, args) {
  try {
    switch (name) {
      case 'taste_draw': {
        const scriptArgs = [];
        if (args.app) scriptArgs.push('--app');
        if (args.sector) scriptArgs.push('--sector', args.sector);
        if (args.brief) scriptArgs.push('--brief', args.brief);
        if (args.sections) scriptArgs.push('--sections', args.sections);
        if (args.tone) scriptArgs.push('--tone', args.tone);
        if (args.options) scriptArgs.push('--options', String(args.options));
        if (args.direction) scriptArgs.push('--direction', args.direction);
        if (args.keep) scriptArgs.push('--keep', args.keep);

        const res = await runScript('draw.mjs', scriptArgs);
        const text = res.stdout || res.stderr || (res.exitCode === 0 ? 'Success' : `Failed with exit code ${res.exitCode}`);
        return {
          content: [{ type: 'text', text }]
        };
      }

      case 'taste_show': {
        const res = await runScript('draw.mjs', ['--show']);
        const text = res.stdout || res.stderr || 'No active direction found in .taste-skill/direction.json';
        return {
          content: [{ type: 'text', text }]
        };
      }

      case 'taste_lint': {
        const scriptArgs = [];
        if (args.app) scriptArgs.push('--app');
        if (args.json) scriptArgs.push('--json');
        if (Array.isArray(args.paths) && args.paths.length > 0) {
          scriptArgs.push(...args.paths);
        } else {
          scriptArgs.push('.');
        }

        const res = await runScript('lint.mjs', scriptArgs);
        let text = res.stdout;
        if (res.stderr) text = (text ? text + '\n' : '') + res.stderr;
        if (!text) text = res.exitCode === 0 ? 'Lint passed with 0 errors.' : `Lint exited with code ${res.exitCode}`;

        return {
          content: [{ type: 'text', text }]
        };
      }

      case 'taste_inspect': {
        const scriptArgs = [args.url];
        if (args.widths) scriptArgs.push('--widths', args.widths);
        if (args.app) scriptArgs.push('--app');
        if (args.film) scriptArgs.push('--film');

        const res = await runScript('inspect.mjs', scriptArgs);
        let text = res.stdout;
        if (res.stderr) text = (text ? text + '\n' : '') + res.stderr;
        if (!text) text = `Inspect finished with exit code ${res.exitCode}`;

        return {
          content: [{ type: 'text', text }]
        };
      }

      case 'taste_assets': {
        const scriptArgs = [args.query];
        if (args.source) scriptArgs.push('--source', args.source);
        if (args.license) scriptArgs.push('--license', args.license);
        if (args.limit) scriptArgs.push('--limit', String(args.limit));

        const res = await runScript('assets.mjs', scriptArgs);
        let text = res.stdout;
        if (res.stderr) text = (text ? text + '\n' : '') + res.stderr;
        if (!text) text = `No assets found for query: ${args.query}`;

        return {
          content: [{ type: 'text', text }]
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (err) {
    return {
      isError: true,
      content: [{ type: 'text', text: `Error executing ${name}: ${err.message}` }]
    };
  }
}

function sendResponse(id, result, error = null) {
  const msg = {
    jsonrpc: '2.0',
    id
  };
  if (error) {
    msg.error = error;
  } else {
    msg.result = result;
  }
  process.stdout.write(JSON.stringify(msg) + '\n');
}

// Stdio JSON-RPC line processor
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on('line', async (line) => {
  const trimmed = line.trim();
  if (!trimmed) return;

  let request;
  try {
    request = JSON.parse(trimmed);
  } catch (e) {
    process.stderr.write(`Invalid JSON received: ${trimmed}\n`);
    return;
  }

  const { id, method, params } = request;

  // Notification (no id)
  if (id === undefined || id === null) {
    if (method === 'notifications/initialized') {
      // client initialized confirmation
    }
    return;
  }

  switch (method) {
    case 'initialize': {
      sendResponse(id, {
        protocolVersion: '2024-11-05',
        capabilities: {
          tools: {}
        },
        serverInfo: {
          name: 'taste-skill-mcp',
          version: '2.0.0'
        }
      });
      break;
    }

    case 'tools/list': {
      sendResponse(id, {
        tools: TOOLS
      });
      break;
    }

    case 'tools/call': {
      if (!params || !params.name) {
        sendResponse(id, null, { code: -32602, message: 'Missing tool name in params' });
        break;
      }
      const result = await handleToolCall(params.name, params.arguments || {});
      sendResponse(id, result);
      break;
    }

    case 'ping': {
      sendResponse(id, {});
      break;
    }

    default: {
      sendResponse(id, null, { code: -32601, message: `Method not found: ${method}` });
      break;
    }
  }
});

process.stderr.write('Taste Skill MCP Server running on stdio...\n');
