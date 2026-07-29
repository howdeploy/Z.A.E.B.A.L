// Z.A.E.B.A.L. — OpenCode adapter.
// Zaebal? Audit. Errors. Break. Analize. Leave no assumption.
//
// On every user message, runs the shared python core against the message
// text and injects the escalation protocol (if any) as a synthetic part.
// Fail-open: any error (no python3, timeout, core crash) is a silent no-op.

import { spawnSync } from "child_process"
import { homedir } from "os"
import { join } from "path"
import type { Plugin } from "@opencode-ai/plugin"

const CORE = join(homedir(), ".zaebal", "core", "zaebal.py")

export const ZaebalPlugin: Plugin = async ({ directory }) => {
  return {
    "chat.message": async (input, output) => {
      try {
        const text = (output.parts as any[])
          .filter((p) => p && p.type === "text" && typeof p.text === "string")
          .map((p) => p.text)
          .join("\n")
        if (!text.trim()) return

        const payload = JSON.stringify({
          session_id: input.sessionID ?? "unknown",
          prompt: text,
          cwd: directory ?? "",
        })
        const result = spawnSync("python3", [CORE, "--host", "opencode"], {
          input: payload,
          encoding: "utf8",
          timeout: 120000,
        })
        const injected = (result.stdout ?? "").trim()
        if (result.status === 0 && injected) {
          ;(output.parts as any[]).unshift({
            type: "text",
            text: injected,
            synthetic: true,
          })
        }
      } catch {
        // fail-open: never break the session because of zaebal
      }
    },
  }
}

export default ZaebalPlugin
