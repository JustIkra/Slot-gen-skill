#!/usr/bin/env bun
/**
 * generate-image — OpenRouter image generator.
 *
 * Shared backend for the slot-gen skill (art flow and Spine flow).
 *
 * Usage:
 *   bun run generate-image.ts --prompt "..." [--size 2K] [--aspect-ratio 1:1]
 *                             [--reference-image path ...]
 *                             [--output /path/out.png]
 *
 *   --reference-image is repeatable: pass it multiple times to send several
 *   reference images in one request (e.g. a style ref + a character ref + a
 *   logo). All are attached as image_url parts after the text prompt.
 *
 * Env (loaded from ~/.codex/.env if not already in shell):
 *   OPENROUTER_KEY     required
 */

import { readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { extname, resolve } from "node:path";

type Model = "nano-banana-2" | "nano-banana-pro";
type AspectRatio =
  | "1:1" | "1:4" | "1:8" | "2:3" | "3:2" | "3:4"
  | "4:1" | "4:3" | "4:5" | "5:4" | "8:1"
  | "9:16" | "16:9" | "21:9";
type Size = "1K" | "2K" | "4K";
type ReasoningEffort = "minimal" | "low" | "medium" | "high" | "xhigh" | "none";
type ProviderTag = "google-vertex/global" | "google-ai-studio";

interface Args {
  model: Model;
  prompt: string;
  size: Size;
  aspectRatio: AspectRatio;
  output: string;
  referenceImages?: string[];
  transparent?: boolean;
  variations?: number;
  reasoning?: ReasoningEffort;
  reasoningIncludeTrace?: boolean;
  provider?: ProviderTag;
}

const DEFAULTS = {
  model: "nano-banana-2" as Model,
  size: "2K" as Size,
  aspectRatio: "1:1" as AspectRatio,
  output: "/tmp/slot-gen-image.png",
};

const SIZES: Size[] = ["1K", "2K", "4K"];
const ASPECTS: AspectRatio[] = [
  "1:1", "1:4", "1:8", "2:3", "3:2", "3:4",
  "4:1", "4:3", "4:5", "5:4", "8:1",
  "9:16", "16:9", "21:9",
];
const REASONING_EFFORTS: ReasoningEffort[] = [
  "minimal", "low", "medium", "high", "xhigh", "none",
];
const PROVIDER_TAGS: ProviderTag[] = ["google-vertex/global", "google-ai-studio"];

// The Pro image model (gemini-3-pro-image) rejects the extreme "strip"
// aspect ratios — observed live: 4:1 and 8:1 return HTTP 400
// "aspect_ratio not supported ... Only google/gemini-3.1-flash-image".
// Use nano-banana-2 for these. Listed so we fail fast with a clear message
// instead of a confusing 400 (or, in --creative-variations, a partial run).
const PRO_UNSUPPORTED_ASPECTS: AspectRatio[] = ["1:4", "4:1", "1:8", "8:1"];

// GA stable image models (newer snapshot, best quality). NOTE: the GA aliases
// max out at 2K — 4K is only available on the older -preview snapshots
// (observed live: HTTP 400 "image_size '4K' is not supported ... Only
// ...-preview... support 4K"). Use --size 2K with these; switch to the
// -preview aliases only if you specifically need 4K.
const OPENROUTER_MODELS: Record<Model, string> = {
  "nano-banana-2": "google/gemini-3.1-flash-image",
  "nano-banana-pro": "google/gemini-3-pro-image",
};

const OPENROUTER_SIZE_MAP: Record<Size, string> = {
  "1K": "1K",
  "2K": "2K",
  "4K": "4K",
};

class CLIError extends Error {}

async function loadEnv(): Promise<void> {
  const envPath = resolve(process.env.HOME ?? "", ".codex/.env");
  if (!existsSync(envPath)) return;
  const text = await readFile(envPath, "utf8");
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const eq = line.indexOf("=");
    if (eq === -1) continue;
    const key = line.slice(0, eq).trim();
    let value = line.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (!process.env[key]) process.env[key] = value;
  }
}

function showHelp(): never {
  console.log(`
generate-image — OpenRouter image generator (slot-gen skill)

USAGE:
  bun run generate-image.ts --prompt "<text>" [OPTIONS]

REQUIRED:
  --prompt <text>          Image generation prompt

OPTIONS:
  --model <model>          nano-banana-2 (default) | nano-banana-pro
  --size <size>            1K | 2K (default) | 4K
  --aspect-ratio <ratio>   ${ASPECTS.join(" | ")}    (default 1:1)
  --output <path>          Output PNG path (default ${DEFAULTS.output})
  --reference-image <path> Optional reference image (.png .jpg .jpeg .webp).
                           Repeatable — pass multiple times to attach several
                           reference images in a single request.
  --transparent            Prepend transparent-background hint to the prompt
  --reasoning <effort>     Gemini thinking via OpenRouter: ${REASONING_EFFORTS.join(" | ")}
                           (default off; adds reasoning_tokens billing)
  --reasoning-trace        Surface reasoning text in console (default excluded)
  --provider <tag>         Force OpenRouter provider: ${PROVIDER_TAGS.join(" | ")}
  --creative-variations <n>  Generate N variations (-v1, -v2, ...)
  --help                   Show this help

ENV:
  OPENROUTER_KEY           required
`);
  process.exit(0);
}

function parseArgs(argv: string[]): Args {
  const a = argv.slice(2);
  if (a.length === 0 || a.includes("--help") || a.includes("-h")) showHelp();

  const out: Partial<Args> = {
    model: DEFAULTS.model,
    size: DEFAULTS.size,
    aspectRatio: DEFAULTS.aspectRatio,
    output: DEFAULTS.output,
  };

  for (let i = 0; i < a.length; i++) {
    const flag = a[i];
    if (!flag.startsWith("--")) throw new CLIError(`Invalid flag: ${flag}`);
    const key = flag.slice(2);

    if (key === "transparent")      { out.transparent = true; continue; }
    if (key === "reasoning-trace")  { out.reasoningIncludeTrace = true; continue; }

    const value = a[i + 1];
    if (value === undefined || value.startsWith("--")) {
      throw new CLIError(`Missing value for ${flag}`);
    }
    switch (key) {
      case "model":
        if (value !== "nano-banana-2" && value !== "nano-banana-pro") {
          throw new CLIError(`--model must be nano-banana-2 or nano-banana-pro`);
        }
        out.model = value;
        break;
      case "prompt":           out.prompt = value; break;
      case "size":
        if (!SIZES.includes(value as Size)) {
          throw new CLIError(`--size must be one of ${SIZES.join(",")}`);
        }
        out.size = value as Size;
        break;
      case "aspect-ratio":
        if (!ASPECTS.includes(value as AspectRatio)) {
          throw new CLIError(`--aspect-ratio must be one of ${ASPECTS.join(",")}`);
        }
        out.aspectRatio = value as AspectRatio;
        break;
      case "output":           out.output = value; break;
      case "reference-image":
        (out.referenceImages ??= []).push(value);
        break;
      case "creative-variations": {
        const n = parseInt(value, 10);
        if (Number.isNaN(n) || n < 1 || n > 10) {
          throw new CLIError(`--creative-variations must be 1..10`);
        }
        out.variations = n;
        break;
      }
      case "reasoning":
        if (!REASONING_EFFORTS.includes(value as ReasoningEffort)) {
          throw new CLIError(`--reasoning must be one of ${REASONING_EFFORTS.join(",")}`);
        }
        out.reasoning = value as ReasoningEffort;
        break;
      case "provider":
        if (!PROVIDER_TAGS.includes(value as ProviderTag)) {
          throw new CLIError(`--provider must be one of ${PROVIDER_TAGS.join(",")}`);
        }
        out.provider = value as ProviderTag;
        break;
      default: throw new CLIError(`Unknown flag: ${flag}`);
    }
    i++;
  }

  if (!out.prompt) throw new CLIError("Missing --prompt");

  if (out.model === "nano-banana-pro" &&
      PRO_UNSUPPORTED_ASPECTS.includes(out.aspectRatio as AspectRatio)) {
    throw new CLIError(
      `nano-banana-pro does not support aspect ratio ${out.aspectRatio} ` +
      `(extreme strips ${PRO_UNSUPPORTED_ASPECTS.join("/")} are flash-only). ` +
      `Use --model nano-banana-2 for this aspect.`,
    );
  }

  return out as Args;
}

const TRANSPARENT_PREFIX =
  "CRITICAL: Transparent background (PNG with alpha channel) — NO background " +
  "color, pure transparency. Subject floating in transparent space. ";

async function loadReference(p: string): Promise<{ mimeType: string; data: string }> {
  const buf = await readFile(p);
  const ext = extname(p).toLowerCase();
  const mimeType =
    ext === ".png"  ? "image/png"  :
    ext === ".webp" ? "image/webp" :
    (ext === ".jpg" || ext === ".jpeg") ? "image/jpeg" :
    "";
  if (!mimeType) throw new CLIError(`Unsupported reference format: ${ext}`);
  return { mimeType, data: buf.toString("base64") };
}

async function generate(args: Args, finalPrompt: string, outPath: string): Promise<void> {
  const apiKey = process.env.OPENROUTER_KEY;
  if (!apiKey) throw new CLIError("OPENROUTER_KEY is not set");

  const modelId = OPENROUTER_MODELS[args.model];
  const label = args.model === "nano-banana-pro" ? "Nano Banana Pro" : "Nano Banana 2";
  const refs = args.referenceImages ?? [];
  const refLabel =
    refs.length === 0 ? "" :
    refs.length === 1 ? " with reference" :
    ` with ${refs.length} references`;
  console.log(`[openrouter] ${label} ${args.size} ${args.aspectRatio}${refLabel} → ${outPath}`);

  // Text prompt first, then image parts — OpenRouter recommends this ordering
  // for reliable multi-image parsing.
  const content: Array<{ type: string; text?: string; image_url?: { url: string } }> = [
    { type: "text", text: finalPrompt },
  ];
  for (const refPath of refs) {
    const ref = await loadReference(refPath);
    content.push({
      type: "image_url",
      image_url: { url: `data:${ref.mimeType};base64,${ref.data}` },
    });
  }

  const body: Record<string, unknown> = {
    model: modelId,
    messages: [{ role: "user", content }],
    modalities: ["image", "text"],
    stream: false,
    image_config: {
      aspect_ratio: args.aspectRatio,
      image_size: OPENROUTER_SIZE_MAP[args.size],
    },
  };
  if (args.reasoning && args.reasoning !== "none") {
    body.reasoning = {
      effort: args.reasoning,
      exclude: !args.reasoningIncludeTrace,
    };
  }
  if (args.provider) {
    body.provider = { only: [args.provider] };
  }

  const resp = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const errText = await resp.text();
    throw new CLIError(`OpenRouter ${resp.status}: ${errText}`);
  }

  const data = (await resp.json()) as any;
  const message = data?.choices?.[0]?.message;
  if (!message) throw new CLIError("OpenRouter returned empty response");

  if (typeof message.content === "string" && message.content.trim()) {
    console.log(`[openrouter] model said: ${message.content}`);
  }

  const reasoningTokens =
    data?.usage?.completion_tokens_details?.reasoning_tokens as number | undefined;
  if (reasoningTokens) {
    console.log(`[openrouter] reasoning_tokens=${reasoningTokens}`);
  }
  if (args.reasoningIncludeTrace && typeof message.reasoning === "string" && message.reasoning.trim()) {
    console.log(`[openrouter] reasoning:\n${message.reasoning}`);
  }

  let b64: string | undefined;
  if (Array.isArray(message.images) && message.images.length > 0) {
    const url: string | undefined = message.images[0]?.image_url?.url;
    if (url?.startsWith("data:image/")) b64 = url.slice(url.indexOf(",") + 1);
  }
  if (!b64 && Array.isArray(message.content)) {
    for (const part of message.content) {
      const url: string | undefined = part?.image_url?.url;
      if (part?.type === "image_url" && url?.startsWith("data:image/")) {
        b64 = url.slice(url.indexOf(",") + 1);
        break;
      }
    }
  }
  if (!b64) throw new CLIError("OpenRouter response contained no image data");

  await writeFile(outPath, Buffer.from(b64, "base64"));
  console.log(`[openrouter] saved ${outPath}`);
}

async function main(): Promise<void> {
  try {
    await loadEnv();
    const args = parseArgs(process.argv);

    const prompt = args.transparent ? TRANSPARENT_PREFIX + args.prompt : args.prompt;

    if (args.variations && args.variations > 1) {
      const base = args.output.replace(/\.png$/, "");
      const tasks: Promise<void>[] = [];
      for (let i = 1; i <= args.variations; i++) {
        const out = `${base}-v${i}.png`;
        tasks.push(generate(args, prompt, out));
      }
      await Promise.all(tasks);
      return;
    }

    await generate(args, prompt, args.output);
  } catch (err) {
    if (err instanceof CLIError) {
      console.error(`error: ${err.message}`);
      process.exit(1);
    }
    console.error(err);
    process.exit(1);
  }
}

main();
